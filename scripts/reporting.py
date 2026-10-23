"""Common JUnit writer for host and container unittest suites."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
import unittest
import xml.etree.ElementTree as ET

class ReportResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []
        self.timings = {}
    def startTest(self, test):
        self.cases.append(test.id())
        self.timings[test.id()] = time.monotonic()
        super().startTest(test)
    def stopTest(self, test):
        self.timings[test.id()] = time.monotonic() - self.timings[test.id()]
        super().stopTest(test)

def run(directory, report):
    suite = unittest.TestLoader().discover(str(directory), pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2, resultclass=ReportResult).run(suite)
    root = ET.Element('testsuite', name='addon-harness', tests=str(result.testsRun),
                      failures=str(len(result.failures)), errors=str(len(result.errors)),
                      skipped=str(len(result.skipped)), timestamp=datetime.now(timezone.utc).isoformat())
    def details(entries):
        grouped = {}
        for test, detail in entries:
            # unittest records failed subtests separately from their parent case.
            parent = getattr(test, 'test_case', test)
            grouped.setdefault(parent.id(), []).append(test.id() + '\n' + detail)
        return {key: '\n\n'.join(values) for key, values in grouped.items()}
    failures = details(result.failures)
    errors = details(result.errors)
    skipped = details(result.skipped)
    for test_id in result.cases:
        module, _, name = test_id.rpartition('.')
        case = ET.SubElement(root, 'testcase', classname=module, name=name,
                             time=f'{result.timings[test_id]:.6f}')
        for kind, mapping in [('failure', failures), ('error', errors), ('skipped', skipped)]:
            if test_id in mapping:
                ET.SubElement(case, kind).text = mapping[test_id]
    report = Path(report)
    report.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(str(report), encoding='unicode')
    return result.wasSuccessful()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    raise SystemExit(0 if run(args.directory, args.report) else 1)
