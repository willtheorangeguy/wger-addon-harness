from collections import Counter
import unittest
from client import APIError, rows
from contract import api


class WgerExtendedTests(unittest.TestCase):
    def test_weight_history_values_progress_over_fourteen_dates(self):
        weights = sorted(rows(api().request('/api/v2/weightentry/?limit=100')), key=lambda x: x['date'])
        self.assertEqual(len(weights), 14)
        self.assertEqual(len({x['date'][:10] for x in weights}), 14)
        for index, item in enumerate(weights):
            self.assertAlmostEqual(float(item['weight']), round(82 - index * .07, 2), places=2)

    def test_weight_pagination_has_no_missing_or_repeated_ids(self):
        client = api()
        expected = {x['id'] for x in rows(client.request('/api/v2/weightentry/?limit=100'))}
        found = []
        for offset in range(0, 14, 2):
            page = client.request(f'/api/v2/weightentry/?limit=2&offset={offset}')
            self.assertEqual(len(page['results']), 2)
            found.extend(x['id'] for x in page['results'])
        self.assertEqual(set(found), expected)
        self.assertEqual(len(found), len(set(found)))

    def test_nutrition_has_three_meals_on_each_seed_day(self):
        values = rows(api().request('/api/v2/nutritiondiary/?limit=100'))
        counts = Counter(x['datetime'][:10] for x in values)
        self.assertEqual(len(counts), 14)
        self.assertEqual(set(counts.values()), {3})
        self.assertTrue(all(float(x['amount']) == 300 for x in values))

    def test_weight_create_read_update_delete(self):
        client = api()
        result = client.request('/api/v2/weightentry/', {'date': '2002-01-01', 'weight': '79.5'})
        path = '/api/v2/weightentry/' + str(result['id']) + '/'
        try:
            self.assertAlmostEqual(float(client.request(path)['weight']), 79.5)
            client.request(path, {'weight': '80.25'}, method='PATCH')
            self.assertAlmostEqual(float(client.request(path)['weight']), 80.25)
        finally:
            client.request(path, method='DELETE')
        with self.assertRaises(APIError) as caught:
            client.request(path)
        self.assertEqual(caught.exception.status, 404)

    def test_invalid_measurement_is_rejected_without_changing_count(self):
        client = api()
        before = client.request('/api/v2/weightentry/?limit=1')['count']
        with self.assertRaises(APIError) as caught:
            client.request('/api/v2/weightentry/', {'date': 'invalid', 'weight': 'invalid'})
        self.assertEqual(caught.exception.status, 400)
        self.assertEqual(client.request('/api/v2/weightentry/?limit=1')['count'], before)
