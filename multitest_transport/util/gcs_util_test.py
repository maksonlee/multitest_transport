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

"""Unit tests for gcs_util."""

from absl.testing import absltest
import cloudstorage as gcs
import mock

from google.appengine.ext import testbed

from multitest_transport.util import env
from multitest_transport.util import file_util
from multitest_transport.util import gcs_util


class GcsUtilTest(absltest.TestCase):

  def setUp(self):
    super(GcsUtilTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.addCleanup(self.testbed.deactivate)

  def _CreateMockFiles(self, filenames):
    for filename in filenames:
      with gcs.open(filename, 'w') as fh:
        fh.write('dummy')

  def _AssertFilesExist(self, filenames):
    for filename in filenames:
      self.assertTrue(gcs_util.Exists(filename))

  def _AssertFilesNotExist(self, filenames):
    for filename in filenames:
      self.assertFalse(gcs_util.Exists(filename))

  def testGetDownloadUrl(self):
    env.BLOBSTORE_PATH = None  # Not running in standalone mode
    self.assertEqual('gs:/filename', gcs_util.GetDownloadUrl('filename'))

  def testGetDownloadUrl_local(self):
    # Running in standalone mode
    env.BLOBSTORE_PATH = 'blobstore'
    env.APPLICATION_ID = 'application'
    # File exists
    gcs_util.GCS_FILE_INFO = mock.Mock()
    blob = gcs_util.GCS_FILE_INFO.all().filter().get()
    blob.key().id_or_name.return_value = '_test'

    self.assertEqual('file://blobstore/application/t/test',
                     gcs_util.GetDownloadUrl('filename'))

  def testGetDownloadUrl_localRetry(self):
    # Running in standalone mode
    env.BLOBSTORE_PATH = 'blobstore'
    env.APPLICATION_ID = 'application'
    # File is found after retrying
    gcs_util.GCS_FILE_INFO = mock.Mock()
    blob = mock.Mock()
    gcs_util.GCS_FILE_INFO.all().filter().get.side_effect = [None, blob]
    blob.key().id_or_name.return_value = '_test'

    self.assertEqual('file://blobstore/application/t/test',
                     gcs_util.GetDownloadUrl('filename'))

  @mock.patch.object(file_util.FileHandle, 'Get')
  def testExists(self, mock_handler_factory):
    # running in standalone mode and 2nd file checked will exist
    env.BLOBSTORE_PATH = 'blobstore'
    mock_handler = mock.MagicMock()
    mock_handler_factory.return_value = mock_handler
    mock_handler.Info.side_effect = [None, file_util.FileInfo(1, 'type', None)]

    path = env.GCS_ROOT_PATH + '/foo'
    filenames = [
        path + '/bar.txt',
        path + '/zzz.txt',
    ]
    self._CreateMockFiles(filenames)

    self.assertFalse(gcs_util.Exists(path + 'unknown.txt'))  # not in GCS DB
    self.assertFalse(gcs_util.Exists(path + '/bar.txt'))  # in DB but not found
    self.assertTrue(gcs_util.Exists(path + '/zzz.txt'))  # in DB and found

  def testDeleteFiles(self):
    path = env.GCS_ROOT_PATH + '/foo'
    filenames = [
        path + '/bar.txt',
        path + '/zzz.txt'
    ]
    self._CreateMockFiles(filenames)
    self._AssertFilesExist(filenames)

    gcs_util.DeleteFiles(path)

    self._AssertFilesNotExist(filenames)

  def testDeleteFiles_withFilesToKeep(self):
    path = env.GCS_ROOT_PATH + '/foo'
    filenames = [
        path + '/bar.txt',
        path + '/zzz.txt'
    ]
    self._CreateMockFiles(filenames)

    gcs_util.DeleteFiles(path, files_to_keep=filenames[1:])

    self._AssertFilesNotExist(filenames[0:1])
    self._AssertFilesExist(filenames[1:])

if __name__ == '__main__':
  absltest.main()
