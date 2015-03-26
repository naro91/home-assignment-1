# coding: utf-8

import json
import unittest
import mock
from notification_pusher import create_pidfile, notification_worker, done_with_processed_tasks
import requests
import tarantool
from source import notification_pusher
from source.notification_pusher import stop_handler, start_worker, start_worker_in_cycle, run_greenlet_for_task, \
    main_loop, parse_cmd_args, daemonize, install_signal_handlers, daemon_os_fork


class NotificationPusherTestCase(unittest.TestCase):
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                create_pidfile('/file/path')

        m_open.assert_called_once_with('/file/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_notification_worker(self):
        response = mock.Mock()
        response.status_code = 200
        requests_post_mock = mock.Mock(return_value=response)
        logger_info_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        task_queue_mock.put = mock.Mock()
        task_mock = mock.Mock()
        task_mock.data = {'callback_url' : 'tech-mail.ru'}
        task_mock.task_id = 0
        current_thread = mock.Mock()
        with mock.patch('notification_pusher.current_thread', mock.Mock(return_value=current_thread), create=True):
            with mock.patch('notification_pusher.logger.info', logger_info_mock, create=True):
                with mock.patch('notification_pusher.requests.post', requests_post_mock, create=True):
                    notification_worker(task_mock, task_queue_mock, 'test_args', test_kwargs = 'ok')
                    logger_info_mock.assert_any_call('Send data to callback url [tech-mail.ru].')
                    requests_post_mock.assert_called_once_with('tech-mail.ru', 'test_args', data='{"id": 0}', test_kwargs = 'ok')
                    logger_info_mock.assert_any_call('Callback url [tech-mail.ru] response status code=200.')
                    task_queue_mock.put.assert_called_once_with((task_mock, 'ack'))
                    self.assertEqual(current_thread.name, "pusher.worker#0")

    def test_notification_worker_exception(self):
        logger_info_mock = mock.Mock()
        task_queue_mock = mock.Mock()
        task_queue_mock.put = mock.Mock()
        task_mock = mock.Mock()
        task_mock.data = {'callback_url' : 'tech-mail.ru'}
        task_mock.task_id = 0
        current_thread_mock = mock.Mock()
        with mock.patch('notification_pusher.current_thread', mock.Mock(return_value=current_thread_mock), create=True):
            with mock.patch('notification_pusher.logger.info', logger_info_mock, create=True):
                with mock.patch('notification_pusher.requests.post', mock.Mock(side_effect=requests.RequestException), create=True):
                    notification_worker(task_mock, task_queue_mock, 'test_args', test_kwargs = 'ok')
                    logger_info_mock.assert_any_call('Send data to callback url [tech-mail.ru].')
                    task_queue_mock.put.assert_called_once_with((task_mock, 'bury'))
                    self.assertEqual(current_thread_mock.name, "pusher.worker#0")


    def test_done_with_processed_tasks(self):
        task_mock = mock.Mock()
        task_mock.task_id = 1
        task_mock.my_action = mock.Mock()
        task_queue_mock = mock.Mock()
        task_queue_mock.qsize = mock.Mock(return_value=1)
        task_queue_mock.get_nowait = mock.Mock(return_value=(task_mock, 'my_action'))
        with mock.patch('notification_pusher.logger.debug', mock.Mock(), create=True):
            done_with_processed_tasks(task_queue_mock)
            task_mock.my_action.assert_called_once_with()

    def test_done_with_processed_tasks_exeption(self):
        task_mock = mock.Mock()
        task_mock.my_action = mock.Mock(side_effect=tarantool.DatabaseError)
        task_queue_mock = mock.Mock()
        task_queue_mock.qsize = mock.Mock(return_value=2)
        task_queue_mock.get_nowait = mock.Mock(return_value=(task_mock, 'my_action'))
        logger_debug = mock.Mock()
        logger_exception = mock.Mock()
        with mock.patch('notification_pusher.logger.debug', logger_debug, create=True):
            with mock.patch('notification_pusher.logger.exception', logger_exception, create=True):
                done_with_processed_tasks(task_queue_mock)
                self.assertTrue(logger_exception.called)


    def test_stop_handler(self):
        temp_run_application = notification_pusher.run_application
        temp_exit_code = notification_pusher.exit_code
        signum = 1
        logger_info_mock = mock.Mock()
        with mock.patch('notification_pusher.current_thread', mock.Mock(), create=True):
            with mock.patch('notification_pusher.logger.info', logger_info_mock, create=True):
                stop_handler(signum)
                self.assertTrue(notification_pusher.run_application == False)
                self.assertTrue(notification_pusher.exit_code == (notification_pusher.SIGNAL_EXIT_CODE_OFFSET + signum))
                logger_info_mock.assert_called_once_with('Got signal #{signum}.'.format(signum=signum))
        notification_pusher.run_application = temp_run_application
        notification_pusher.exit_code = temp_exit_code

    def test_start_worker(self):
        task_mock = mock.Mock()
        task_mock.task_id = 1
        worker_mock = mock.Mock()
        worker_mock.start = mock.Mock()
        worker_pool_mock = mock.Mock()
        worker_pool_mock.add = mock.Mock()
        processed_task_queue_mock = mock.Mock()
        config_mock = mock.Mock()
        logger_info_mock = mock.Mock()
        number = 1
        with mock.patch('notification_pusher.logger.info',logger_info_mock, create=True ):
            with mock.patch('source.notification_pusher.Greenlet', mock.Mock(return_value=worker_mock), create=True):
                start_worker(number, task_mock, processed_task_queue_mock, config_mock, worker_pool_mock)
                logger_info_mock.assert_called_once_with('Start worker#1 for task id=1.')
                worker_pool_mock.add.assert_called_once_with(worker_mock)
                worker_mock.start.assert_called_once_with()

    def test_start_worker_in_cycle(self):
        free_workers_count = 1
        tube_mock = mock.Mock()
        task_mock = mock.Mock()
        task_mock.task_id = 1
        worker_pool_mock = mock.Mock()
        worker_pool_mock.add = mock.Mock()
        processed_task_queue_mock = mock.Mock()
        config_mock = mock.Mock()
        logger_debug_mock = mock.Mock()
        with mock.patch('notification_pusher.logger.debug', logger_debug_mock, create=True):
            with mock.patch('source.notification_pusher.Greenlet', mock.Mock(return_value=mock.Mock()), create=True):
                start_worker_in_cycle(free_workers_count, tube_mock, config_mock, processed_task_queue_mock, worker_pool_mock)
                logger_debug_mock.assert_called_once_with('Get task from tube for worker#0.')

    def test_run_greenlet_for_task_run_app_True(self):
        tube_mock = mock.Mock()
        task_mock = mock.Mock()
        logger_info_mock = mock.Mock()
        task_mock.task_id = 1
        worker_pool_mock = mock.Mock()
        worker_pool_mock.free_count = mock.Mock(return_value=1)
        processed_task_queue_mock = mock.Mock()
        config_mock = mock.Mock()
        config_mock.SLEEP = 10
        logger_debug_mock = mock.Mock()
        # в этой функции меняется переменная проверяемая в условии цикла
        def sleep(param):
            notification_pusher.run_application = False
            pass
        with mock.patch('notification_pusher.logger.debug', logger_debug_mock, create=True):
            with mock.patch('notification_pusher.logger.info', logger_info_mock, create=True):
                with mock.patch('source.notification_pusher.Greenlet', mock.Mock(return_value=mock.Mock()), create=True):
                    with mock.patch('source.notification_pusher.done_with_processed_tasks', mock.Mock(), create=True):
                        with mock.patch('source.notification_pusher.sleep', sleep, create=True):
                            run_greenlet_for_task(worker_pool_mock, tube_mock, config_mock, processed_task_queue_mock)
                            logger_debug_mock.assert_any_call('Pool has 1 free workers.')
                            self.assertTrue(logger_debug_mock.call_count == 2)
                            logger_info_mock.assert_any_call('Stop application loop.')


    def test_main_loop(self):
        config = mock.Mock()
        logger = mock.Mock()
        with mock.patch('notification_pusher.logger', logger, create=True):
            with mock.patch('source.notification_pusher.Pool', mock.Mock(), create=True):
                with mock.patch('source.notification_pusher.tarantool_queue', mock.Mock(), create=True):
                    with mock.patch('source.notification_pusher.Greenlet', mock.Mock(return_value=mock.Mock()), create=True):
                        with mock.patch('source.notification_pusher.run_greenlet_for_task', mock.Mock(), create=True):
                            main_loop(config)

    # def test_parse_cmd_args(self):
    #     print parse_cmd_args({'--pid', '-P'})

    def test_daemonize(self):
        def os_fork():
            try:
                os_fork.a += 1
            except AttributeError:
                os_fork.a = 0
            return os_fork.a
        os = mock.Mock()
        os.fork = os_fork
        os.setsid = mock.Mock()
        os._exit = mock.Mock()
        with mock.patch('source.notification_pusher.os', os, create=True):
            daemonize()
            os.setsid.assert_called_once_with()
            self.assertTrue(os.fork() == 2)
            os._exit.assert_called_once_with(0)
            daemonize()
            os.setsid.assert_called_once_with()
            self.assertTrue(os._exit.call_count == 2)

    def test_daemon_os_fork_exeption(self):
        os = mock.Mock()
        os.fork = mock.Mock(side_effect=OSError)
        os.setsid = mock.Mock()
        os._exit = mock.Mock()
        with mock.patch('source.notification_pusher.os', os, create=True):
            try:
                daemon_os_fork()
            except Exception as ex:
                self.assertTrue(os._exit.call_count == 0)
                self.assertTrue(os.setsid.call_count == 0)
                pass

    # def test_install_signal_handlers(self):
    #     gevent_signal_mock = mock.Mock()
    #     stop_handler_mock = mock.Mock()
    #     with mock.patch('notification_pusher.gevent.signal', gevent_signal_mock, create=True):
    #         with mock.patch('notification_pusher.stop_handler', stop_handler_mock, create=True):
    #             install_signal_handlers()
    #             self.assertEqual(gevent_signal_mock.call_count, 4)
    #             for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
    #                 gevent_signal_mock.assert_any_call(signum, stop_handler_mock, signum)