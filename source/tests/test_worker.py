import unittest
import mock
import source.lib
from source.lib import worker
from tarantool.error import DatabaseError

class WokerTestCase(unittest.TestCase):
    def test_get_redirect_history_from_task_error_history_not_recheck(self):
        mock_task = mock.Mock()
        mock_task.data = {
            'recheck': False,
            'url': 'url',
            'url_id': 0
        }
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=[['ERROR'], [], []])),\
            mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value='url')):
             self.assertEqual(worker.get_redirect_history_from_task(mock_task, 1), (True, mock_task.data))

    def test_get_redirect_history_from_task_recheck_not_suspicious(self):
        mock_task = mock.Mock()
        mock_task.data = {
            'recheck': True,
            'url': 'url',
            'url_id': 0
        }
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=[['lel'],[],[]])),\
             mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value='url')):
            waiting_result = (False, {
                "url_id": mock_task.data["url_id"],
                "result": [['lel'],[],[]],
                "check_type": "normal"
            })
            self.assertEqual(worker.get_redirect_history_from_task(mock_task, 1), waiting_result)

    def test_get_redirect_history_from_task_recheck_suspicious(self):
        mock_task = mock.Mock()
        mock_task.data = {
            'recheck': True,
            'url': 'url',
            'url_id': 0,
            'suspicious': 'suspicious'
        }
        with mock.patch('source.lib.worker.get_redirect_history', mock.Mock(return_value=[['ERROR'],[],[]])),\
             mock.patch('source.lib.worker.to_unicode', mock.Mock(return_value='url')):
            waiting_result = (False, {
                "url_id": mock_task.data["url_id"],
                "result": [['ERROR'],[],[]],
                "check_type": "normal",
                'suspicious': 'suspicious'
            })
            self.assertEqual(worker.get_redirect_history_from_task(mock_task, 1), waiting_result)

    def test_worker_no_proc(self):
        mock_get_redirect_history_from_task = mock.Mock()
        with mock.patch('source.lib.worker.os.path.exists', mock.Mock(side_effect=[False, False])),\
             mock.patch('source.lib.worker.get_tube', mock.MagicMock()),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock_get_redirect_history_from_task):
            worker.worker(mock.MagicMock(), 42)
            self.assertEqual(mock_get_redirect_history_from_task.call_count, 0)

    def test_worker_no_task(self):
        config = mock.MagicMock()
        pid = 42
        tube = mock.MagicMock()#magic is cool
        tube.take = mock.Mock(return_value=False)
        mock_get_tube = mock.Mock(return_value=tube)
        mock_get_redirect_history_from_task = mock.Mock()
        with mock.patch('source.lib.worker.os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_tube', mock_get_tube),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock_get_redirect_history_from_task):
            worker.worker(config, pid)
            self.assertEqual(mock_get_redirect_history_from_task.call_count, 0)

    def test_worker_no_result(self):########
        config = mock.MagicMock()
        pid=42
        mock_input_tube = mock.MagicMock()
        mocked_put=mock.Mock()
        mock_input_tube.put=mocked_put
        mock_output_tube = mock.MagicMock()
        mock_get_redirect_history_from_task = mock.Mock(return_value=None)
        with mock.patch('source.lib.worker.os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[mock_input_tube, mock_output_tube])),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock_get_redirect_history_from_task):
            worker.worker(config, pid)
            self.assertEquals(mock_input_tube.put.call_count,0)

    def test_worker_result_input(self):
        config = mock.MagicMock()
        pid=42
        mock_input_tube = mock.MagicMock()
        mock_output_tube = mock.MagicMock()
        mock_get_redirect_history_from_task = mock.Mock(return_value=[True, 'data'])
        with mock.patch('source.lib.worker.os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[mock_input_tube, mock_output_tube])),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock_get_redirect_history_from_task):
            worker.worker(config, pid)
            self.assertGreater(mock_input_tube.put.call_count, 0)
            self.assertEqual(mock_output_tube.put.call_count, 0)

    def test_worker_result_no_input(self):
        config = mock.MagicMock()
        pid=42
        mock_input_tube = mock.MagicMock()
        mock_output_tube = mock.MagicMock()
        mock_get_redirect_history_from_task = mock.Mock(return_value=[False, 'data'])
        with mock.patch('source.lib.worker.os.path.exists', mock.Mock(side_effect=[True, False])),\
             mock.patch('source.lib.worker.get_tube', mock.Mock(side_effect=[mock_input_tube, mock_output_tube])),\
             mock.patch('source.lib.worker.get_redirect_history_from_task', mock_get_redirect_history_from_task):
            worker.worker(config, pid)
            self.assertEqual(mock_input_tube.put.call_count, 0)
            self.assertGreater(mock_output_tube.put.call_count, 0)

    def test_worker_task_DBException(self):
        config_mock = mock.Mock()
        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}
        task_mock = mock.Mock()
        task_mock.data = {'url': 'error_url', 'url_id': 5}
        task_mock.meta = mock.Mock(return_value={'pri': 'pri'})
        task_mock.ack = mock.Mock(side_effect=DatabaseError)
        tube_mock.take = mock.Mock(return_value=task_mock)
        with mock.patch('source.lib.worker.get_tube', mock.Mock(return_value=tube_mock), create=True):
            with mock.patch('source.lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('source.lib.worker.get_redirect_history_from_task', mock.Mock(return_value=(True, task_mock.data)), create=True):
                        with mock.patch('source.lib.worker.logger.info', mock.Mock(), create=True):
                            worker.worker(config_mock, None)
                            self.assertRaises(DatabaseError)
