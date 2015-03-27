import mock

__author__ = 'mid'

import unittest
from source.lib import utils
from urllib2 import URLError

def execfile_fake_for_correct(filepath, variables):
    variables['KEY'] = 'VALUE'
    variables['UPPER_CASE'] = 'value'

def execfile_fake_CamelCase_variables(filepath, variables):
    variables['KEY'] = 'value'
    variables['CamelCase'] = 'ingore'
    variables['Key'] = 'ignore'

def pass_func(args):
    pass

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
                utils.create_pidfile('/my/way')
        m_open.assert_called_once_with('/my/way', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_parse_cmd_args_with_config(self):
        args = ['--config', './config']
        parser = utils.parse_cmd_args(args)
        self.assertEqual(parser.config, './config',)
        self.assertFalse(parser.daemon)
        self.assertIsNone(parser.pidfile)

    def test_parse_cmd_args_without_config(self):
        with self.assertRaises(SystemExit):
            utils.parse_cmd_args([])

    def test_parse_cmd_args_check_add_daemon_argument(self):
        args = ['--config', './config',
                 '--pid', './pidfile',
                 '--daemon']
        parser = utils.parse_cmd_args(args)
        self.assertEqual(parser.config, './config')
        self.assertEqual(parser.pidfile, './pidfile')
        self.assertTrue(parser.daemon)

    def test_parse_cmd_args_check_add_pidfile(self):
        args = ['--config', './config',
                 '--pid', './pidfile']
        parser = utils.parse_cmd_args(args)
        self.assertEqual(parser.config, './config')
        self.assertEqual(parser.pidfile, './pidfile')
        self.assertFalse(parser.daemon)

    def test_get_tube_set_args(self):
        fake_space = 42
        tarantool_queue_mock = mock.Mock()
        with mock.patch('source.lib.utils.tarantool_queue', tarantool_queue_mock):
            utils.get_tube('DA_HOST', 666, fake_space, 'DA_NAME')
        tarantool_queue_mock.Queue.assert_called_once_with(
            host='DA_HOST',
            port=666,
            space=fake_space
        )

    def test_get_tube__tube_has_been_called(self):
        fake_space = 0
        queue_mock = mock.Mock()
        with mock.patch('source.lib.utils.tarantool_queue.Queue', mock.Mock(return_value=queue_mock)):
            utils.get_tube('host', 8080, fake_space, 'name')
        queue_mock.tube.assert_called_once_with('name')

    def test_load_config_from_pyfile_uppercase_variables(self):
        with mock.patch('__builtin__.execfile', mock.Mock(side_effect=execfile_fake_for_correct)):
            config = utils.load_config_from_pyfile('filepath')
        self.assertEqual(config.KEY, 'VALUE')
        self.assertEqual(config.UPPER_CASE, 'value')

    def test_load_config_from_pyfile_camelcase_variables(self):
        with mock.patch('__builtin__.execfile', mock.Mock(side_effect=execfile_fake_CamelCase_variables)):
            config = utils.load_config_from_pyfile('filepath')
        self.assertFalse(hasattr(config, 'CamelCase'))
        self.assertFalse(hasattr(config, 'Key'))

    def test_spawn_workers_many(self):
        p_mock = mock.Mock()
        with mock.patch('source.lib.utils.Process', mock.Mock(return_value=p_mock)):
            utils.spawn_workers(34, pass_func, [], parent_pid=10)
            self.assertEqual(p_mock.start.call_count, 34)
    def test_spawn_workers_many_one(self):
        p_mock = mock.Mock()
        with mock.patch('source.lib.utils.Process', mock.Mock(return_value=p_mock)):
            utils.spawn_workers(1, pass_func, [], parent_pid=11)
            self.assertEqual(p_mock.start.call_count, 1)

    def test_check_network_ok(self):
        with mock.patch('lib.utils.urllib2.urlopen', mock.Mock()):
            self.assertTrue(utils.check_network_status('url', 66))

    def test_check_network_not_ok(self):
        with mock.patch('lib.utils.urllib2.urlopen', mock.Mock(side_effect=ValueError)):
            self.assertFalse(utils.check_network_status('url', 66))



