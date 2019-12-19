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

"""Tests for google3.wireless.android.test_tools.mtt.plugins.strem_uploader."""

import urllib2
import mock
from absl.testing import absltest
from multitest_transport.plugins import stream_uploader


class StreamUploaderTest(absltest.TestCase):

  def setUp(self):
    self.media = stream_uploader.MediaUpload('sample_url', 100)

  def testSize(self):
    """Test size."""
    size = self.media.size()
    self.assertEqual(size, 100)

  def testHasStream(self):
    """Test has stream."""
    has_stream = self.media.has_stream()
    self.assertFalse(has_stream)

  @mock.patch.object(urllib2, 'urlopen', autospec=True)
  @mock.patch.object(urllib2, 'Request', autospec=True)
  def testGetBytes(self, mock_request, mock_urlopen):
    """Test get bytes."""
    mock_src = mock.MagicMock()
    mock_urlopen.return_value = mock_src
    mock_src.read.return_value = 'abcdefg'

    start = 0
    length = 7
    content = self.media.getbytes(start, length)
    mock_request.assert_called_with(
        'sample_url',
        headers={'Range': 'bytes=%s-%s' % (start, start + length - 1)})
    self.assertEqual(content, 'abcdefg')

  @mock.patch.object(urllib2, 'urlopen', autospec=True)
  @mock.patch.object(urllib2, 'Request', autospec=True)
  def testGetBytes_withLargeFiles(self, mock_request, mock_urlopen):
    """Test get bytes."""
    mock_src = mock.MagicMock()
    mock_urlopen.return_value = mock_src
    mock_src.read.side_effect = ['abcdefg', 'hijklmn']

    start = 0
    length = 7
    content = self.media.getbytes(start, length)
    mock_request.assert_called_with(
        'sample_url',
        headers={'Range': 'bytes=%s-%s' % (start, start + length - 1)})
    self.assertEqual(content, 'abcdefg')
    # second call
    start = start + length
    content = self.media.getbytes(start, length)
    mock_request.assert_called_with(
        'sample_url',
        headers={'Range': 'bytes=%s-%s' % (start, start + length - 1)})
    self.assertEqual(content, 'hijklmn')

if __name__ == '__main__':
  absltest.main()
