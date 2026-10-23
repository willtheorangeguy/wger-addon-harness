"""Compare semantic fixture values and identities across reseeds and restarts."""
import hashlib
import json
from pathlib import Path
import sys

from contract import seed_state, target


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


mode = sys.argv[1]
prefix = 'restart' if mode.startswith('restart-') else 'seed'
state = seed_state()
path = Path('/reports') / (prefix + '-before.json')
if mode in ('capture', 'restart-capture'):
    path.write_text(json.dumps(state, indent=2))
else:
    before = json.loads(path.read_text())
    evidence = {'platform': target(), 'passed': before == state,
                'before_digest': digest(before), 'after_digest': digest(state)}
    (Path('/reports') / (prefix + '-idempotence.json')).write_text(json.dumps(evidence, indent=2))
    assert before == state, prefix + ' changed fixture identities or semantic values'
print(prefix + ' audit ' + mode + ': passed', flush=True)
