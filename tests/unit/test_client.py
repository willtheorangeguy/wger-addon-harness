import json
import os
from pathlib import Path
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
from client import API, APIError


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def do_GET(self):
        self.handle_request()
    def do_POST(self):
        self.handle_request()
    def do_PATCH(self):
        self.handle_request()
    def do_DELETE(self):
        self.handle_request()
    def handle_request(self):
        path = urlsplit(self.path)
        data = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if path.path == '/error':
            self.send_response(401)
            body = b'upstream-secret-DO-NOT-LOG'
        elif path.path == '/empty':
            self.send_response(204)
            body = b''
        elif path.path == '/paged':
            page = int(parse_qs(path.query)['pagination[page]'][0])
            self.send_response(200)
            body = json.dumps({'entries': [page], 'pagination': {'totalPages': 2}}).encode()
        else:
            self.send_response(200)
            if path.path == '/session':
                self.send_header('Set-Cookie', 'harness_session=valid; Path=/')
            body = json.dumps({'authorization': self.headers.get('Authorization'),
                'api_key': self.headers.get('x-api-key'), 'cookie': self.headers.get('Cookie'),
                'method': self.command, 'body': data.decode(),
                'content_type': self.headers.get('Content-Type')}).encode()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
    def setUp(self):
        base = f'http://127.0.0.1:{self.server.server_port}'
        self.environment = patch.dict(os.environ, {'APP_URL': base, 'PUBLIC_URL': base,
            'TARGET': 'test', 'DREEVE_API_KEY': 'synthetic-bearer'})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_legacy_token_authentication(self):
        self.assertEqual(API({'token': 'synthetic'}).request('/echo')['authorization'], 'Token synthetic')
    def test_api_key_authentication(self):
        self.assertEqual(API({'api_key': 'synthetic'}).request('/echo')['api_key'], 'synthetic')
    def test_bearer_authentication(self):
        self.assertEqual(API('synthetic').request('/echo')['authorization'], 'Bearer synthetic')
    def test_login_jwt_authentication(self):
        self.assertEqual(API({'bearer_token': 'jwt'}).request('/echo')['authorization'], 'Bearer jwt')
    def test_disabled_authentication_sends_no_key(self):
        result = API({'api_key': 'synthetic', 'token': 'synthetic'}).request('/echo', authenticated=False)
        self.assertIsNone(result['authorization'])
        self.assertIsNone(result['api_key'])
    def test_json_request_and_response(self):
        response = API().request('/echo', {'name': 'Synthetic café'})
        self.assertEqual(json.loads(response['body']), {'name': 'Synthetic café'})
        self.assertEqual(response['method'], 'POST')
    def test_patch_and_delete_methods(self):
        for method in ('PATCH', 'DELETE'):
            self.assertEqual(API().request('/echo', method=method)['method'], method)
    def test_cookie_session_is_preserved(self):
        client = API()
        client.request('/session')
        self.assertIn('harness_session=valid', client.request('/echo')['cookie'])
    def test_error_status_preserved_without_body_leak(self):
        with self.assertRaises(APIError) as caught:
            API().request('/error')
        self.assertEqual(caught.exception.status, 401)
        self.assertNotIn('DO-NOT-LOG', str(caught.exception))
    def test_empty_success_response(self):
        self.assertIsNone(API().request('/empty', method='DELETE'))
    def test_pagination_joins_all_pages(self):
        self.assertEqual(API().rows('/paged', 'entries'), [1, 2])
    def test_multipart_upload_is_well_formed(self):
        client = API()
        with patch.object(client, 'base', client.base):
            response = client.upload('synthetic.fit', b'FIT-payload')
        self.assertIn('name="file"', response['body'])
        self.assertIn('filename="synthetic.fit"', response['body'])
        self.assertIn('FIT-payload', response['body'])
        self.assertIn('multipart/form-data; boundary=harness-', response['content_type'])
    def test_internal_requests_ignore_host_proxy(self):
        with patch.dict(os.environ, {'HTTP_PROXY': 'http://127.0.0.1:1', 'NO_PROXY': ''}):
            self.assertEqual(API().request('/echo')['method'], 'GET')
    def test_dreeve_uses_environment_key(self):
        with patch.dict(os.environ, {'TARGET': 'dreeve'}):
            self.assertEqual(API().request('/echo')['authorization'], 'Bearer synthetic-bearer')
    def test_explicit_credentials_do_not_mutate_input(self):
        value = {'api_key': 'synthetic'}
        API(value).request('/echo')
        self.assertEqual(value, {'api_key': 'synthetic'})


if __name__ == '__main__':
    unittest.main()
