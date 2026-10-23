"""Shared dependency-free API client; platform-specific authentication stays explicit."""
import json
import os
import time
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, ProxyHandler, Request, build_opener
from uuid import uuid4

class APIError(RuntimeError):
    def __init__(self, status, path):
        self.status = status
        super().__init__(f'HTTP {status} from {path}')

class API:
    def __init__(self, credentials=None):
        self.base = os.environ['APP_URL'].rstrip('/')
        self.credentials = credentials if isinstance(credentials, dict) else {}
        self.token = (credentials if isinstance(credentials, str) else None)
        if os.environ.get('TARGET') == 'dreeve' and credentials is None:
            self.token = os.environ['DREEVE_API_KEY']
        self.opener = build_opener(ProxyHandler({}), HTTPCookieProcessor(CookieJar()))

    def request(self, path, data=None, method=None, authenticated=True, content_type='application/json'):
        headers = {'Content-Type': content_type,
                   'Origin': os.environ.get('PUBLIC_URL', self.base)}
        if authenticated:
            if self.credentials.get('token'):
                headers['Authorization'] = 'Token ' + self.credentials['token']
            if self.credentials.get('api_key'):
                headers['x-api-key'] = self.credentials['api_key']
            if self.token or self.credentials.get('bearer_token'):
                headers['Authorization'] = 'Bearer ' + (self.token or self.credentials['bearer_token'])
        if isinstance(data, dict):
            data = json.dumps(data).encode()
        request = Request(self.base + path, data=data, headers=headers,
                          method=method or ('POST' if data is not None else 'GET'))
        try:
            with self.opener.open(request, timeout=30) as response:
                body = response.read()
                if not body:
                    return None
                return json.loads(body) if 'json' in response.headers.get('Content-Type', '') else body.decode()
        except HTTPError as error:
            error.close()
            # Raw upstream response bodies can contain secrets; keep errors structural.
            raise APIError(error.code, path) from None

    def upload(self, filename, payload):
        boundary = 'harness-' + uuid4().hex
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
                f'filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()
        body += payload + f'\r\n--{boundary}--\r\n'.encode()
        return self.request('/api/v1/activity/upload', body,
                            content_type='multipart/form-data; boundary=' + boundary)

    def rows(self, path, key):
        result = []
        for page in range(1, 101):
            separator = '&' if '?' in path else '?'
            value = self.request(f'{path}{separator}pagination[page]={page}&pagination[size]=100')
            result.extend(value[key])
            if page >= value['pagination']['totalPages']:
                return result
        raise RuntimeError('Pagination exceeded sandbox safety limit')

    def activities(self):
        return self.rows('/api/v1/activities', 'activities')

def credentials():
    return json.loads(Path('/runtime/credentials.json').read_text())

def rows(value):
    if isinstance(value, list):
        return value
    return value.get('results', value.get('entries', []))

def wait_for(description, predicate, timeout=370):
    print('Waiting: ' + description, flush=True)
    deadline = time.monotonic() + timeout
    heartbeat = time.monotonic()
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        if time.monotonic() - heartbeat > 30:
            print('Still waiting: ' + description, flush=True)
            heartbeat = time.monotonic()
        time.sleep(2)
    raise AssertionError('Timed out: ' + description)

def snapshot():
    platform = os.environ['TARGET']
    if platform == 'dreeve':
        activities = API().activities()
        manifest = Path('/runtime/seed-manifest.json')
        return {'platform': platform, 'activity_count': len(activities),
                'sports': sorted({a['sportType'] for a in activities}), 'activities': activities,
                'seed': json.loads(manifest.read_text()) if manifest.exists() else None}
    creds = credentials()
    api = API(creds)
    if platform == 'wger':
        weights = rows(api.request('/api/v2/weightentry/?limit=100'))
        routines = rows(api.request('/api/v2/routine/?limit=100'))
        return {'platform': platform, 'weight_entries': len(weights), 'routines': len(routines),
                'latest_weight': weights[0] if weights else None}
    day = creds['end_date']
    checkin = api.request('/api/measurements/check-in/' + day)
    food = rows(api.request('/api/food-entries/by-date/' + day))
    return {'platform': platform, 'date': day, 'checkin': checkin, 'food_entries': len(food)}
