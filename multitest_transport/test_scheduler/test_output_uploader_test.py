# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A test for test_output_uploader.

Tests for google3.wireless.android.test_tools.mtt.test_scheduler
.test_output_uploader.
"""
import json
import os.path
import mock
from google.appengine.ext import testbed
from absl.testing import absltest
from multitest_transport.models import build
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import test_output_uploader
from multitest_transport.util import env
from multitest_transport.util import file_util
from multitest_transport.util import tfc_client


class TestOutputUploaderTest(absltest.TestCase):

  def setUp(self):
    root_path = os.path.dirname(__file__)
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.testbed.init_taskqueue_stub(root_path=root_path)
    self.taskqueue_stub = self.testbed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)

  def tearDown(self):
    self.testbed.deactivate()

  @mock.patch.object(tfc_client, 'GetRequest')
  def testGetFileUrls_withStandAloneMode(self, mock_get_request):
    """Test get file urls."""
    env.FILE_OPEN_URL_FORMAT = 'http://{hostname}:8800/open'
    mock_test = ndb_models.Test(name='test', command='command')
    mock_test_run = ndb_models.TestRun(
        test=mock_test,
        request_id='request_id',
        state=ndb_models.TestRunState.UNKNOWN,
        output_path='sample_out_path',
        output_storage=file_util.FileStorage.LOCAL_FILE_SYSTEM)

    mock_tfc_request = {
        'command_attempts': [{
            'command_id': '89001',
            'attempt_id': 'cb5179e3-ea4c',
        }, {
            'command_id': '89002',
            'attempt_id': 'acsdsadsufioa',
        }]
    }
    mock_get_request.return_value = mock_tfc_request
    file_path_list = test_output_uploader._GetFileUrls(mock_test_run)
    path_1 = 'http://localhost:8800/open/sample_out_path/89001/cb5179e3-ea4c'
    path_2 = 'http://localhost:8800/open/sample_out_path/89002/acsdsadsufioa'
    self.assertIn(path_1, file_path_list)
    self.assertIn(path_2, file_path_list)

  @mock.patch.object(test_output_uploader, '_GetFileNames')
  @mock.patch.object(test_output_uploader, '_GetFileUrls')
  def testScheduleUploadJobs(self,
                             mock_get_file_urls,
                             mock_get_file_names):
    """Test Schedule Upload Events."""
    mock_test = ndb_models.Test(name='test', command='command')
    mock_test_run = ndb_models.TestRun(
        test=mock_test,
        test_output_upload_configs=[
            ndb_models.TestOutputUploadConfig(url='mtt:///id/upload_path')
        ])
    mock_test_run.put()
    path = 'http://localhost:8800/open/sample_path'
    mock_get_file_urls.return_value = [path]
    mock_get_file_names.return_value = ['error.txt', 'out.txt', 'test.zip']
    job_list = test_output_uploader.ScheduleUploadJobs(mock_test_run.key.id())
    job_1 = {
        'file_name': 'http://localhost:8800/open/sample_path/error.txt',
        'url': 'mtt:///id/upload_path'
    }
    job_2 = {
        'file_name': 'http://localhost:8800/open/sample_path/out.txt',
        'url': 'mtt:///id/upload_path'
    }
    job_3 = {
        'file_name': 'http://localhost:8800/open/sample_path/test.zip',
        'url': 'mtt:///id/upload_path'
    }
    self.assertIsNotNone(job_list)
    self.assertIn(job_1, job_list)
    self.assertIn(job_2, job_list)
    self.assertIn(job_3, job_list)

    file_info_path = 'http://localhost:8800/open/sample_path/FILES'
    mock_get_file_names.assert_called_with(file_info_path)

    tasks = self.taskqueue_stub.get_filtered_tasks(
        queue_names=[test_output_uploader._TEST_OUTPUT_UPLOADER_QUEUE])
    self.assertEqual(3, len(tasks))
    task = tasks[0]
    data = json.loads(task.payload)
    self.assertEqual('http://localhost:8800/open/sample_path/error.txt',
                     data['file_name'])
    self.assertEqual('mtt:///id/upload_path', data['url'])

  def testScheduleUploadJobs_withEmptyUploadConfig(self):
    """Test Schedule Upload Events with empty upload config."""
    mock_test = ndb_models.Test(name='test', command='command')
    mock_test_run = ndb_models.TestRun(
        test=mock_test, test_output_upload_configs=[])
    mock_test_run.put()
    job_list = test_output_uploader.ScheduleUploadJobs(mock_test_run.key.id())
    self.assertEqual(len(job_list), 0)

  def testParseBrowsepyFilename(self):
    """Test _ParseBrowsepyFilename."""
    browsepy_file_name = 'http://8800/open/app_default_bucket/sample.txt'
    file_name = test_output_uploader._ParseBrowsepyFilename(browsepy_file_name)
    self.assertEqual(file_name, 'sample.txt')

    bad_file_name = 'http://8800/open/random_name'
    file_name = test_output_uploader._ParseBrowsepyFilename(bad_file_name)
    self.assertIsNone(file_name)

  @mock.patch.object(build, 'GetBuildChannel')
  def testUpload(self, mock_get_build_channel):
    """Test Process upload event."""
    mock_build_channel = mock.MagicMock()
    mock_build_channel.UploadFile = mock.MagicMock()
    mock_get_build_channel.return_value = mock_build_channel
    test_output_uploader.Upload(
        'http://localhost:8800/open/app_default_bucket/test_runs/stdout.txt',
        'mtt:///id/upload_path')
    mock_build_channel.UploadFile.assert_called_with(
        'http://localhost:8800/open/app_default_bucket/test_runs/stdout.txt',
        'upload_path/test_runs/stdout.txt')


if __name__ == '__main__':
  absltest.main()
