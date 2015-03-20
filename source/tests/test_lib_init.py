import mock

__author__ = 'Abovyan'

import unittest
import source.lib

class LibTestCase(unittest.TestCase):
    def test_to_unicode_uStr(self):
        self.assertTrue(isinstance(source.lib.to_unicode(u"Hello test !"), unicode))

    def test_to_unicode_not_uStr(self):
        self.assertTrue(isinstance(source.lib.to_unicode("Hello test"),unicode))

    def test_to_str_not_unicode(self):
        self.assertFalse(isinstance(source.lib.to_str("Hello test"), unicode))

    def test_to_str_unicode(self):
        self.assertFalse(isinstance(source.lib.to_str(u"Hello test"), unicode))

    def test_counters(self):
        content = "src='www.google-analytics.com/ga.js.index'"
        self.assertEqual(len(source.lib.get_counters(content)), 1)
        self.assertEqual(source.lib.get_counters(content)[0], 'GOOGLE_ANALYTICS')

    def test_counters_absent(self):
        self.assertEqual(len(source.lib.get_counters("src='www.tech-mail.ru/ga.js.min'")), 0)

    def test_check_for_meta(self):
        content = '<meta http-equiv="refresh" content="3;url=http://www.youtube.com/"><head>'
        self.assertEqual(source.lib.check_for_meta(content, ''), 'http://www.youtube.com/')

    def test_meta_incorrect_redirect(self):
        self.assertIsNone(source.lib.check_for_meta('<meta http-equiv="refresh"><head>', ''))

    def test_check_for_meta_incorrectUrl(self):
        content = '<meta http-equiv="refresh" content="3;http://www.youtube.com/"><head>'
        self.assertIsNone(source.lib.check_for_meta(content, ''))

    def test_market(self):
        url = 'market://search?q=pname:net.mandaria.tippytipper'
        self.assertEqual(source.lib.fix_market_url(url),
                         'http://play.google.com/store/apps/search?q=pname:net.mandaria.tippytipper')

    def test_make_pycurl_request(self):
        content = "Test content"
        redirectUrl = "tech-mail.ru"

        mockCurl = mock.Mock()
        mockCurl.getinfo.return_value = redirectUrl

        mockIO = mock.Mock()
        mockIO.getvalue.return_value = content

        with mock.patch("pycurl.Curl", mock.Mock(return_value=mockCurl)):
            with mock.patch("StringIO.StringIO", mock.Mock(return_value=mockIO)):
                self.assertEqual(source.lib.make_pycurl_request('tech-mail.ru', 1)[1], redirectUrl)

    def test_make_pycurl_request_useragent(self):
        userAgent = "Mozila"

        mockCurl = mock.Mock()
        mockSetopt = mock.Mock()
        mockCurl.setopt = mockSetopt

        with mock.patch("pycurl.Curl", mock.Mock(return_value=mockCurl)):
            source.lib.make_pycurl_request('tech-mail.ru', 1, userAgent)
            mockSetopt.assert_any_call(source.lib.pycurl.USERAGENT, userAgent)
