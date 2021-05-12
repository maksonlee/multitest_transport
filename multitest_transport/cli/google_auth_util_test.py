"""Tests for google_auth_util."""
import datetime
from absl.testing import absltest
import mock

from multitest_transport.cli import google_auth_util


class GoogleAuthUtilTest(absltest.TestCase):
  """Unit test for ssh util."""

  def _CreateMockVersionInfo(self, name, create_time, state):
    state_obj = mock.MagicMock()
    state_obj.name = state
    version = mock.MagicMock()
    version.name = name
    version.create_time = create_time
    version.state = state_obj
    return version

  @mock.patch.object(
      google_auth_util.secretmanager, 'SecretManagerServiceClient')
  def testDisableSecretVersions(self, mock_client_class):
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    before = now - datetime.timedelta(days=100)
    mock_client = mock.MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.secret_path.return_value = 'parent'
    mock_client.list_secret_versions.return_value = [
        self._CreateMockVersionInfo('version9', now, 'ENABLED'),
        self._CreateMockVersionInfo('version8', now, 'ENABLED'),
        self._CreateMockVersionInfo('version7', before, 'DISABLED'),
        self._CreateMockVersionInfo('version6', before, 'ENABLED'),
        self._CreateMockVersionInfo('version5', before, 'ENABLED'),
    ]

    google_auth_util.DisableSecretVersions(
        'aproject', 'asecret',
        exclude_versions=['version9', 'version5'],
        days_before=10,
        credentials=mock.MagicMock())

    mock_client.list_secret_versions.assert_called_once_with(
        {'parent': 'parent'})
    # Only disable old and non-excluded ones.
    mock_client.disable_secret_version.assert_called_once_with(
        {'name': 'version6'})


if __name__ == '__main__':
  absltest.main()
