"""Identical behavioral baseline in all three addon harness repositories."""
import json
import os
from pathlib import Path
import unittest
from urllib.request import ProxyHandler, build_opener

from client import APIError, credentials, snapshot
from contract import api, health_path, invalid_api, login, private_path, seed_date, seed_state, target


class ContractTests(unittest.TestCase):
    def test_01_application_health_interface(self):
        self.assertTrue(api().request(health_path()))

    def test_02_frontend_serves_html(self):
        url = os.environ['FRONTEND_URL'] + ('/admin/login' if target() == 'dreeve' else '/')
        with build_opener(ProxyHandler({})).open(url, timeout=30) as response:
            self.assertEqual(response.status, 200)
            self.assertIn('text/html', response.headers['Content-Type'])
            self.assertIn('<html', response.read().decode().lower())

    def test_03_valid_demo_login_reads_private_data(self):
        self.assertTrue(login(True))

    def test_04_invalid_demo_login_is_rejected(self):
        try:
            result = login(False)
        except APIError as error:
            self.assertIn(error.status, (400, 401, 403))
        else:
            self.assertFalse(result)

    def test_05_missing_authentication_is_rejected(self):
        with self.assertRaises(APIError) as caught:
            api().request(private_path(), authenticated=False)
        self.assertIn(caught.exception.status, (401, 403))

    def test_06_invalid_credential_is_rejected(self):
        with self.assertRaises(APIError) as caught:
            invalid_api().request(private_path())
        self.assertIn(caught.exception.status, (401, 403))

    def test_07_valid_credential_reads_seed_data(self):
        self.assertTrue(api().request(private_path()))

    def test_08_repeat_seed_preserves_ids_dates_and_values(self):
        report = json.loads(Path('/reports/seed-idempotence.json').read_text())
        self.assertTrue(report['passed'])
        self.assertEqual(report['before_digest'], report['after_digest'])

    def test_09_seed_dates_are_frozen(self):
        self.assertEqual(seed_state()['end_date'], seed_date())
        self.assertRegex(seed_date(), r'^\d{4}-\d{2}-\d{2}$')

    def test_10_seed_record_ids_are_unique(self):
        state = seed_state()
        for key, values in state.items():
            if not isinstance(values, list):
                continue
            with self.subTest(collection=key):
                self.assertTrue(values)
                ids = [row['id'] for row in values]
                self.assertTrue(all(ids))
                self.assertEqual(len(ids), len(set(ids)))

    def test_11_example_addon_uses_real_authenticated_data(self):
        if os.environ.get('CHECK_EXAMPLE_ADDON', 'true').lower() != 'true':
            self.skipTest('Custom addon interface configured')
        with build_opener(ProxyHandler({})).open('http://example-addon:8080/', timeout=30) as response:
            value = json.load(response)
        self.assertEqual(value['platform'], target())
        for key, expected in snapshot().items():
            self.assertEqual(value[key], expected, key)

    def test_12_addon_does_not_return_credentials(self):
        if os.environ.get('CHECK_EXAMPLE_ADDON', 'true').lower() != 'true':
            self.skipTest('Custom addon interface configured')
        with build_opener(ProxyHandler({})).open('http://example-addon:8080/', timeout=30) as response:
            body = response.read().decode()
        secrets = list(credentials().get(key) for key in ('token', 'api_key', 'password'))
        secrets.append(os.environ.get('DREEVE_API_KEY'))
        for value in secrets:
            if value:
                self.assertNotIn(value, body)

    def test_13_unknown_api_resource_returns_404(self):
        path = {'wger': '/api/v2/weightentry/999999999/',
                'sparkyfitness': '/api/harness-resource-does-not-exist',
                'dreeve': '/api/v1/activities/activity-00000000-0000-4000-8000-000000000000'}[target()]
        with self.assertRaises(APIError) as caught:
            api().request(path)
        self.assertEqual(caught.exception.status, 404)
