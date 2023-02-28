# Copyright 2021 Google LLC
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

"""Tests for control_server_util."""
import datetime
from unittest import mock

from absl.testing import absltest
import apiclient.errors


from multitest_transport.cli import control_server_util


class ControlServerUtilTest(absltest.TestCase):

  def setUp(self):
    super(ControlServerUtilTest, self).setUp()
    self.mock_build_discovery_client = mock.MagicMock()
    self.apiclient_discovery_build_patcher = mock.patch.object(
        control_server_util.apiclient.discovery, 'build_from_document',
        return_value=self.mock_build_discovery_client)
    self.apiclient_discovery_build_patcher.start()
    self.apiclient_discovery_doc_patcher = mock.patch.object(
        control_server_util.apiclient.discovery, '_retrieve_discovery_doc')
    self.apiclient_discovery_doc_patcher.start()

  def tearDown(self):
    self.apiclient_discovery_build_patcher.stop()
    self.apiclient_discovery_doc_patcher.stop()
    super(ControlServerUtilTest, self).tearDown()

  @mock.patch.object(control_server_util.google_auth_util,
                     'CreateCredentialFromServiceAccount')
  def testSubmitHostUpdateStateChangedEvent_NoEngprodApiClient(
      self, mock_creds):
    host_update_state = 'FAKE_EVENT'
    hostname = 'host1'
    control_server_client = control_server_util.ControlServerClient(
        None, None, None)
    control_server_client.SubmitHostUpdateStateChangedEvent(
        hostname, host_update_state)

    (self
     .mock_build_discovery_client()
     .test().hostEvents().submit().execute.assert_not_called())
    mock_creds.assert_not_called()

  @mock.patch.object(control_server_util.google_auth_util,
                     'CreateCredentialFromServiceAccount')
  @mock.patch.object(control_server_util.datetime, 'datetime')
  def testSubmitHostUpdateStateChangedEvent_SubmitIsSucceessful(
      self, mock_datetime, mock_creds):
    host_update_state = 'FAKE_EVENT'
    hostname = 'host1'
    display_message = 'some message'
    target_image = 'repo:tag'
    fake_now = datetime.datetime(2020, 1, 2)
    mock_datetime.utcnow.return_value = fake_now
    expected_event_body = {
        'host_events': [
            {
                'time': int(fake_now.timestamp()),
                'event_type': 'HOST_UPDATE_STATE_CHANGED',
                'host_update_state': host_update_state,
                'hostname': hostname,
                'host_update_state_display_message': display_message,
                'data': {
                    'host_update_target_image': target_image,
                },
            },
        ]
    }
    control_server_client = control_server_util.ControlServerClient(
        'url1', 'key.json', 'fakeApiKey')
    control_server_client.SubmitHostUpdateStateChangedEvent(
        hostname, host_update_state, display_message, target_image)

    (self.mock_build_discovery_client
     .test().hostEvents().submit
     .assert_called_once_with(body=expected_event_body))
    (self.mock_build_discovery_client
     .test().hostEvents().submit().execute.assert_called_once())
    mock_creds.assert_called_once_with(
        'key.json',
        scopes=['https://www.googleapis.com/auth/android-test.internal'])

  @mock.patch.object(control_server_util.google_auth_util,
                     'CreateCredentialFromServiceAccount')
  @mock.patch.object(control_server_util.datetime, 'datetime')
  def testSubmitHostUpdateStateChangedEvent_SubmitSwallowHttpError(
      self, mock_datetime, unused_mock_creds):
    host_update_state = 'FAKE_EVENT'
    hostname = 'host1'
    fake_now = datetime.datetime(2020, 1, 2)
    mock_datetime.utcnow.return_value = fake_now

    self.mock_build_discovery_client.test().hostEvents().submit.side_effect = (
        apiclient.errors.HttpError(mock.MagicMock(), 'error_content'))

    control_server_client = control_server_util.ControlServerClient(
        'url1', 'key.json', 'fakeApiKey')
    control_server_client.SubmitHostUpdateStateChangedEvent(
        hostname, host_update_state)

  @mock.patch.object(control_server_util.google_auth_util,
                     'CreateCredentialFromServiceAccount')
  def testGetHostMetadata(
      self, unused_mock_creds):
    hostname = 'host1'
    expected_metadata = {
        'hostname': hostname,
        'test_harness_image': 'image',
    }
    self.mock_build_discovery_client.test().hosts().getMetadata(
        ).execute.return_value = expected_metadata

    control_server_client = control_server_util.ControlServerClient(
        'url1', 'key.json', 'fakeApiKey')
    metadata_response = control_server_client.GetHostMetadata(hostname)

    self.assertEqual(expected_metadata, metadata_response)

  @mock.patch.object(control_server_util.google_auth_util,
                     'CreateCredentialFromServiceAccount')
  def testPatchTestHarnessImageToHostMetadata(
      self, unused_mock_creds):
    hostname = 'host1'
    test_harness_image = 'image_1'

    control_server_client = control_server_util.ControlServerClient(
        'url1', 'key.json', 'fakeApiKey')
    control_server_client.PatchTestHarnessImageToHostMetadata(
        hostname, test_harness_image)
    self.mock_build_discovery_client.test().hosts(
        ).patchMetadata.assert_called_once_with(
            hostname=hostname,
            body={'test_harness_image': test_harness_image})


if __name__ == '__main__':
  absltest.main()
