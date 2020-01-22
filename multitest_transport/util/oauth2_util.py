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
import collections
from oauth2client import client
from six.moves import urllib

MANUAL_COPY_PASTE_URI = 'urn:ietf:wg:oauth:2.0:oob'

OAuth2Config = collections.namedtuple('OAuth2Config',
                                      ['client_id', 'client_secret', 'scopes'])


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
    oauth2client.client.OAuth2Flow
  """
  if not oauth2_config:
    raise ValueError('No OAuth2 configuration provided')
  return client.OAuth2WebServerFlow(
      client_id=oauth2_config.client_id,
      client_secret=oauth2_config.client_secret,
      scope=oauth2_config.scopes,
      redirect_uri=redirect_uri)
