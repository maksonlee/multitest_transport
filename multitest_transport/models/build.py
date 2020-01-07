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

"""A module that defines build channel classes."""

import fnmatch
import logging
import os
import re
import urllib
import uuid

from oauth2client import appengine
from oauth2client import client

from multitest_transport import plugins
from multitest_transport.models import ndb_models
from multitest_transport.util import env
from multitest_transport.util import errors
from multitest_transport.plugins import base

BuildItem = plugins.BuildItem  BuildItemType = plugins.BuildItemType  UrlPattern = plugins.UrlPattern  

WILDCARD_CHARS = '*?'


class Error(Exception):
  pass


class NoBuildError(Error):
  pass


class BuildLocator(object):
  """A utility class which parses an encoded url."""

  def __init__(self, build_channel_id, directory, filename, path):
    self._build_channel_id = build_channel_id
    self._directory = directory
    self._filename = filename
    self._path = path

  @classmethod
  def ParseUrl(cls, url):
    """Parse an encoded url.

    Args:
      url: an encoded url.

    Returns:
      A BuildLocator or None if url not start with mtt:///
    """
    if not url:
      return None
    m = re.match(r'mtt:///([^/]*)/(.*)', url)
    if not m:
      return None

    directory = None
    filename = None
    build_channel_id = m.group(1)
    path = m.group(2)

    idx = path.rfind('/')
    if idx == -1:
      # Only filename remain
      filename = urllib.unquote(path.encode('utf-8')).decode('utf-8')
      path = filename
    else:
      directory = path[:idx]
      filename = urllib.unquote(path[idx + 1:].encode('utf-8')).decode('utf-8')
      path = os.path.join(directory, filename)
    return BuildLocator(build_channel_id, directory, filename, path)

  @property
  def build_channel_id(self):
    return self._build_channel_id

  @property
  def directory(self):
    """Get the directory within an MTT url.

    e.g. mtt:///local_file_store/a/b/c.txt, directory will be a/b
    e.g. mtt:///local_file_store/c.txt, directory will be None
    Returns:
      directory: an mtt url directory
    """
    return self._directory

  @property
  def filename(self):
    """Filename will be decoded filename.

    Returns:
      filename: a filename
    """
    return self._filename

  @property
  def path(self):
    """Get the concatenation of directory and filename.

    e.g. mtt:///local_file_store/a/b/c.txt, path will be a/b/c.txt
    e.g. mtt:///local_file_store/a.txt, path will be a.txt
    Returns:
      path: an mtt url path
    """
    return self._path


def GetBuildProviderClass(name):
  """Returns a build provider class.

  Args:
    name: a build provider name.
  Returns:
    a plugins.BuildProvider class.
  """
  return plugins.GetBuildProviderClass(name)


def ListBuildProviderNames():
  """Returns a list of names of registered build providers.

  Returns:
    a list of build provider names.
  """
  return plugins.ListBuildProviderNames()


class BuildChannel(object):
  """A class representing a build channel."""

  def __init__(self, config):
    self.id = config.key.id()
    self.config = config
    self.auth_state = ndb_models.BuildChannelAuthState.NOT_AUTHORIZED
    self.provider = GetBuildProviderClass(config.provider_name)()
    self.provider.UpdateOptions(
        **ndb_models.NameValuePair.ToDict(self.config.options))
    self.provider.UpdateCredentials(self._LoadCredentials())
    self.oauth2_config = self.provider.GetOAuth2Config()

  def _LoadCredentials(self):
    """Loads credentials from Datastore.

    Returns:
      a oauth2client.client.Credentials object.
    """
    storage = appengine.StorageByKeyName(
        ndb_models.BuildChannelConfig, self.id, 'credentials')
    credentials = storage.get()
    if credentials:
      self.auth_state = ndb_models.BuildChannelAuthState.AUTHORIZED
    return credentials

  def _StoreCredentials(self, credentials):
    """Stores credentials to Datastore.

    Args:
      credentials: a oauth2client.client.Credentials object.
    """
    storage = appengine.StorageByKeyName(
        ndb_models.BuildChannelConfig, self.id, 'credentials')
    storage.put(credentials)
    if credentials:
      self.auth_state = ndb_models.BuildChannelAuthState.AUTHORIZED
    else:
      self.auth_state = ndb_models.BuildChannelAuthState.NOT_AUTHORIZED

  def ListBuildItems(self, path=None, page_token=None, item_type=None):
    """List build items.

    Args:
      path: a path within a build channel.
      page_token: an optional token for paging.
      item_type: a type of build items to list. Returns all types if None.
    Returns:
      (a list of base.BuildItem objects, a next page token)
    """
    return self.provider.ListBuildItems(
        path=path, page_token=page_token, item_type=item_type)

  def GetBuildItem(self, path):
    """Get a build item.

    Args:
      path: a build item path.
    Returns:
      a base.BuildItem object.
    """
    return self.provider.GetBuildItem(path)

  def DeleteBuildItem(self, path):
    """Delete a build item.

    Args:
      path: a build item path.
    """
    self.provider.DeleteBuildItem(path)

  def DownloadFile(self, path, offset=0):
    """Download a build file.

    Args:
      path: a build file path
      offset: byte offset to read from
    Returns:
      FileChunk generator (yields data, current position, total file size)
    """
    return self.provider.DownloadFile(path, offset=offset)

  def UploadFile(self, source_url, dst_file_path):
    """Upload content from source_url to dst_file_path.

    Args:
      source_url: a url which stores file content
      dst_file_path: a destination file path (e.g folder1/folder2/error.txt)
    """
    self.provider.UploadFile(source_url, dst_file_path)

  def Update(self, name, provider_name, options):
    """Updates a build channel.

    Args:
      name: a build channel name.
      provider_name: a build provider name.
      options: a option dict.
    Returns:
      an updated ndb_models.BuildChannelConfig object.
    """
    provider = GetBuildProviderClass(provider_name)()
    provider.UpdateOptions(**options)
    self.config.name = name
    self.config.provider_name = provider_name
    self.config.options = ndb_models.NameValuePair.FromDict(options)
    self.config.put()
    self.provider = provider
    return self.config

  def _GetOAuth2Flow(self, redirect_uri):
    """Returns OAuth2 flow.

    Args:
      redirect_uri: a URI to redirect after authorization is done.
    Returns:
      an oauth2client.client.OAuth2Flow object.
    Raises:
      RuntimeError: if a provider does not use OAuth2.
    """
    oauth2_config = self.provider.GetOAuth2Config()
    if not oauth2_config:
      raise RuntimeError('no oauth2 config for provider %s' % self.provider)
    if not hasattr(self, '_flow'):
      # TODO: Use self.config.oauth2_config
      self._flow = client.OAuth2WebServerFlow(
          client_id=oauth2_config.client_id,
          client_secret=oauth2_config.client_secret,
          scope=oauth2_config.scopes,
          redirect_uri=redirect_uri)
    return self._flow

  def GetAuthorizeUrl(self, redirect_uri):
    flow = self._GetOAuth2Flow(redirect_uri)
    return flow.step1_get_authorize_url()

  def Authorize(self, redirect_uri, code):
    flow = self._GetOAuth2Flow(redirect_uri)
    credentials = flow.step2_exchange(code)
    self._StoreCredentials(credentials)

  def FindBuildItemPath(self, url):
    return self.provider.FindBuildItemPath(url)

  @property
  def name(self):
    return self.config.name

  @property
  def provider_name(self):
    return self.config.provider_name

  @property
  def options(self):
    return self.config.options

  @property
  def url_patterns(self):
    """File URL patterns."""
    return self.provider.url_patterns


def AddBuildChannel(name, provider_name, options):
  """Adds a new build channel.

  Args:
    name: a build channel name.
    provider_name: a build provider name.
    options: a option dict.
  Returns:
    a newly created ndb_models.BuildChannelConfig object.
  """
  provider = GetBuildProviderClass(provider_name)()
  # Validate options.
  provider.UpdateOptions(**options)
  new_config = ndb_models.BuildChannelConfig(
      id=str(uuid.uuid4()),
      name=name,
      provider_name=provider_name,
      options=ndb_models.NameValuePair.FromDict(options))
  new_config.put()
  return new_config


def GetBuildChannel(build_channel_id):
  """Returns a build channel.

  Args:
    build_channel_id: a build channel id.
  Returns:
    BuildChannel or None if not found.
  """
  config = ndb_models.BuildChannelConfig.get_by_id(build_channel_id)
  if config is None:
    return None
  return BuildChannel(config)


def ListBuildChannelConfigs():
  """Lists all build channel configs.

  Returns:
    a list of ndb_models.BuildChannelConfig objects.
  """
  return ndb_models.BuildChannelConfig.query().fetch()


def ListBuildChannels():
  """Lists all build channels.

  Returns:
    a list of ndb_models.BuildChannelConfig objects.
  """
  return [
      BuildChannel(config)
      for config in ndb_models.BuildChannelConfig.query().fetch()
  ]


def FindBuildChannel(url):
  """Find a build channel for a given URL.

  Args:
    url: a URL.
  Returns:
    (a build channel, a build item path)
  Raises:
    ValueError: if a build channel ID is not found.
  """
  # Don't map local GCS path to any build channels.
  if url.startswith('gs://' + env.GCS_BUCKET_NAME):
    return None, None

  build_locator = BuildLocator.ParseUrl(url)

  if build_locator:
    config = ndb_models.BuildChannelConfig.get_by_id(
        build_locator.build_channel_id)
    if not config:
      raise ValueError('Cannot find build channel: id=%s' %
                       build_locator.build_channel_id)
    return BuildChannel(config), build_locator.path

  for config in ndb_models.BuildChannelConfig.query().fetch():
    build_channel = BuildChannel(config)
    path = build_channel.FindBuildItemPath(url)
    if path:
      return build_channel, path
  return None, None


def BuildUrl(build_channel_id, build_item):
  """Build a encoded url.

  (e.g. if channel id is local_file_store, has a build item a/b c.txt,
  it will convert it to mtt:///local_file_store/a%2Fb%20c.txt)

  Args:
    build_channel_id: a build channel id
    build_item: a build item

  Returns:
    An encode url
  """
  path = build_item.path[:-len(build_item.name)]
  filename = build_item.name
  if not filename:
    return 'mtt:///%s/%s' % (build_channel_id, path)
  encoded_filename = urllib.quote(filename.encode('utf-8'), safe='')
  if not path:
    return 'mtt:///%s/%s' % (build_channel_id, encoded_filename)
  else:
    return 'mtt:///%s/%s' % (build_channel_id,
                             os.path.join(path, encoded_filename))


def FindTestResources(test_resource_pipes):
  """Convert TestResourcePipes to TestResourceObjs (may contains wildcard).

  Args:
    test_resource_pipes: a list of TestResourcePipe

  Returns:
    test_resource_objs: a list of TestResourceObj
  Raises:
    NoBuildError: if a test resource pipe's url is invalid
    TestResourceError: if a test resource pipe url is missing
  """
  # Convert test resource pipes (may contain wildcards) into test resources
  test_resource_map = {}
  for pipe in test_resource_pipes:
    build_locator = BuildLocator.ParseUrl(pipe.url)
    if build_locator:
      build_item = FindFile(build_locator.build_channel_id,
                            build_locator.directory, build_locator.filename)
      if not build_item:
        raise NoBuildError('Cannot find build from %s' % pipe.url)
      # Build a encoded url
      url = BuildUrl(build_locator.build_channel_id, build_item)
    else:
      url = pipe.url
    test_resource_map[pipe.name] = ndb_models.TestResourceObj(
        name=pipe.name, url=url, test_resource_type=pipe.test_resource_type)
  test_resource_objs = sorted(test_resource_map.values(), key=lambda x: x.name)
  for r in test_resource_objs:
    logging.info('\t%s: %s', r.name, r.cache_url)
    if not r.url:
      raise errors.TestResourceError('No URL for test resource %s' % r.name)
  return test_resource_objs


def FindFile(build_channel_id, path, filename=None):
  """Finds a file build item under a given path recursively.

  Args:
    build_channel_id: a build channel ID.
    path: a build item path.
    filename: a filename. Can containd wildcard characters (*?).

  Returns:
    a plugins.BuildItem object.
  """
  build_channel = GetBuildChannel(build_channel_id)
  if path:
    build_item = build_channel.GetBuildItem(path)
  else:
    # Path can be none when file are at first level into the build channel
    # e.g. mtt:///google_drive/file.txt, in this case google_drive in the
    # id, and file.txt is filename, but path is none.
    build_item = base.BuildItem(name=None, path=None, is_file=False)
  if not filename:
    return build_item

  # If a given path is for a director and a filename is given, recursively
  # search the first file that matches.
  while build_item and not build_item.is_file:
    next_build_item = None
    # If filename has wildcard characters
    if any([c in filename for c in WILDCARD_CHARS]):
      for child_item in _BuildItemIterator(
          build_channel, build_item.path, item_type=BuildItemType.FILE):
        if child_item.is_file and fnmatch.fnmatch(child_item.name, filename):
          next_build_item = child_item
          break
    else:
      child_item = build_channel.GetBuildItem(
          os.path.join(build_item.path or '', filename))
      if child_item and child_item.is_file:
        next_build_item = child_item
    if not next_build_item:
      # We assume the first build item returned is the latest one.
      for child_item in _BuildItemIterator(
          build_channel,
          build_item.path,
          item_type=BuildItemType.DIRECTORY):
        next_build_item = child_item
        break
    build_item = next_build_item
  return build_item


def _BuildItemIterator(build_channel, path, item_type=None):
  """An iterator to list all build items under a given path.

  Args:
    build_channel: a build.BuildChannel object.
    path: a build item path.
    item_type: a build item type.
  Yields:
    plugins.BuildItem objects.
  """
  page_token = None
  while True:
    items, page_token = build_channel.ListBuildItems(
        path, page_token=page_token, item_type=item_type)
    for item in items:
      if (item_type and
          (item.is_file and item_type != BuildItemType.FILE) or
          (not item.is_file and item_type == BuildItemType.FILE)):
        logging.warn(
            'An item does not match an item type filter: item=%s, item_type=%s',
            item, item_type)
        continue
      yield item
    if not page_token:
      break
