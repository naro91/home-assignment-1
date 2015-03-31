import mock

__author__ = 'Abovyan'

import unittest
import source.lib

class LibTestCase(unittest.TestCase):
    def test_to_unicode_uStr(self):
        self.assertTrue(isinstance(source.lib.to_unicode(u"Hello test !"), unicode))
        self.assertEquals(source.lib.to_unicode(u"Hello test !"),"Hello test !")

    def test_to_unicode_not_uStr(self):
        self.assertTrue(isinstance(source.lib.to_unicode("Hello test"),unicode))

    def test_to_str_not_unicode(self):
        self.assertFalse(isinstance(source.lib.to_str("Hello test"), unicode))

    def test_to_str_unicode(self):
        self.assertFalse(isinstance(source.lib.to_str(u"Hello test"), unicode))

    def test_get_counters(self):
        content = "src='www.google-analytics.com/ga.js.index'"
        self.assertEqual(len(source.lib.get_counters(content)), 1)
        self.assertEqual(source.lib.get_counters(content)[0], 'GOOGLE_ANALYTICS')

    def test_get_counters_absent(self):
        self.assertEqual(len(source.lib.get_counters("src='www.tech-mail.ru/ga.js.min'")), 0)

    def test_check_for_meta(self):
        content = '<meta http-equiv="refresh" content="3;url=http://www.youtube.com/"><head>'
        self.assertEqual(source.lib.check_for_meta(content, ''), 'http://www.youtube.com/')

    def test_meta_incorrect_redirect(self):
        self.assertIsNone(source.lib.check_for_meta('<meta http-equiv="refresh"><head>', ''))

    def test_check_for_meta_incorrectUrl(self):
        content = '<meta http-equiv="refresh" content="3;http://www.youtube.com/"><head>'
        self.assertIsNone(source.lib.check_for_meta(content, ''))

    def test_check_for_meta_len_2(self):#incorrect content split
        content = '<meta http-equiv="refresh" content="url=http://www.youtube.com/"><head>'
        self.assertEqual(source.lib.check_for_meta(content, ''), None)

    def test_fix_market_url(self):
        url = 'market://search?q=pname:net.mandaria.tippytipper'
        self.assertEqual(source.lib.fix_market_url(url),'http://play.google.com/store/apps/search?q=pname:net.mandaria.tippytipper')
        self.assertEqual(source.lib.fix_market_url(''),'http://play.google.com/store/apps/')
        self.assertEqual(source.lib.fix_market_url('someapp'),'http://play.google.com/store/apps/someapp')


    def test_make_pycurl_request(self):
        content = "Test content"
        redirectUrl = "tech-mail.ru"

        mockCurl = mock.Mock()
        mockCurl.getinfo.return_value = redirectUrl

        mockIO = mock.Mock()
        mockIO.getvalue.return_value = content

        with mock.patch("StringIO.StringIO", mock.Mock(return_value=mockIO)):
             curl_mock = mock.Mock()
             curl_mock.getinfo.return_value = 'url'
             with mock.patch('source.lib.pycurl.Curl', mock.Mock(return_value=curl_mock)):
                self.assertEqual(source.lib.make_pycurl_request('url', 1), ('', 'url'))

    def test_make_pycurl_request_useragent(self):
        curl_mock = mock.Mock()
        curl_mock.getinfo.return_value = 'url'
        with mock.patch('source.lib.pycurl.Curl', mock.Mock(return_value=curl_mock)):
            self.assertEqual(source.lib.make_pycurl_request('url', 1,'safazila'), ('', 'url'))


    def test_get_url_check_error(self):
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            with mock.patch('source.lib.logger',mock.Mock()):
                self.assertEquals(source.lib.get_url("url",2),("url",'ERROR',None))

    def test_get_url_check_redirect(self):
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=('content', 'http://odnoklassniki.ru/unittest.redirect'))):
            self.assertEquals(source.lib.get_url('http://odnoklassniki.ru/unittest.redirect',1),(None,None,'content'))

    def test_get_url_not_redirect(self):
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=('content', 'http://ololo.ru/sailorspirit'))):
            self.assertEquals(source.lib.get_url("http://ololo.ru/sailorspirit",1),("http://ololo.ru/sailorspirit",source.lib.REDIRECT_HTTP,'content'))

    def test_get_url_meta(self):
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=('content', None))):
            with mock.patch('source.lib.check_for_meta',mock.Mock(return_value=(None))):
                self.assertEquals(source.lib.get_url('url',1),(None,None,'content'))

    def test_get_url_not_meta(self):
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=('content', None))):
            with mock.patch('source.lib.check_for_meta',mock.Mock(return_value=('new_url'))):
                self.assertEquals(source.lib.get_url('url',1),('new_url',source.lib.REDIRECT_META,'content'))

    def test_get_url_market(self):
        with mock.patch('source.lib.make_pycurl_request', mock.Mock(return_value=('content', 'market://ololo.ru/sailorspirit'))):
            self.assertEquals(source.lib.get_url("market://ololo.ru/sailorspirit",1),(u"http://play.google.com/store/apps/ololo.ru/sailorspirit",source.lib.REDIRECT_HTTP,'content'))

    def test_get_redirect_history_mm_ok(self):
        with mock.patch('source.lib.prepare_url',mock.Mock(return_value='http://my.mail.ru/apps/lel')):
            self.assertEquals(source.lib.get_redirect_history("http://my.mail.ru/apps/lel",3,30),([],["http://my.mail.ru/apps/lel"],[]))

    def test_get_redirect_error(self):
        with mock.patch('source.lib.prepare_url',mock.Mock(return_value='url1')),\
            mock.patch('source.lib.get_url',mock.Mock(return_value=('url2','ERROR','content'))),\
            mock.patch('source.lib.get_counters',mock.Mock(return_value=['GOOGLE_ANALYTICS'])):
                self.assertEquals(source.lib.get_redirect_history('url1',3),(['ERROR'],['url1','url2'],['GOOGLE_ANALYTICS']));#useragent does not matter
    def test_get_redirect_max_redirects(self):
        with mock.patch('source.lib.prepare_url',mock.Mock(return_value='url1')),\
            mock.patch('source.lib.get_url',mock.Mock(return_value=('url2','REDIR','content'))),\
            mock.patch('source.lib.get_counters',mock.Mock(return_value=['GOOGLE_ANALYTICS'])):
                self.assertEquals(source.lib.get_redirect_history('url1',3,1),(['REDIR'],['url1','url2'],['GOOGLE_ANALYTICS']))#max_redirect in argument to end cycle
    def test_get_redirect_check_cycle_redir(self):
        with mock.patch('source.lib.prepare_url',mock.Mock(return_value='url1')),\
            mock.patch('source.lib.get_url',mock.Mock(return_value=('url1','CYCLE','content'))),\
            mock.patch('source.lib.get_counters',mock.Mock(return_value=['GOOGLE_ANALYTICS'])):
                self.assertEquals(source.lib.get_redirect_history('url1',3,1),(['CYCLE'],['url1','url1'],['GOOGLE_ANALYTICS']))
    def test_get_redirect_no_redir(self):
        with mock.patch('source.lib.prepare_url',mock.Mock(return_value='url1')),\
            mock.patch('source.lib.get_url',mock.Mock(return_value=(None,None,None))):
                self.assertEquals(source.lib.get_redirect_history('url1',3),([],['url1'],[]))

    def test_prepare_url_none(self):
        self.assertEquals(source.lib.prepare_url(None),None)

    def test_prepare_url_ok(self):
        self.assertEquals(source.lib.prepare_url('http://www.mail.ru/news/weather?id=232'),'http://www.mail.ru/news/weather?id=232')

    def test_prepare_url_unicode_err(self):# how do i mock encode?!
        mock_netloc = mock.Mock()
        mock_netloc.encode.side_effect = UnicodeError
        mock_urlunparse = mock.Mock(return_value='http://someurl.le/')
        with mock.patch("source.lib.urlparse", mock.Mock(return_value=(None, mock_netloc, None, None, None, None))),\
            mock.patch("source.lib.quote", mock.Mock()),\
            mock.patch("source.lib.quote_plus", mock.Mock()),\
            mock.patch("source.lib.urlunparse", mock_urlunparse):
              result = source.lib.prepare_url('http://someurl.le/')
              self.assertEqual(result, 'http://someurl.le/')
