import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from diagnose_comet_mice_failure import classify


class FailureTests(unittest.TestCase):
    def test_returns_only_fixed_categories(self):
        text='MICE engine stopped: missing_mice_or_jsonlite\nsynthetic-private-value-123'
        result=classify(text)
        self.assertEqual(result,['missing_mice_or_jsonlite'])
        self.assertNotIn('synthetic',str(result))

    def test_unknown_not_guessed(self):
        self.assertEqual(classify('arbitrary runtime failure'),[])
        self.assertEqual(classify('cannot create R_TempDir'),['r_temp_directory_failure'])
        self.assertEqual(classify('cannot create other thing'),[])
