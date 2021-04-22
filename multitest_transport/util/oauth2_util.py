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

"""OAuth2 utilities."""
import json
import logging
import pickle

import attr
import google_auth_httplib2
from google_auth_oauthlib import flow
from six.moves import urllib
from tradefed_cluster.util import ndb_shim as ndb
from google.auth import credentials as ga_credentials
from google.oauth2 import credentials as authorized_user

MANUAL_COPY_PASTE_URI = 'urn:ietf:wg:oauth:2.0:oob'
GOOGLE_AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'


class CredentialsProperty(ndb.BlobProperty):
  """Stores authorized user or service account credentials."""

  def _validate(self, value):
    if value is not None and not isinstance(value, ga_credentials.Credentials):
      raise TypeError('Value %s is not a Credentials instance.' % value)

  def _to_base_type(self, value):
    # Using protocol 2 to ensure compatibility with Python 2.
    return pickle.dumps(value, protocol=2)

  def _from_base_type(self, value):
    try:
      # Use UTF-8 encoding for backwards compatibility with Python 2
      credentials = pickle.loads(value, encoding='utf-8')
      # Patch missing fields from older credentials objects (b/176850961)
      if not hasattr(credentials, '_quota_project_id'):
        setattr(credentials, '_quota_project_id', None)
      return credentials
    except (KeyError, pickle.PickleError):
      logging.warning('Unpickling credentials failed, reverting to JSON')
    # Try to parse JSON blob for backwards compatibility with oauth2client
    try:
      data = json.loads(value)
      return authorized_user.Credentials.from_authorized_user_info(data)
    except ValueError:
      return None


@attr.s(frozen=True)
class OAuth2Config(object):
  """OAuth2 configuration."""
  client_id = attr.ib()
  client_secret = attr.ib()
  scopes = attr.ib(factory=list)
  auth_uri = attr.ib(default=GOOGLE_AUTH_URI)
  token_uri = attr.ib(default=GOOGLE_TOKEN_URI)

  @property
  def is_valid(self):
    return all([self.client_id, self.client_secret, self.scopes])


def ApplyHeader(headers, credentials, scopes=None):
  """Helper function to apply credentials to request headers."""
  if not credentials:
    return  # TODO: try to use default credentials
  if scopes:
    credentials = ga_credentials.with_scopes_if_required(credentials, scopes)
  credentials.apply(headers)


def AuthorizeHttp(http, credentials, scopes=None):
  """Helper function to apply credentials to an HTTP client."""
  if not credentials:
    return http  # TODO: try to use default credentials
  if scopes:
    credentials = ga_credentials.with_scopes_if_required(credentials, scopes)
  return google_auth_httplib2.AuthorizedHttp(credentials, http)


def GetRedirectUri(redirect_uri):
  """Verifies a redirect URI, returning the actual URI to use.

  Args:
    redirect_uri: base redirect URI, e.g. http://127.0.0.1:8000/auth_return

  Returns:
    redirect_uri: actual redirect URI to use
    is_manual: whether the manual copy/paste flow should be used
  """
  hostname = urllib.parse.urlparse(redirect_uri).hostname
  if hostname not in ('127.0.0.1', 'localhost'):
    return MANUAL_COPY_PASTE_URI, True
  return redirect_uri, False


def GetOAuth2Flow(oauth2_config, redirect_uri):
  """Constructs a OAuth2 flow used to generate URLs and exchange codes.

  Args:
    oauth2_config: OAuth2 configuration (client details and scopes)
    redirect_uri: URI to redirect to after authorization

  Returns:
    google_auth_oauthlib.flow.Flow
  """
  if not oauth2_config:
    raise ValueError('No OAuth2 configuration provided')
  return flow.Flow.from_client_config(
      {
          'web': {
              'auth_uri': oauth2_config.auth_uri,
              'client_id': oauth2_config.client_id,
              'client_secret': oauth2_config.client_secret,
              'token_uri': oauth2_config.token_uri,
          },
      },
      scopes=oauth2_config.scopes,
      redirect_uri=redirect_uri)
