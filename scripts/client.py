"""Shared API client for seed scripts, addon examples, and integration tests."""
import json
import os
from pathlib import Path
from urllib.request import Request, build_opener, HTTPCookieProcessor
from http.cookiejar import CookieJar
from urllib.error import HTTPError

class API:
    def __init__(self, credentials=None):
        self.base = os.environ['APP_URL'].rstrip('/')
        self.credentials = credentials or {}
        self.opener = build_opener(HTTPCookieProcessor(CookieJar()))

    def request(self, path, data=None, method=None, authenticated=True):
        headers = {'Content-Type': 'application/json', 'Origin': os.environ.get('PUBLIC_URL', self.base)}
        if authenticated and self.credentials.get('token'):
            headers['Authorization'] = 'Token ' + self.credentials['token']
        if authenticated and self.credentials.get('api_key'):
            headers['x-api-key'] = self.credentials['api_key']
        req = Request(self.base + path, data=None if data is None else json.dumps(data).encode(),
                      headers=headers, method=method or ('GET' if data is None else 'POST'))
        try:
            with self.opener.open(req, timeout=30) as res:
                raw = res.read()
                if not raw:
                    return None
                if 'json' in res.headers.get('Content-Type', ''):
                    return json.loads(raw)
                return raw.decode()
        except HTTPError as error:
            detail = error.read().decode()[:1500]
            raise RuntimeError(f'{req.method} {path}: HTTP {error.code}: {detail}') from error

def credentials():
    return json.loads(Path('/runtime/credentials.json').read_text())

def rows(value):
    if isinstance(value, list):
        return value
    return value.get('results', value.get('entries', []))

def snapshot():
    creds = credentials()
    api = API(creds)
    if os.environ['TARGET'] == 'wger':
        weight = rows(api.request('/api/v2/weightentry/?limit=100'))
        routines = rows(api.request('/api/v2/routine/?limit=100'))
        return {'platform': 'wger', 'weight_entries': len(weight), 'routines': len(routines),
                'latest_weight': weight[0] if weight else None}
    day = creds['end_date']
    checkin = api.request('/api/measurements/check-in/' + day)
    food = rows(api.request('/api/food-entries/by-date/' + day))
    return {'platform': 'sparkyfitness', 'date': day, 'checkin': checkin, 'food_entries': len(food)}
