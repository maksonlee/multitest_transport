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

"""Tests for google3.wireless.android.test_tools.mtt.core.config_loader."""

import mock

from google.appengine.ext import testbed
from absl.testing import absltest

from multitest_transport.core import config_loader
from multitest_transport.util import file_util


class ConfigLoaderTest(absltest.TestCase):

  def setUp(self):
    super(ConfigLoaderTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.addCleanup(self.testbed.deactivate)

  @mock.patch.object(file_util, 'DownloadDirectory')
  def testReadAdditionalConfigs(self, mock_download):
    fake_tarfile = mock.MagicMock()
    fake_tarfile.read.return_value = 'content'

    fake_tar = mock.MagicMock()
    fake_tar.getnames.return_value = ['filename']
    fake_tar.extractfile.return_value = fake_tarfile
    mock_download.return_value = fake_tar

    file_contents = list(config_loader._ReadAdditionalConfigs())
    self.assertEqual(['content'], file_contents)

  @mock.patch.object(file_util, 'DownloadDirectory')
  def testReadAdditionalConfigs_fileNotFound(self, mock_download):
    fake_tar = mock.MagicMock()
    fake_tar.getnames.return_value = ['filename']
    fake_tar.extractfile.return_value = None
    mock_download.return_value = fake_tar

    file_contents = list(config_loader._ReadAdditionalConfigs())
    self.assertEqual([], file_contents)

  @mock.patch.object(file_util, 'DownloadDirectory')
  def testReadAdditionalConfigs_dirNotFound(self, mock_download):
    mock_download.return_value = None
    file_contents = list(config_loader._ReadAdditionalConfigs())
    self.assertEqual([], file_contents)

if __name__ == '__main__':
  absltest.main()
