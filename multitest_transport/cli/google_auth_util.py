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

"""Google credential helpers."""
import base64
import datetime
import json
import logging

import google.auth
import google.auth.transport.requests
from google.cloud import secretmanager
import google.oauth2.credentials
import google.oauth2.service_account
import googleapiclient.discovery


logger = logging.getLogger(__name__)

GCS_READ_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_only'
ANDROID_TEST_API_SCOPE = 'https://www.googleapis.com/auth/android-test.internal'
AUTH_SCOPE = 'https://www.googleapis.com/auth/cloud-platform'
_IAM_CREATE_SERVICE_ACCOUNT_KEY_PERMISSION = 'iam.serviceAccountKeys.create'
_SECRET_MANAGER_ADD_VERSION_PERMISSION = 'secretmanager.versions.add'
_PERMISSIONS_KEY = 'permissions'
_RESOURCE_KEY = 'resource'
_DEFAULT_DAYS_FOR_DISABLE_SECRET_VERSIONS = '30'
_VERSION_ENABLED = 'ENABLED'

LATEST_SECRET_VERSION = 'latest'


class AuthError(Exception):
  """Authentication error."""
  pass


def CreateCredentialFromServiceAccount(
    service_account_json_key_path, scopes=None):
  """Get credential from service account json key file.

  Args:
    service_account_json_key_path: service account key file.
    scopes: scopes for the credential.
  Returns:
    google.auth.credentials.Credentials object
  """
  credential = (google.oauth2.service_account.Credentials
                .from_service_account_file(
                    service_account_json_key_path))
  if scopes:
    credential = credential.with_scopes(scopes)
  credential.refresh(google.auth.transport.requests.Request())
  return credential


def GetGCloudCredential(command_context, scopes=None):
  """Get credential from command command_context.

  This comes from "gcloud auth login".
  TODO: should use oauth workflow to replace this.

  Args:
    command_context: a CommandContext object.
    scopes: scopes for the credential.
  Returns:
    google.auth.credentials.Credentials object
  """
  if not command_context.gcloud:
    logger.debug('No gcloud, can not get credential.')
    return None
  logger.debug('Get credential from gcloud auth print-access-token.')
  res = command_context.Run(
      [command_context.gcloud, 'auth', 'print-access-token'],
      raise_on_failure=False)
  if res.return_code != 0:
    logger.debug(
        'Fail to get user credentials with '
        '"gcloud auth print-access-token": %s.',
        res.stderr)
    return None
  credential = google.oauth2.credentials.Credentials(res.stdout.strip())
  if credential and scopes:
    credential = credential.with_scopes_if_required(credential, scopes)
  return credential


def GetDefaultCredential(scopes=None):
  """Get default credential on current host."""
  credential, _ = google.auth.default(scopes=scopes)
  if not credential:
    raise AuthError(
        'No default user credentials. Run "gcloud auth login".')
  return credential


def GetSecret(
    project_id, secret_id, credentials=None, version_id=LATEST_SECRET_VERSION):
  """Get secret from Google Cloud Secret Manager.

  Args:
    project_id: Google Cloud project id.
    secret_id: secret_id.
    credentials: credentials to access secret manager.
    version_id: version of the secret.
  Returns:
    a bytearray represent the secret.
  """
  logger.debug('Get secret %s(%s) from %s.', secret_id, version_id, project_id)
  credentials = credentials or GetDefaultCredential()
  client = secretmanager.SecretManagerServiceClient(credentials=credentials)
  name = client.secret_version_path(project_id, secret_id, version_id)
  response = client.access_secret_version(request={'name': name})
  return response.payload.data


def CanUpdateSecret(project_id, secret_id, credentials=None):
  """The credentials can update the secret.

  Args:
    project_id: Google Cloud project id.
    secret_id: secret_id.
    credentials: credentials to access secret manager.
  Returns:
    True if the credentials can update the secret, otherwise False.
  """
  credentials = credentials or GetDefaultCredential()
  client = secretmanager.SecretManagerServiceClient(credentials=credentials)
  res = client.test_iam_permissions({
      _RESOURCE_KEY: client.secret_path(project_id, secret_id),
      _PERMISSIONS_KEY: [_SECRET_MANAGER_ADD_VERSION_PERMISSION]
  })
  if _SECRET_MANAGER_ADD_VERSION_PERMISSION in (res.permissions or []):
    logger.debug('Can update secret %s %s.', project_id, secret_id)
    return True
  logger.debug('No permission to update secret %s %s.', project_id, secret_id)
  return False


def DisableSecretVersions(
    project_id, secret_id,
    exclude_versions=(),
    days_before=_DEFAULT_DAYS_FOR_DISABLE_SECRET_VERSIONS,
    credentials=None):
  """Disable old secret versions.

  Args:
    project_id: secret project id.
    secret_id: secret id.
    exclude_versions: do not disable these versions.
    days_before: only disable versions older than days.
    credentials: credentials to access secret manager.
  """
  credentials = credentials or GetDefaultCredential()
  before = (datetime.datetime.now(tz=datetime.timezone.utc) -
            datetime.timedelta(days=days_before)).timestamp()
  client = secretmanager.SecretManagerServiceClient(credentials=credentials)
  res = client.list_secret_versions(
      {'parent': client.secret_path(project_id, secret_id)})
  versions_to_disable = []
  for version in res:
    if version.state.name != _VERSION_ENABLED:
      logger.debug('Version %s is not ENABLED.', version.name)
      continue
    if version.name in exclude_versions:
      logger.debug('Version %s is excluded.', version.name)
      continue
    if version.create_time.timestamp() > before:
      logger.debug('Version %s is new.', version.name)
      continue
    versions_to_disable.append(version.name)
  for version in versions_to_disable:
    logger.debug('Disable %s.', version)
    client.disable_secret_version({'name': version})


def UpdateSecret(
    project_id, secret_id, content, credentials=None):
  """Update secret to Google Cloud Secret Manager.

  Args:
    project_id: Google Cloud project id.
    secret_id: secret_id.
    content: a bytearray secret content
    credentials: credentials to access secret manager.
  Returns:
    a bytearray represent the secret.
  """
  logger.info('Update secret %s in %s.', secret_id, project_id)
  credentials = credentials or GetDefaultCredential()
  client = secretmanager.SecretManagerServiceClient(credentials=credentials)
  name = client.secret_path(project_id, secret_id)
  version = client.add_secret_version(
      request={'parent': name, 'payload': {'data': content}}
  )
  logger.info('Create version %s for %s in %s.', version, secret_id, project_id)
  return version.name


def _BuildIAMAPIClient(credentials=None):
  """BUild API Client for Google Cloud IAM."""
  credentials = credentials or GetDefaultCredential(AUTH_SCOPE)
  return googleapiclient.discovery.build('iam', 'v1', credentials=credentials)


def GetServiceAccountKeyInfo(
    service_account_email, service_account_key_id, credentials=None):
  """Get service account key's information.

  Args:
    service_account_email: the key's service account email.
    service_account_key_id: the key's id.
    credentials: credentials used to access the API.
  Returns:
    a dict represent service account key information.
  """
  client = _BuildIAMAPIClient(credentials)
  key_info = client.projects().serviceAccounts().keys().get(
      name=(f'projects/-/serviceAccounts/{service_account_email}'
            f'/keys/{service_account_key_id}')
      ).execute()
  return key_info


def CanCreateKey(service_account_email, credentials=None):
  """Check if the credentials have the permission to create new key."""
  client = _BuildIAMAPIClient(credentials)
  res = client.projects().serviceAccounts().testIamPermissions(
      resource=f'projects/-/serviceAccounts/{service_account_email}',
      body={
          _PERMISSIONS_KEY: [_IAM_CREATE_SERVICE_ACCOUNT_KEY_PERMISSION]
      }).execute()
  if (_IAM_CREATE_SERVICE_ACCOUNT_KEY_PERMISSION in
      res.get(_PERMISSIONS_KEY, [])):
    logger.debug('Can create key for %s.', service_account_email)
    return True
  logger.debug('No permission to create key for %s.', service_account_email)
  return False


def CreateKey(service_account_email, credentials=None):
  """Creates a key for a service account.

  Args:
    service_account_email: service account's email.
    credentials: credentials to access service account key API.
  Returns:
    a json represents the service account key.
  """
  client = _BuildIAMAPIClient(credentials)
  key = client.projects().serviceAccounts().keys().create(
      name=f'projects/-/serviceAccounts/{service_account_email}', body={}
      ).execute()
  return json.loads(base64.urlsafe_b64decode(key['privateKeyData']))
