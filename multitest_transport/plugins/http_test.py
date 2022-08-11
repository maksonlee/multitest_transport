# Copyright 2022 Google LLC
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
"""Unit tests for http plugins."""
from unittest import mock

from absl.testing import absltest
from multitest_transport.plugins import http
from multitest_transport.util import errors
from multitest_transport.util import file_util


class BasicAuthHttpProviderTest(absltest.TestCase):

  def setUp(self):
    super(BasicAuthHttpProviderTest, self).setUp()
    self.build_provider = http.BasicAuthHttpProvider()

  @mock.patch.object(file_util, 'HttpFileHandle')
  def testGetBuildItem(self, mock_http_file_handle):
    mock_handle = mock.MagicMock()
    mock_handle.Info.return_value = file_util.FileInfo(url='url')
    mock_http_file_handle.return_value = mock_handle

    build_item = self.build_provider.GetBuildItem('url')

    mock_http_file_handle.assert_called_once_with('url', url_opener=mock.ANY)
    self.assertEqual('url', build_item.name)  # Item name is url
    self.assertEqual('', build_item.path)  # Empty path

  @mock.patch.object(file_util, 'HttpFileHandle')
  def testGetBuildItem_notFound(self, mock_http_file_handle):
    mock_handle = mock.MagicMock()
    mock_handle.Info.return_value = None
    mock_http_file_handle.return_value = mock_handle

    with self.assertRaises(errors.FileNotFoundError):
      self.build_provider.GetBuildItem('url')

  @mock.patch.object(file_util, 'DownloadFile')
  def testDownloadFile(self, mock_download_file):
    self.build_provider.DownloadFile('url')

    mock_download_file.assert_called_once_with('url', url_opener=mock.ANY)


if __name__ == '__main__':
  absltest.main()
