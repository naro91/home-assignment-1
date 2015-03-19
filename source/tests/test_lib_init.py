__author__ = 'Abovyan'

import unittest
import source.lib

class LibTestCase(unittest.TestCase):
    def test_to_unicode_uStr(self):
        self.assertTrue(isinstance(source.lib.to_unicode(u"Hello test !"), unicode))

    def test_to_unicode_Not_uStr(self):
        self.assertTrue(isinstance(source.lib.to_unicode("Hello test"),unicode))