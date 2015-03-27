
import unittest
import mock
from mock import patch
from source.lib.utils import Config
from source import redirect_checker


def stop_cycle(self):
    redirect_checker.loop = False

config = Config()
config.CHECK_URL = 'url'
config.HTTP_TIMEOUT = 1
config.WORKER_POOL_SIZE = 4
config.SLEEP = 1
config.LOGGING = 'logging'
config.EXIT_CODE = 31


class RedirectCheckerTestCase(unittest.TestCase):

    def test_main_loop_with_incorrect_type_of_param(self):
        incorrect_config = 'magic'
        with self.assertRaises(AttributeError):
            redirect_checker.main_loop(incorrect_config)

    def test_main_loop_check_network_status_bad(self):
        mock_spawn_workers = mock.Mock()
        mock_active_children = mock.Mock()
        with patch('source.redirect_checker.check_network_status', mock.Mock(return_value=False)),\
             patch('source.redirect_checker.spawn_workers', mock_spawn_workers),\
             patch('source.redirect_checker.active_children',return_value=[mock.Mock()]),\
             patch('source.redirect_checker.sleep', mock.Mock(side_effect=stop_cycle)):
            redirect_checker.main_loop(config)
            self.assertEqual(mock_spawn_workers.call_count, 0)

            redirect_checker.loop = True

    def test_main_loop_check_network_status_ok_and_workers_number_ok(self):
        mock_spawn_workers = mock.Mock()
        with patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True)),\
             patch('source.redirect_checker.spawn_workers', mock_spawn_workers),\
             patch('source.redirect_checker.active_children', mock.Mock(return_value=[mock.Mock()])),\
             patch('source.redirect_checker.sleep', mock.Mock(side_effect=stop_cycle)):
            redirect_checker.main_loop(config)
            self.assertGreater(mock_spawn_workers.call_count, 0)
            redirect_checker.loop = True

    def test_main_loop_check_network_status_ok_and_workers_number_bad(self):
        mock_stop_cycle = mock.Mock(side_effect=stop_cycle)
        mock_spawn_workers = mock.Mock()
        mock_active_children = mock.Mock()
        with patch('source.redirect_checker.check_network_status', mock.Mock(return_value=True)),\
             patch('source.redirect_checker.spawn_workers', mock_spawn_workers),\
             patch('source.redirect_checker.active_children', mock.Mock(return_value=[mock_active_children]*config.WORKER_POOL_SIZE)),\
             patch('source.redirect_checker.sleep', mock_stop_cycle):
                redirect_checker.main_loop(config)
                self.assertEqual(mock_spawn_workers.call_count, 0)
                redirect_checker.loop = True


    def test_main_with_incorrect_type_of_param(self):
        incorrect_args = 100
        with self.assertRaises(TypeError):
            redirect_checker.main(incorrect_args)


    def test_main_check_args_is_daemon_and_pidfile(self):
        args = mock.MagicMock()
        args.daemon = True
        args.pidfile = True
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        with patch('source.redirect_checker.parse_cmd_args', mock.Mock(return_value=args)),\
             patch('source.redirect_checker.daemonize', mock_daemonize),\
             patch('source.redirect_checker.create_pidfile', mock_create_pidfile),\
             patch('source.redirect_checker.load_config_from_pyfile', mock.Mock(return_value=config)),\
             patch('source.redirect_checker.dictConfig', mock.Mock()),\
             patch('source.redirect_checker.main_loop', mock.Mock()),\
             patch('source.redirect_checker.os.path.realpath', mock.Mock()),\
             patch('source.redirect_checker.os.path.expanduser', mock.Mock()):
                return_exitcode = redirect_checker.main(args)
                self.assertEqual(return_exitcode, config.EXIT_CODE)
                self.assertGreater(mock_daemonize.call_count, 0)
                self.assertGreater(mock_create_pidfile.call_count, 0)

    def test_main_check_args_is_not_daemon_and_pidfile(self):
        args = mock.MagicMock()
        args.daemon = False
        args.pidfile = False
        mock_daemonize = mock.Mock()
        mock_create_pidfile = mock.Mock()
        with patch('source.redirect_checker.parse_cmd_args', mock.Mock(return_value=args)),\
             patch('source.redirect_checker.daemonize', mock_daemonize),\
             patch('source.redirect_checker.create_pidfile', mock_create_pidfile),\
             patch('source.redirect_checker.load_config_from_pyfile', mock.Mock(return_value=config)),\
             patch('source.redirect_checker.dictConfig', mock.Mock()),\
             patch('source.redirect_checker.main_loop', mock.Mock()),\
             patch('source.redirect_checker.os.path.realpath', mock.Mock()),\
             patch('source.redirect_checker.os.path.expanduser', mock.Mock()):
                return_exitcode = redirect_checker.main(args)
                self.assertEqual(return_exitcode, config.EXIT_CODE)
                self.assertEqual(mock_daemonize.call_count, 0)
                self.assertEqual(mock_create_pidfile.call_count, 0)
