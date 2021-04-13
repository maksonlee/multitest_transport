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
import logging

import google.auth
import google.auth.transport.requests
from google.cloud import secretmanager
import google.oauth2.credentials
import google.oauth2.service_account


logger = logging.getLogger(__name__)

GCS_READ_SCOPE = 'https://www.googleapis.com/auth/devstorage.read_only'
ANDROID_TEST_API_SCOPE = 'https://www.googleapis.com/auth/android-test.internal'

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
  response = client.access_secret_version(name)
  return response.payload.data
