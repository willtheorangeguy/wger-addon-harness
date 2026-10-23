"""Platform adapters for the common behavioral contract; no upstream app is mocked."""
import html
import json
import os
import re
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request

from client import API, credentials, rows


def target():
    return os.environ['TARGET']


def api():
    return API() if target() == 'dreeve' else API(credentials())


def private_path():
    if target() == 'dreeve':
        return '/api/v1/activities'
    if target() == 'wger':
        return '/api/v2/weightentry/'
    return '/api/measurements/check-in/' + credentials()['end_date']


def health_path():
    return {'dreeve': '/api/v1/status', 'wger': '/api/v2/version/',
            'sparkyfitness': '/api/health'}[target()]


def invalid_api():
    if target() == 'dreeve':
        return API('invalid-harness-token')
    return API({'token' if target() == 'wger' else 'api_key': 'invalid-harness-token'})


def login(valid):
    client = API({})
    if target() == 'dreeve':
        url = client.base + '/admin/login'
        with client.opener.open(url, timeout=30) as response:
            page = response.read().decode()
        csrf = html.unescape(re.search(r'name="_csrf_token" value="([^"]+)"', page).group(1))
        password = os.environ['DEMO_PASSWORD'] if valid else 'invalid-harness-password'
        body = urlencode({'_username': os.environ['DEMO_USERNAME'], '_password': password,
                          '_csrf_token': csrf}).encode()
        with client.opener.open(Request(url, data=body, headers={
                'Origin': client.base, 'Referer': url}), timeout=30) as response:
            return '/admin/login' not in response.url
    creds = credentials()
    if target() == 'wger':
        response = client.request('/allauth/app/v1/auth/login', {
            'username': creds['username'], 'password': creds['password'] if valid else 'invalid-harness-password'},
            authenticated=False)
        access = response['meta']['access_token']
        client.credentials = {'bearer_token': access}
        assert rows(client.request(private_path())), 'Login JWT cannot read the private API'
        return True
    client.request('/api/auth/sign-in/email', {
        'email': creds['email'], 'password': creds['password'] if valid else 'invalid-harness-password'},
        authenticated=False)
    assert client.request(private_path(), authenticated=False), 'Session cookie cannot read the private API'
    return True


def seed_date():
    filename = '/runtime/seed-manifest.json' if target() == 'dreeve' else '/runtime/credentials.json'
    return json.loads(Path(filename).read_text())['end_date']


def project(records, fields):
    return sorted([{field: item.get(field) for field in fields} for item in records],
                  key=lambda item: json.dumps(item, sort_keys=True))


def seed_state():
    client = api()
    end = seed_date()
    if target() == 'dreeve':
        names = {f['name'] for f in json.loads(Path('/runtime/seed-manifest.json').read_text())['fixtures']}
        activities = [a for a in client.activities() if a['name'] in names]
        return {'end_date': end, 'activities': project(activities, [
            'id', 'name', 'startDateLocal', 'sportType', 'distanceInMeter', 'elapsedTimeInSeconds',
            'movingTimeInSeconds', 'calories', 'description'])}
    if target() == 'wger':
        return {'end_date': end,
            'weights': project(rows(client.request('/api/v2/weightentry/?limit=100')), ['id', 'date', 'weight']),
            'routines': project(rows(client.request('/api/v2/routine/?limit=100')), ['id', 'name', 'start', 'end']),
            'sets': project(rows(client.request('/api/v2/workoutlog/?limit=100')),
                            ['id', 'date', 'exercise', 'weight', 'repetitions', 'routine', 'slot_entry']),
            'meals': project(rows(client.request('/api/v2/nutritiondiary/?limit=100')),
                             ['id', 'datetime', 'amount', 'ingredient', 'meal', 'plan'])}
    start = credentials()['start_date']
    checks = rows(client.request('/api/measurements/check-in-measurements-range/' + start + '/' + end))
    meals, workouts = [], []
    for offset in range(14):
        day = str(date.fromisoformat(end) - timedelta(days=offset))
        meals.extend(rows(client.request('/api/food-entries/by-date/' + day)))
        workouts.extend(rows(client.request('/api/exercise-entries/by-date?selectedDate=' + day)))
    return {'end_date': end,
        'checkins': project(checks, ['id', 'entry_date', 'weight', 'waist', 'steps', 'height']),
        'meals': project(meals, ['id', 'entry_date', 'meal_type', 'food_id', 'quantity', 'calories',
                                'protein', 'carbs', 'fat']),
        'workouts': project(workouts, ['id', 'entry_date', 'exercise_id', 'name', 'sets',
                                      'duration_minutes', 'calories_burned'])}
