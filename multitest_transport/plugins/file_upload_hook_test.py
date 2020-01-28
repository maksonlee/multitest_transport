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

"""Unit tests for file_upload_hook."""
from absl.testing import absltest
import mock

from google.appengine.ext import testbed

from multitest_transport.models import ndb_models
from multitest_transport.plugins import base as plugins
from multitest_transport.plugins import file_upload_hook
from multitest_transport.util import file_util


class AbstractFileUploadHookTest(absltest.TestCase):

  def setUp(self):
    super(AbstractFileUploadHookTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()

  def tearDown(self):
    self.testbed.deactivate()
    super(AbstractFileUploadHookTest, self).tearDown()

  def testInit_noFilePattern(self):
    """Tests that a file pattern is required."""
    with self.assertRaises(ValueError):
      file_upload_hook.AbstractFileUploadHook(file_pattern=None)

  @mock.patch.object(file_upload_hook.AbstractFileUploadHook, 'UploadFile')
  @mock.patch.object(file_util, 'GetOutputFileUrl')
  @mock.patch.object(file_util, 'GetOutputFilenames')
  def testExecute_filePattern(
      self, mock_get_filenames, mock_get_output_url, mock_upload_file):
    """Tests that only files matching the pattern are uploaded."""
    hook_context = plugins.TestRunHookContext(
        test_run=mock.MagicMock(), latest_attempt=mock.MagicMock(),
        phase=ndb_models.TestRunPhase.ON_SUCCESS)
    mock_get_filenames.return_value = ['hello.txt', 'world.xml']
    mock_get_output_url.side_effect = lambda tr, a, filename: filename
    # Hook will only upload XML files
    hook = file_upload_hook.AbstractFileUploadHook(file_pattern=r'.*\.xml')
    hook.Execute(hook_context)
    mock_upload_file.assert_called_once_with('world.xml', 'world.xml')

  @mock.patch.object(file_upload_hook.AbstractFileUploadHook, 'UploadFile')
  @mock.patch.object(file_util, 'GetOutputFileUrl')
  @mock.patch.object(file_util, 'GetOutputFilenames')
  def testExecute_uploadPrefix(
      self, mock_get_filenames, mock_get_output_url, mock_upload_file):
    """Tests that a prefix can be applied to the destination file path."""
    hook_context = plugins.TestRunHookContext(
        test_run=mock.MagicMock(), latest_attempt=mock.MagicMock(),
        phase=ndb_models.TestRunPhase.ON_SUCCESS)
    mock_get_filenames.return_value = ['hello.txt', 'world.xml']
    mock_get_output_url.side_effect = lambda tr, a, filename: filename
    # Hook will apply a dir/ prefix to all destinations
    hook = file_upload_hook.AbstractFileUploadHook(
        file_pattern='.*', upload_prefix='dir/')
    hook.Execute(hook_context)
    mock_upload_file.assert_has_calls([
        mock.call('hello.txt', 'dir/hello.txt'),
        mock.call('world.xml', 'dir/world.xml'),
    ])

  def testExecute_noAttempt(self):
    """Tests that an attempt is required during execution."""
    hook_context = plugins.TestRunHookContext(
        test_run=mock.MagicMock(), latest_attempt=None,
        phase=ndb_models.TestRunPhase.ON_SUCCESS)
    hook = file_upload_hook.AbstractFileUploadHook(file_pattern='.*')
    with self.assertRaises(ValueError):
      hook.Execute(hook_context)


if __name__ == '__main__':
  absltest.main()
