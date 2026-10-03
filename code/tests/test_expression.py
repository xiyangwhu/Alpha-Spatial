import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from export_expression import project


class ExpressionTests(unittest.TestCase):
    def test_target_restriction_and_zero(self):
        row = dict(status='valid', finish_reason='stop', raw_text='{"ERBB2":3,"EXTRA":2}',
                   predicted_expression={'ERBB2':3, 'EXTRA':2})
        values, extras = project(row, ['ERBB2', 'CD3E'])
        self.assertEqual(values, [3, 0])
        self.assertEqual(extras, {'EXTRA':2})

    def test_failures_are_not_zero(self):
        for status in ['truncated', 'invalid']:
            self.assertEqual(project(dict(status=status, predicted_expression=None), ['ERBB2']), ([None], {}))

    def test_inconsistent_valid_flag_rejected(self):
        row = dict(status='valid', finish_reason='stop', raw_text='{"ERBB2":-3}',
                   predicted_expression={'ERBB2':-3})
        with self.assertRaises(ValueError):
            project(row, ['ERBB2'])


if __name__ == '__main__':
    unittest.main()
