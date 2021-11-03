# Copyright 2020 Google LLC
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

"""Tests for service_checker."""
import subprocess

from absl.testing import absltest
import mock
import requests
from tradefed_cluster.util import ndb_test_lib

from multitest_transport.core import service_checker
from multitest_transport.util import env
from multitest_transport.util import file_util
from multitest_transport.models import sql_models


class DatastoreCheckerTest(ndb_test_lib.NdbWithContextTest):

  def testRun(self):
    service_checker.DatastoreChecker.Run()


class FileServerCheckerTest(absltest.TestCase):

  def setUp(self):
    super(FileServerCheckerTest, self).setUp()
    env.STORAGE_PATH = '/'

  @mock.patch.object(file_util.RemoteFileHandle, 'ListFiles')
  def testRun(self, mock_list_files):
    mock_list_files.return_value = []
    service_checker.FileServerChecker.Run()

  @mock.patch.object(file_util.RemoteFileHandle, 'ListFiles')
  def testRun_notFound(self, mock_list_files):
    mock_list_files.return_value = None
    with self.assertRaises(RuntimeError):
      service_checker.FileServerChecker.Run()

  @mock.patch.object(file_util.RemoteFileHandle, 'ListFiles')
  def testRun_error(self, mock_list_files):
    mock_list_files.side_effect = RuntimeError()
    with self.assertRaises(RuntimeError):
      service_checker.FileServerChecker.Run()


class FileClCheckerTest(absltest.TestCase):

  @mock.patch.object(subprocess, 'Popen')
  def testRun_error(self, mock_popen):
    mock_process = mock.MagicMock()
    mock_process.communicate.return_value = ('None', 'None')
    mock_popen.return_value = mock_process
    with self.assertRaisesRegex(RuntimeError, 'File Cleaner not active'):
      service_checker.FileCleanerChecker.Run()

  @mock.patch.object(subprocess, 'Popen')
  def testRun_success(self, mock_popen):
    mock_process = mock.MagicMock()
    mock_process.communicate.return_value = ('multitest_transport.file_cleaner',
                                             'None')
    mock_popen.return_value = mock_process
    service_checker.FileCleanerChecker.Run()


class SQLDatabaseChecker(absltest.TestCase):

  def testRun_error(self):
    type(sql_models.db).engine = mock.PropertyMock(return_value=None)
    with self.assertRaisesRegex(RuntimeError, 'SQL Database not found'):
      service_checker.SQLDatabaseChecker.Run()

  def testRun_success(self):
    type(sql_models.db).engine = mock.PropertyMock(return_value=True)
    service_checker.SQLDatabaseChecker.Run()


class RabbitMQCheckerTest(absltest.TestCase):

  @mock.patch.object(requests, 'get')
  def testRun_error(self, mock_get):
    mock_get.side_effect = RuntimeError('Test error')
    with self.assertRaisesRegex(RuntimeError, 'Test error'):
      service_checker.RabbitMQChecker.Run()

  @mock.patch.object(requests, 'get')
  def testRun_success(self, mock_get):
    mock_response = mock.MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    service_checker.RabbitMQChecker.Run()

if __name__ == '__main__':
  absltest.main()
