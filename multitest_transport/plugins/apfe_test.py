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
"""Unit tests for APFE."""

from unittest import mock

from absl.testing import absltest

from multitest_transport.models import event_log
from multitest_transport.models import ndb_models
from multitest_transport.plugins import apfe
from multitest_transport.plugins import base as plugins
from multitest_transport.util import file_util


class APFEReportUploadHookTest(absltest.TestCase):

  def setUp(self):
    super(APFEReportUploadHookTest, self).setUp()
    # Initialize mock API client and hook under test
    self.client = mock.MagicMock()
    self.hook = apfe.APFEReportUploadHook(company_id='company_id')
    self.hook._client = self.client
    self.hook._authorized_http = mock.MagicMock()

  def testInit_noCompanyId(self):
    """Tests that a company id is required."""
    with self.assertRaises(ValueError):
      apfe.APFEReportUploadHook(company_id=None)

  @mock.patch.object(event_log, 'Warn')
  def testExecute_noContextParams(self, mock_warn):
    """Tests that results aren't uploaded if context parameters not set."""
    test_run = ndb_models.TestRun(test=ndb_models.Test())
    hook_context = plugins.TestRunHookContext(
        test_run=test_run,
        latest_attempt=mock.MagicMock(),
        phase=ndb_models.TestRunPhase.ON_SUCCESS)

    self.hook.Execute(hook_context)

    mock_warn.assert_called_once_with(
        test_run,
        '[APFE Report Upload] Context parameters not set, skipping upload.')
    self.client.compatibility().report().startUploadReport.assert_not_called()

  @mock.patch.object(event_log, 'Warn')
  @mock.patch.object(file_util, 'GetOutputFilenames')
  def testExecute_resultNotFound(self, mock_filenames, mock_warn):
    """Tests that results aren't uploaded if result file not found."""
    test_run = ndb_models.TestRun(
        test=ndb_models.Test(context_file_pattern='.+\\.zip'))
    hook_context = plugins.TestRunHookContext(
        test_run=test_run,
        latest_attempt=mock.MagicMock(),
        phase=ndb_models.TestRunPhase.ON_SUCCESS)
    mock_filenames.return_value = ['hello.txt', 'world.xml']

    self.hook.Execute(hook_context)

    mock_warn.assert_called_once_with(
        test_run,
        '[APFE Report Upload] Result file not found, skipping upload.')
    self.client.compatibility().report().startUploadReport.assert_not_called()

  @mock.patch.object(event_log, 'Warn')
  @mock.patch.object(file_util.FileHandle, 'Get')
  @mock.patch.object(file_util, 'GetOutputFileUrl')
  @mock.patch.object(file_util, 'GetOutputFilenames')
  def testExecute_resultNotZip(self, mock_filenames, mock_output_url,
                               mock_handle_factory, mock_warn):
    """Tests that results aren't uploaded if result file is not zip."""
    test_run = ndb_models.TestRun(
        test=ndb_models.Test(context_file_pattern='.+\\.txt'))
    hook_context = plugins.TestRunHookContext(
        test_run=test_run,
        latest_attempt=mock.MagicMock(),
        phase=ndb_models.TestRunPhase.ON_SUCCESS)
    mock_filenames.return_value = ['hello.txt', 'world.xml']
    mock_output_url.side_effect = lambda tr, a, filename: filename
    mock_handle_factory.return_value.Info.return_value = file_util.FileInfo(
        url='hello.txt', content_type='text/plain')

    self.hook.Execute(hook_context)

    mock_warn.assert_called_once_with(
        test_run,
        '[APFE Report Upload] Result file type is not zip, skipping upload.')
    self.client.compatibility().report().startUploadReport.assert_not_called()

  @mock.patch.object(event_log, 'Info')
  @mock.patch.object(file_util.FileHandle, 'Get')
  @mock.patch.object(file_util, 'GetOutputFileUrl')
  @mock.patch.object(file_util, 'GetOutputFilenames')
  def testExecute_success(self, mock_filenames, mock_output_url,
                          mock_handle_factory, mock_info):
    """Tests report can be uploaded successfully."""
    test_run = ndb_models.TestRun(
        test=ndb_models.Test(context_file_pattern='.+\\.zip'))
    hook_context = plugins.TestRunHookContext(
        test_run=test_run,
        latest_attempt=mock.MagicMock(),
        phase=ndb_models.TestRunPhase.ON_SUCCESS)
    mock_filenames.return_value = ['hello.txt', 'world.zip']
    mock_output_url.side_effect = lambda tr, a, filename: filename
    mock_handle_factory.return_value.Info.return_value = file_util.FileInfo(
        url='world.zip', content_type='application/zip')
    self.client.compatibility().report().startUploadReport(
    ).execute.return_value = b"""
      {
        "ref" : {
          "name" : "resource_name"
        }
      }
    """

    self.hook.Execute(hook_context)

    self.client.compatibility().report().startUploadReport.assert_called()
    self.client.media().upload.assert_called_once_with(
        resourceName='resource_name', media_body=mock.ANY)
    self.client.compatibility().report().create.assert_called_once_with(body={
        'reportRef': {
            'name': 'resource_name',
        },
        'companyId': 'company_id',
    })
    mock_info.assert_called_once_with(
        test_run, '[APFE Report Upload] Uploaded world.zip.')


if __name__ == '__main__':
  absltest.main()
