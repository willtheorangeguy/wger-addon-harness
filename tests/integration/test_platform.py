"""Integration checks against actual seeded services; unittest, no dependencies."""
import json
import os
from pathlib import Path
import time
import unittest
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from urllib.request import urlopen
from client import API, credentials, rows, snapshot

class HarnessTests(unittest.TestCase):
    def test_seed_is_visible_via_api(self):
        value = snapshot()
        api = API(credentials())
        if os.environ['TARGET'] == 'wger':
            self.assertGreaterEqual(value['weight_entries'], 14)
            self.assertGreaterEqual(value['routines'], 1)
            self.assertEqual(len(rows(api.request('/api/v2/workoutlog/?limit=100'))), 54)
            self.assertEqual(len(rows(api.request('/api/v2/nutritiondiary/?limit=100'))), 42)
        else:
            self.assertAlmostEqual(float(value['checkin']['weight']), 81.09, places=2)
            self.assertGreaterEqual(value['food_entries'], 3)
            creds = credentials()
            checkins = rows(api.request('/api/measurements/check-in-measurements-range/' + creds['start_date'] + '/' + creds['end_date']))
            self.assertEqual(len(checkins), 14)
            walks = rows(api.request('/api/exercise-entries/by-date?selectedDate=' + creds['end_date']))
            self.assertEqual(sum(entry['name'] == 'Harness Brisk Walk' for entry in walks), 1)

    def test_strength_workout_history(self):
        api = API(credentials())
        if os.environ['TARGET'] == 'wger':
            entries = rows(api.request('/api/v2/workoutlog/?limit=100'))
            self.assertEqual(len({entry['date'][:10] for entry in entries}), 6)
            self.assertEqual(len(entries), 54)
            self.assertTrue(all(float(entry['repetitions']) == 10 for entry in entries))
            weights = {}
            for entry in entries:
                weights.setdefault(str(entry['exercise']), []).append((entry['date'], float(entry['weight'])))
        else:
            end = date.fromisoformat(credentials()['end_date'])
            weights = {}
            total_sets = 0
            for offset in [12, 10, 8, 5, 3, 0]:
                day = str(end-timedelta(days=offset))
                entries = rows(api.request('/api/exercise-entries/by-date?selectedDate=' + day))
                strength = [entry for entry in entries if entry['name'] in {
                    'Harness Barbell Squat', 'Harness Bench Press', 'Harness Bent-over Row'}]
                self.assertEqual(len(strength), 3)
                for entry in strength:
                    self.assertEqual(len(entry['sets']), 3)
                    for logged_set in entry['sets']:
                        self.assertEqual(logged_set['reps'], 10)
                        self.assertIsNotNone(logged_set['completed_at'])
                        weights.setdefault(entry['name'], []).append((day, float(logged_set['weight'])))
                    total_sets += len(entry['sets'])
            self.assertEqual(total_sets, 54)
        self.assertEqual(len(weights), 3)
        for history in weights.values():
            history.sort()
            self.assertGreater(history[0][1], 0)
            self.assertAlmostEqual(history[-1][1] - history[0][1], 12.5)

    def test_example_addon_reads_real_data(self):
        if os.environ.get('CHECK_EXAMPLE_ADDON', 'true').lower() != 'true':
            self.skipTest('Custom addon interface configured')
        with urlopen('http://example-addon:8080/', timeout=30) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(json.load(response)['platform'], os.environ['TARGET'])

    def test_private_data_requires_authentication(self):
        api = API()
        path = '/api/v2/weightentry/' if os.environ['TARGET'] == 'wger' else '/api/measurements/check-in/' + credentials()['end_date']
        with self.assertRaisesRegex(RuntimeError, r'HTTP (401|403)'):
            api.request(path)

    def test_authenticated_write_read_delete(self):
        api = API(credentials())
        if os.environ['TARGET'] == 'wger':
            # A separate date keeps the round-trip independent of the demo history.
            path = '/api/v2/weightentry/'
            created = api.request(path, {'date': '2001-01-01', 'weight': '79.5'})
            detail = path + str(created['id']) + '/'
            try:
                self.assertEqual(float(api.request(detail)['weight']), 79.5)
            finally:
                api.request(detail, method='DELETE')
        else:
            path = '/api/measurements/check-in'
            created = api.request(path, {'entry_date': '2001-01-01', 'weight': 79.5, 'steps': 1234})
            try:
                self.assertEqual(float(api.request(path + '/2001-01-01')['weight']), 79.5)
            finally:
                api.request(path + '/' + str(created['id']), method='DELETE')
