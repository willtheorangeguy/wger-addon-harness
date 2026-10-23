"""Shared fitness-addon harness controller; Python 3.10+, no host pip dependencies."""
import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def settings():
    return json.loads((ROOT / 'harness.json').read_text(encoding='utf-8'))

def compose_command(*args, overrides=None):
    command = ['docker', 'compose', '--project-directory', str(ROOT), '--env-file',
               str(ROOT / '.env'), '-f', str(ROOT / 'compose.yaml')]
    files = overrides if overrides is not None else ([ROOT / 'compose.override.yaml']
            if (ROOT / 'compose.override.yaml').exists() else [])
    for file in files:
        command += ['-f', str(file)]
    return command + list(args)

def compose(*args, overrides=None, **kwargs):
    return subprocess.run(compose_command(*args, overrides=overrides), cwd=ROOT, check=True, **kwargs)

def image_value():
    return json.loads((ROOT / 'upstream.json').read_text())['application_image']

def docker_output(arguments, *, env=None):
    return subprocess.run(['docker', 'run', '--rm', *arguments], env=env,
                          capture_output=True, text=True, check=True).stdout.strip()

def make_jwt():
    code = ('import base64,json; from cryptography.hazmat.primitives.asymmetric import rsa; '
            'from jwt.algorithms import RSAAlgorithm; '
            'key=rsa.generate_private_key(public_exponent=65537,key_size=2048); '
            'private=json.loads(RSAAlgorithm.to_jwk(key)); private.update(alg="RS256",kid="harness"); '
            'public={k:private[k] for k in ("kty","n","e","alg","kid")}; '
            'encode=lambda d:base64.urlsafe_b64encode(json.dumps(d).encode()).decode(); '
            'print(json.dumps({"JWT_PRIVATE_KEY":encode(private),"JWT_PUBLIC_KEY":encode(public)}))')
    values = json.loads(docker_output(['--entrypoint', 'python3', image_value(), '-c', code]))
    if set(values) != {'JWT_PRIVATE_KEY', 'JWT_PUBLIC_KEY'} or not all(values.values()):
        raise RuntimeError('Application did not return a JWT keypair')
    return values

def init():
    config = settings()
    env_path = ROOT / '.env'
    if not env_path.exists():
        content = (ROOT / '.env.example').read_text(encoding='utf-8')
        markers = set(re.findall(r'GENERATE_([A-Z_]+)', content))
        replacements = {}
        if 'ADMIN_PASSWORD_HASH' in markers:
            password = re.search(r'^DEMO_PASSWORD=(.*)$', content, re.M).group(1).strip()
            value = docker_output(['-e', 'DEMO_PASSWORD', '--entrypoint', 'php', image_value(),
                                   '-r', 'echo password_hash(getenv("DEMO_PASSWORD"), PASSWORD_BCRYPT);'],
                                  env=os.environ | {'DEMO_PASSWORD': password})
            if not re.fullmatch(r'\$2[aby]\$\d\d\$[./A-Za-z0-9]{53}', value):
                raise RuntimeError('Application did not return a valid bcrypt password hash')
            replacements['ADMIN_PASSWORD_HASH'] = "'" + value + "'"
        if config.get('jwt_keypair'):
            replacements.update(make_jwt())
        for key in markers:
            value = replacements.get(key)
            if value is None:
                value = ('drv_' if key == 'DREEVE_API_KEY' else '') + secrets.token_hex(32)
            content = content.replace('GENERATE_' + key, value)
        with env_path.open('x', encoding='utf-8') as stream:
            stream.write(content)
    content = env_path.read_text(encoding='utf-8')
    if 'GENERATE_' in content:
        raise RuntimeError('.env contains unresolved credential placeholders; run init with a generated .env')
    # Upgrade an existing wger sandbox without rotating its existing DB/API credentials.
    if config.get('jwt_keypair') and not re.search(r'^JWT_PRIVATE_KEY=.+', content, re.M):
        values = make_jwt()
        with env_path.open('a', encoding='utf-8') as stream:
            stream.write('\n' + '\n'.join(k + '=' + v for k, v in values.items()) + '\n')
    env_path.chmod(0o600)
    for name in config['generated_dirs']:
        path = ROOT / name
        if path.is_symlink() or path.resolve().parent != ROOT.resolve():
            raise RuntimeError('Refusing a redirected generated directory: ' + name)
        path.mkdir(exist_ok=True)
        path.chmod(0o777)

def seed():
    compose('run', '--rm', '-T', 'seed')
    if settings()['seed_mode'] == 'files':
        compose('exec', '-T', 'app', 'bin/console', 'app:import:files')
        compose('run', '--rm', '-T', 'seed', 'python', 'seed.py', '--verify')

def audit(mode):
    compose('run', '--rm', '-T', 'test', 'python', '/harness/scripts/audit_seed.py', mode)

def ready(*, repeat_seed=False):
    config = settings()
    compose('config', '--quiet')
    compose('up', '-d', '--wait', '--wait-timeout', '600', *config['services'])
    if config['build_services']:
        compose('--profile', 'tools', '--profile', 'addon', 'build', *config['build_services'])
    seed()
    if repeat_seed:
        audit('capture')
        seed()
        audit('verify')
    compose('--profile', 'addon', 'up', '-d', '--build', '--wait', '--wait-timeout', '180', 'example-addon')

def verify_override():
    try:
        compose('--profile', 'addon', 'up', '-d', '--build', '--wait', '--wait-timeout', '180',
                'example-addon', overrides=[ROOT / 'compose.addon.example.yaml'])
        compose('run', '--rm', '-T', 'test', 'python', '/harness/scripts/check_override.py',
                overrides=[ROOT / 'compose.addon.example.yaml'])
    finally:
        # Return to the user's original override (or the built-in addon).
        compose('--profile', 'addon', 'up', '-d', '--build', '--wait', '--wait-timeout', '180', 'example-addon')

def capture_logs():
    (ROOT / 'reports').mkdir(exist_ok=True)
    with (ROOT / 'reports/compose.log').open('w', encoding='utf-8') as stream:
        try:
            return subprocess.run(compose_command('--profile', '*', 'logs', '--no-color'), cwd=ROOT,
                                  stdout=stream, stderr=subprocess.STDOUT, check=False).returncode
        except OSError as error:
            stream.write('Could not collect Compose logs: ' + str(error))
            return 1

def clear_generated():
    for name in settings()['generated_dirs']:
        target = ROOT / name
        if target.is_symlink() or target.resolve().parent != ROOT.resolve():
            raise RuntimeError('Refusing to clear redirected directory: ' + name)
        if not target.exists():
            continue
        for child in target.iterdir():
            if child.is_symlink():
                child.unlink()
            elif not child.resolve().is_relative_to(target.resolve()):
                raise RuntimeError('Refusing to clear redirected child in ' + name)
            elif child.is_dir():
                shutil.rmtree(child)
            elif child.name != '.gitkeep':
                child.unlink()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'up', 'seed', 'test', 'test-unit', 'test-override',
                                          'status', 'logs', 'config', 'down', 'reset'])
    parser.add_argument('--yes', action='store_true', help='Required to reset this sandbox data')
    args = parser.parse_args()
    if args.command == 'reset' and not args.yes:
        parser.error('reset deletes this sandbox data; pass --yes')
    if args.command == 'test-unit':
        subprocess.run([sys.executable, str(ROOT / 'scripts/reporting.py'), '--directory',
                        str(ROOT / 'tests/unit'), '--report', str(ROOT / 'reports/unit.xml')],
                       cwd=ROOT, check=True)
        return
    init()
    if args.command in ('test', 'test-override'):
        try:
            ready(repeat_seed=True)
            if args.command == 'test':
                compose('run', '--rm', '-T', 'test')
                audit('restart-capture')
                compose('restart', *settings()['restart_services'])
                compose('up', '-d', '--wait', '--wait-timeout', '600', *settings()['services'])
                audit('restart-verify')
            verify_override()
        finally:
            capture_logs()
    elif args.command == 'up':
        ready()
        print('Ready. See .env for the app/addon ports and README.md for demo login.')
    elif args.command == 'seed':
        if settings()['build_services']:
            compose('--profile', 'tools', 'build', 'seed')
        seed()
    elif args.command == 'reset':
        compose('--profile', '*', 'down', '--volumes', '--remove-orphans')
        clear_generated()
        print('Sandbox data removed; .env credentials were preserved.')
    elif args.command == 'down':
        compose('--profile', '*', 'down', '--remove-orphans')
    elif args.command == 'status':
        compose('--profile', '*', 'ps', '-a')
    elif args.command == 'logs':
        compose('--profile', '*', 'logs', '--tail', '100', '-f')
    elif args.command == 'config':
        compose('config', '--quiet')
    else:
        print('Initialized .env and generated directories.')

if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, OSError, RuntimeError, ValueError) as error:
        print('Harness failed: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
