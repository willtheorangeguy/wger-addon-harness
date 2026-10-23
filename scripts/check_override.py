"""Assert the replacement really ran and read real seeded data."""
import json
import os
from pathlib import Path
from urllib.request import ProxyHandler, build_opener
from client import snapshot

with build_opener(ProxyHandler({})).open('http://example-addon:8080/', timeout=30) as response:
    actual = json.load(response)
expected = snapshot()
assert actual['implementation'] == 'api-inspector', 'Original addon was not replaced'
assert actual['platform'] == os.environ['TARGET']
for key, value in expected.items():
    assert actual[key] == value, key
Path('/reports/override.json').write_text(json.dumps(actual, indent=2))
print('Verified replacement addon against the actual authenticated application API.')
