import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import harness


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.root_patch = patch.object(harness, 'ROOT', self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        self.addCleanup(self.temporary.cleanup)
        self.config = {'platform': 'test', 'generated_dirs': ['runtime', 'reports', 'watch'],
                       'services': ['app'], 'restart_services': ['app'], 'build_services': [],
                       'seed_mode': 'api'}
        self.save_config()
        (self.root / '.env.example').write_text('SECRET_KEY=GENERATE_SECRET_KEY\nDREEVE_API_KEY=GENERATE_DREEVE_API_KEY\n')
        (self.root / 'upstream.json').write_text(json.dumps({'application_image': 'example/image@sha256:test'}))

    def save_config(self):
        (self.root / 'harness.json').write_text(json.dumps(self.config))

    def run_main(self, command, *arguments):
        with patch('sys.argv', ['harness.py', command, *arguments]):
            return harness.main()

    def test_compose_uses_absolute_workspace_and_env_paths(self):
        command = harness.compose_command('config', '--quiet')
        self.assertIn(str(self.root / 'compose.yaml'), command)
        self.assertIn(str(self.root / '.env'), command)
        self.assertIn(str(self.root), command)
        self.assertEqual(command[-2:], ['config', '--quiet'])

    def test_user_override_is_automatically_loaded(self):
        override = self.root / 'compose.override.yaml'
        override.touch()
        self.assertIn(str(override), harness.compose_command('config'))

    def test_explicit_override_preserves_user_file(self):
        original = self.root / 'compose.override.yaml'
        original.write_text('user data')
        replacement = self.root / 'compose.addon.example.yaml'
        command = harness.compose_command('config', overrides=[replacement])
        self.assertIn(str(replacement), command)
        self.assertNotIn(str(original), command)
        self.assertEqual(original.read_text(), 'user data')

    def test_explicit_empty_overrides_disables_auto_override(self):
        override = self.root / 'compose.override.yaml'
        override.touch()
        self.assertNotIn(str(override), harness.compose_command('config', overrides=[]))

    def test_compose_runs_from_workspace_without_changing_parent_cwd(self):
        before = Path.cwd()
        with patch.object(subprocess, 'run') as run:
            harness.compose('config')
            self.assertEqual(run.call_args.kwargs['cwd'], self.root)
            self.assertTrue(run.call_args.kwargs['check'])
        self.assertEqual(Path.cwd(), before)

    def test_init_generates_non_placeholder_credentials(self):
        harness.init()
        content = (self.root / '.env').read_text()
        self.assertNotIn('GENERATE_', content)
        self.assertRegex(content, r'SECRET_KEY=[0-9a-f]{64}')
        self.assertRegex(content, r'DREEVE_API_KEY=drv_[0-9a-f]{64}')
        self.assertTrue(all((self.root / name).is_dir() for name in self.config['generated_dirs']))

    def test_init_preserves_existing_env(self):
        path = self.root / '.env'
        path.write_text('CUSTOM_CREDENTIAL=preserve-me\n')
        harness.init()
        self.assertEqual(path.read_text(), 'CUSTOM_CREDENTIAL=preserve-me\n')

    def test_init_rejects_unresolved_existing_placeholders(self):
        (self.root / '.env').write_text('SECRET_KEY=GENERATE_SECRET_KEY')
        with self.assertRaisesRegex(RuntimeError, 'placeholder'):
            harness.init()

    def test_repeated_init_does_not_rotate_credentials(self):
        harness.init()
        original = (self.root / '.env').read_bytes()
        harness.init()
        self.assertEqual(original, (self.root / '.env').read_bytes())

    def test_hash_is_quoted_and_password_is_not_in_arguments(self):
        (self.root / '.env.example').write_text('DEMO_PASSWORD=synthetic-password\nADMIN_PASSWORD_HASH=GENERATE_ADMIN_PASSWORD_HASH\n')
        value = '$2y$12$' + 'a' * 53
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, value)) as run:
            harness.init()
        self.assertIn("ADMIN_PASSWORD_HASH='" + value + "'", (self.root / '.env').read_text())
        self.assertNotIn('synthetic-password', repr(run.call_args.args))

    def test_invalid_hash_does_not_create_partial_env(self):
        (self.root / '.env.example').write_text('DEMO_PASSWORD=synthetic\nADMIN_PASSWORD_HASH=GENERATE_ADMIN_PASSWORD_HASH')
        with patch.object(harness, 'docker_output', return_value='not-a-hash'):
            with self.assertRaisesRegex(RuntimeError, 'bcrypt'):
                harness.init()
        self.assertFalse((self.root / '.env').exists())

    def test_jwt_upgrade_preserves_existing_credentials_and_runs_once(self):
        self.config['jwt_keypair'] = True
        self.save_config()
        (self.root / '.env').write_text('SECRET_KEY=preserve-existing\n')
        with patch.object(harness, 'make_jwt', return_value={
                'JWT_PRIVATE_KEY': 'synthetic-private', 'JWT_PUBLIC_KEY': 'synthetic-public'}) as make:
            harness.init()
            harness.init()
        content = (self.root / '.env').read_text()
        self.assertIn('SECRET_KEY=preserve-existing', content)
        self.assertEqual(content.count('JWT_PRIVATE_KEY='), 1)
        self.assertEqual(make.call_count, 1)

    def test_malformed_jwt_output_is_rejected_before_env_creation(self):
        self.config['jwt_keypair'] = True
        self.save_config()
        with patch.object(harness, 'docker_output', return_value='{}'):
            with self.assertRaisesRegex(RuntimeError, 'keypair'):
                harness.init()
        self.assertFalse((self.root / '.env').exists())

    def test_test_unit_does_not_require_docker_or_credentials(self):
        with patch.object(harness, 'init') as init, patch.object(subprocess, 'run') as run:
            self.run_main('test-unit')
            init.assert_not_called()
            self.assertIn(str(self.root / 'scripts/reporting.py'), run.call_args.args[0])

    def test_config_is_quiet(self):
        with patch.object(harness, 'init'), patch.object(harness, 'compose') as compose:
            self.run_main('config')
            compose.assert_called_once_with('config', '--quiet')

    def test_reset_requires_confirmation_before_init(self):
        with patch.object(harness, 'init') as init, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                self.run_main('reset')
        self.assertEqual(caught.exception.code, 2)
        init.assert_not_called()

    def test_down_preserves_volumes(self):
        with patch.object(harness, 'init'), patch.object(harness, 'compose') as compose:
            self.run_main('down')
            self.assertNotIn('--volumes', compose.call_args.args)

    def test_reset_removes_project_volumes_only_with_flag(self):
        with patch.object(harness, 'init'), patch.object(harness, 'compose') as compose, patch.object(harness, 'clear_generated') as clear:
            self.run_main('reset', '--yes')
            self.assertIn('--volumes', compose.call_args.args)
            clear.assert_called_once()

    def test_clear_generated_preserves_other_project_files(self):
        for name in self.config['generated_dirs']:
            path = self.root / name
            path.mkdir()
            (path / 'nested').mkdir()
            (path / 'nested/data').write_text('synthetic')
        (self.root / '.env').write_text('keep credential')
        (self.root / 'keep.txt').write_text('keep')
        harness.clear_generated()
        self.assertEqual((self.root / '.env').read_text(), 'keep credential')
        self.assertEqual((self.root / 'keep.txt').read_text(), 'keep')
        self.assertTrue(all(not list((self.root / name).iterdir()) for name in self.config['generated_dirs']))

    def test_clear_generated_rejects_parent_escape(self):
        self.config['generated_dirs'] = ['../outside']
        self.save_config()
        with self.assertRaises(RuntimeError):
            harness.clear_generated()

    def test_clear_generated_rejects_redirected_directory(self):
        with tempfile.TemporaryDirectory() as other:
            try:
                os.symlink(other, self.root / 'runtime', target_is_directory=True)
            except OSError:
                self.skipTest('Host does not permit directory symlinks')
            with self.assertRaises(RuntimeError):
                harness.clear_generated()

    def test_startup_failure_still_collects_logs(self):
        with patch.object(harness, 'init'), patch.object(harness, 'ready', side_effect=RuntimeError('startup failed')), patch.object(harness, 'capture_logs') as capture:
            with self.assertRaisesRegex(RuntimeError, 'startup failed'):
                self.run_main('test')
            capture.assert_called_once()

    def test_override_check_restores_original_after_failure(self):
        calls = []
        def compose(*args, **kwargs):
            calls.append((args, kwargs))
            if args[:4] == ('run', '--rm', '-T', 'test'):
                raise RuntimeError('replacement failed')
        with patch.object(harness, 'compose', side_effect=compose):
            with self.assertRaisesRegex(RuntimeError, 'replacement failed'):
                harness.verify_override()
        self.assertEqual(calls[-1][1], {})
        self.assertIn('example-addon', calls[-1][0])

    def test_missing_docker_during_log_capture_does_not_mask_failure(self):
        with patch.object(subprocess, 'run', side_effect=FileNotFoundError('docker missing')):
            self.assertEqual(harness.capture_logs(), 1)
        self.assertIn('docker missing', (self.root / 'reports/compose.log').read_text())


if __name__ == '__main__':
    unittest.main()
