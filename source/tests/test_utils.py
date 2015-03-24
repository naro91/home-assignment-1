import mock

__author__ = 'mid'

import unittest
import source.lib
from source.lib import utils

class UtilsTestCase(unittest.TestCase):
    def test_demonize(self):
        pid = 42
        with mock.patch('os.fork', mock.Mock(return_value=pid)):
            with mock.patch('os._exit', mock.Mock()) as mock_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()
                    self.assertEqual(mock_exit.call_count, 1)
    def test_demonize_exc(self):
        with mock.patch('os.fork', mock.Mock(side_effect=OSError(1, 'erer')), create=True):
            with mock.patch('os._exit', mock.Mock()):
                with mock.patch('os.setsid', mock.Mock()):
                    with self.assertRaises(Exception):
                        utils.daemonize()

    def test_demonize_pid0(self):
        with mock.patch('os.fork', mock.Mock(return_value=0), create=True):
            with mock.patch('os._exit', mock.Mock()) as mock_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()
                    self.assertEqual(mock_exit.call_count, 0)
    def test_demonize_pid0_exception(self):
        with mock.patch('os.fork', mock.Mock(side_effect=[0, OSError(1, 'Ops')]), create=True):
            with mock.patch('os._exit', mock.Mock()):
                with mock.patch('os.setsid', mock.Mock()):
                    with self.assertRaises(Exception):
                        utils.daemonize()

    def test_demonize_pid0_pidnot0(self):
        with mock.patch('os.fork', mock.Mock(side_effect=[0, 10]), create=True):
            with mock.patch('os._exit', mock.Mock(), create=True) as mock_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()
                    self.assertEqual(mock_exit.call_count, 1)
    def test_create_pidfile(self):
        pid = 42
        with mock.patch('source.lib.utils.open', mock.mock_open(), create=True) as m_open:
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('/some/path')
        m_open.assert_called_once_with('/some/path', 'w')
        m_open().write.assert_called_once_with(str(pid))
