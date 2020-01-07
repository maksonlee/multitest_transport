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

"""A MTT plugin for Partner Android Build service."""

import json
import logging
import urllib2

from multitest_transport.plugins import base
from multitest_transport.util import env
from multitest_transport.util import file_util

OAUTH2_SCOPES = ('https://www.googleapis.com/auth/partnerdash',
                 'https://www.googleapis.com/auth/alkali-base')
API_BASE_URL = 'https://partnerdash.google.com/partnerdash/d/partnerandroidbuild'
DUMMY = 'DUMMY'


class PartnerAndroidBuildProvider(base.BuildProvider):
  """A build provider for Partner Android Build service."""
  name = 'Partner Android Build'

  def __init__(self):
    super(PartnerAndroidBuildProvider, self).__init__()
    self.AddOptionDef('account_id')

  def GetOAuth2Config(self):
    return base.OAuth2Config(
        client_id=env.GOOGLE_OAUTH2_CLIENT_ID,
        client_secret=env.GOOGLE_OAUTH2_CLIENT_SECRET,
        scopes=OAUTH2_SCOPES)

  def _CallAPI(self, method, branch, target, build_id=None, resource=None):
    """Call PAB API."""
    url_parts = [
        API_BASE_URL,
        'builds',
        method,
        branch,
        target,
        build_id or DUMMY,
        resource or DUMMY
    ]
    options = self.GetOptions()
    url = '/'.join(url_parts) + '?a=%s' % options.account_id
    headers = {}
    self.GetCredentials().apply(headers)
    logging.info('Fetching %s: headers=%s', url, headers)
    request = urllib2.Request(url, headers=headers)
    content = urllib2.urlopen(request).read()
    logging.info('Response: %s', content[:200])
    return json.loads(content)

  def ListBuildItems(self, path=None, page_token=None, item_type=None):
    """List build items under a given path.

    Args:
      path: a build item path (e.g. /git_master/taimen-userdebug).
      page_token: an optional page token.
      item_type: a type of build items to list. Returns all types if None.
    Returns:
      (a list of base.BuildItem objects, the next page token)
    Raises:
      ValueError: if a path is invalid.
    """
    parts = path.split('/') if path else []
    if not parts:
      # Branch listing is not supported.
      return [], None
    elif len(parts) == 1:
      # Target listing is not supported.
      return [], None
    elif len(parts) == 2:
      if item_type == base.BuildItemType.FILE:
        return [], None
      return self._ListBuilds(
          branch=parts[0], target=parts[1], page_token=page_token)
    elif len(parts) == 3:
      if item_type == base.BuildItemType.DIRECTORY:
        return [], None
      return self._ListBuildArtifacts(
          branch=parts[0], target=parts[1], build_id=parts[2],
          page_token=page_token)
    raise ValueError('invalid path: %s' % path)

  def GetBuildItem(self, path):
    """Returns a build item.

    Args:
      path: a build item path.
    Returns:
      a base.BuildItem object.
    """
    parts = path.split('/') if path else []
    if len(parts) == 3:
      return self._GetBuild(
          branch=parts[0], target=parts[1], build_id=parts[2])
    elif len(parts) == 4:
      return self._GetBuildArtifact(
          branch=parts[0], target=parts[1], build_id=parts[2], name=parts[3])
    raise ValueError('invalid path: %s' % path)

  def _ListBuilds(self, branch, target, page_token):
    """List builds as build items."""
    data = self._CallAPI('list', branch=branch, target=target)
    builds = data['build']
    build_items = []
    path_parts = [branch, target]
    for b in builds:
      if b['build_attempt_status'] != 'COMPLETE':
        continue
      name = str(b['build_id'])
      path = '/'.join(path_parts + [name])
      build_items.append(
          base.BuildItem(
              name=name, path=path, is_file=False, size=None, timestamp=None))
    return (build_items, None)

  def _GetBuild(self, branch, target, build_id):
    """Returns a build as a build item."""
    path = '/'.join([branch, target, build_id])
    return base.BuildItem(
        name=build_id, path=path, is_file=False, size=None, timestamp=None)

  def _ListBuildArtifacts(self, branch, target, build_id, page_token):
    """Lists build artifacts as build items."""
    data = self._CallAPI(
        'artifacts', branch=branch, target=target, build_id=build_id)
    artifacts = data['buildArtifacts']
    build_items = []
    path_parts = [branch, target, build_id]
    for artifact in artifacts:
      name = artifact['name']
      path = '/'.join(path_parts + [name])
      build_items.append(
          base.BuildItem(
              name=name, path=path, is_file=True, size=artifact['size']))
    return (build_items, None)

  def _GetBuildArtifact(self, branch, target, build_id, name):
    """Returns a build artifact as a build item."""
    # Check the existence of a build artifact.
    self._CallAPI(
        'get', branch=branch, target=target, build_id=build_id, resource=name)
    path = '/'.join([branch, target, build_id, name])
    return base.BuildItem(
        name=name, path=path, is_file=True, size=None, timestamp=None)

  def DownloadFile(self, path, offset=0):
    """Download a build file.

    Args:
      path: a build file path
      offset: byte offset to read from
    Returns:
      FileChunk generator (yields data, current position, total size in bytes)
    """
    parts = path.split('/')
    # A path should be in a form of "branch/target/build_id/artifact_name".
    if len(parts) != 4:
      raise ValueError('Invalid build file path: %s' % path)
    branch, target, build_id, name = parts
    data = self._CallAPI(
        'get', branch=branch, target=target, build_id=build_id, resource=name)
    return file_util.DownloadFile(data['url'], offset=offset)

  def UploadFile(self, source_url, dst_file_path):
    """Upload content from source_url to dst_file_path.

    Args:
      source_url: a url which stores file content
      dst_file_path: a file path (e.g folder1/folder2/error.txt)
    """

    raise NotImplementedError('UploadFile() is not implemented.')
