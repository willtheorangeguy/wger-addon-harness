import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import reporting


class ReportingTests(unittest.TestCase):
    def test_report_preserves_success_failure_error_and_skip(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = '''import unittest
class SyntheticCases(unittest.TestCase):
    def test_success(self): pass
    def test_failure(self): self.fail("failure <detail>")
    def test_error(self): raise RuntimeError("error detail")
    @unittest.skip("synthetic skip")
    def test_skip(self): pass
'''
            (root / 'test_synthetic_reporting.py').write_text(source)
            output = root / 'nested/junit.xml'
            with contextlib.redirect_stderr(io.StringIO()):
                success = reporting.run(root, output)
            self.assertFalse(success)
            suite = ET.parse(output).getroot()
            self.assertEqual(suite.attrib['tests'], '4')
            self.assertEqual(suite.attrib['failures'], '1')
            self.assertEqual(suite.attrib['errors'], '1')
            self.assertEqual(suite.attrib['skipped'], '1')
            self.assertEqual(len(suite.findall('testcase')), 4)
            self.assertTrue(all(float(case.attrib['time']) >= 0 for case in suite))
            self.assertIn('failure <detail>', suite.find('.//failure').text)

    def test_empty_suite_writes_valid_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertTrue(reporting.run(root, root / 'junit.xml'))
            self.assertEqual(ET.parse(root / 'junit.xml').getroot().attrib['tests'], '0')

    def test_subtest_failures_and_errors_keep_diagnostics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'test_subtest_reporting.py').write_text('''import unittest
class Subtests(unittest.TestCase):
    def test_rows(self):
        with self.subTest(row="bad-value"): self.fail("wrong value")
        with self.subTest(row="bad-type"): raise ValueError("wrong type")
''')
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertFalse(reporting.run(root, root / 'junit.xml'))
            case = ET.parse(root / 'junit.xml').getroot().find('testcase')
            self.assertIn('bad-value', case.find('failure').text)
            self.assertIn('wrong value', case.find('failure').text)
            self.assertIn('bad-type', case.find('error').text)
            self.assertIn('wrong type', case.find('error').text)
