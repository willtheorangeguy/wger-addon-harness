from pathlib import Path
import json
from client import snapshot
from reporting import run

success = run('/harness/tests', '/reports/junit.xml')
try:
    Path('/reports/api-snapshot.json').write_text(json.dumps(snapshot(), indent=2))
except (RuntimeError, OSError):
    success = False
raise SystemExit(0 if success else 1)
