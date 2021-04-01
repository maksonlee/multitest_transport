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
from absl.testing import absltest
import mock
from tradefed_cluster.util import ndb_test_lib

from multitest_transport.core import service_checker
from multitest_transport.util import env
from multitest_transport.util import file_util


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


if __name__ == '__main__':
  absltest.main()
