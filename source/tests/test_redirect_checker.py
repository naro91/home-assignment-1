import unittest
import mock
import source.redirect_checker
from source import redirect_checker

import source.lib.utils


class RedirectCheckerTestCase(unittest.TestCase):
    def test_main_with_incorrect_type_of_param(self):
        uncorrect_args = 9001
        with self.assertRaises(TypeError):
            redirect_checker.main(uncorrect_args)



