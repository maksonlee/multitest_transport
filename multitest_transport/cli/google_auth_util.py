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
