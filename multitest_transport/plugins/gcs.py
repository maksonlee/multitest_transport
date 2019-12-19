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

"""A MTT plugin for Google Cloud Storage."""
import datetime
import logging

import apiclient.discovery
import apiclient.errors
import apiclient.http
import httplib2
import six

from multitest_transport.plugins import base
from multitest_transport.plugins import constant
from multitest_transport.plugins import stream_uploader
from multitest_transport.util import env
from multitest_transport.util import file_util

_PATH_DELIMITER = '/'
_EMPTY_FOLDER_CONTENT_TYPE = 'application/x-www-form-urlencoded;charset=UTF-8'
_GCS_OAUTH2_SCOPES = ['https://www.googleapis.com/auth/devstorage.full_control']
_GCS_BUILD_API_NAME = 'storage'
_GCS_BUILD_API_VERSION = 'v1'
_PAGE_SIZE = 10
_UPLOAD_BUFFER_SIZE = 1024 * 1024


def _ParsePath(path):
  """Parses a path into a bucket name and an object name."""
  if not path:
    return '', ''
  parts = path.split(_PATH_DELIMITER, 1)
  bucket = parts[0] if parts[0] else None
  object_name = parts[1] if 1 < len(parts) else None
  return bucket, object_name


def _ParseTimeStamp(timestamp):
  """Parse a timestamp into a datetime.datetime object.

  Parse a timestamp from Cloud Storage JSON API into a datetime.datetime object

  Args:
    timestamp: Cloud Storage JSON API timestamp.
  Returns:
    a datetime.datetime object or None (if timestamp is None).
  """
  if timestamp is None:
    return None
  return datetime.datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ')


class GCSBucketNotFoundError(Exception):
  """A Google Cloud Storage Error indicating that bucket is not supplied."""


class GCSBuildProvider(base.BuildProvider):
  """A build channel.

  A Google Cloud Storage plugin that allows user to download Android builds and
  listing builds with pagination.
  """

  def __init__(self):
    super(GCSBuildProvider, self).__init__(
        url_patterns=[base.UrlPattern(r'gs://(?P<path>.*)', '{path}')])
    self._client = None

  def _GetClient(self):
    """Initialize client.

    Returns:
      a client which is a Google Api Client Resource object with methods
    for interacting with the service. Returns None if client has already been
    initialized
    """
    if self._client:
      return self._client

    http = httplib2.Http(timeout=constant.HTTP_TIMEOUT_SECONDS)
    credentials = self.GetCredentials()
    if credentials:
      http = credentials.authorize(http)
    self._client = apiclient.discovery.build(
        _GCS_BUILD_API_NAME,
        _GCS_BUILD_API_VERSION,
        http=http,
        developerKey=env.GOOGLE_API_KEY)
    return self._client

  def GetOAuth2Config(self):
    """Provide base with params needed for OAuth2 authentication."""
    return base.OAuth2Config(
        client_id=env.GOOGLE_OAUTH2_CLIENT_ID,
        client_secret=env.GOOGLE_OAUTH2_CLIENT_SECRET,
        scopes=_GCS_OAUTH2_SCOPES)

  def _GetGCSObject(self, bucket, object_name):
    """Get a Google Cloud Storage object from path.

    Args:
      bucket: a bucket name.
      object_name: an object name (e.g. path/to/object.zip).
    Returns:
      (a response object that contains attributes for the object requested)
    """
    client = self._GetClient()
    try:
      request = client.objects().get(bucket=bucket, object=object_name)
      return request.execute(num_retries=constant.NUM_RETRIES)
    except apiclient.errors.HttpError as e:
      if e.resp.status == 404:
        logging.info(e)
        return None
      raise

  def GetBuildItem(self, path=None):
    """Get a build item.

    Args:
      path: a path to file or directory, (e.g. path/to/file/kitten.png -> file
      path1/path2/ -> directory)

    Returns:
      a base.BuildItem object if response is valid, otherwise, return None
    """
    bucket, object_name = _ParsePath(path)
    # If an object name is not given, return a root directory.
    if not object_name:
      return base.BuildItem(name=None, is_file=False, path=path)
    response = self._GetGCSObject(bucket, object_name)
    if not response and not object_name.endswith(_PATH_DELIMITER):
      # Because directory passed in don't have a trailing slash, need
      # to try again with trailing slash to check if it's direcotry
      response = self._GetGCSObject(bucket, object_name + _PATH_DELIMITER)
    if not response:
      return None
    object_name = response['name']
    is_file = not object_name.endswith(_PATH_DELIMITER)
    # Parse an object name.
    if is_file:
      name = object_name.split(_PATH_DELIMITER)[-1]
    else:
      name = object_name[:-1].split(_PATH_DELIMITER)[-1] + _PATH_DELIMITER
    return base.BuildItem(
        name=name,
        path=_PATH_DELIMITER.join([bucket, response['name']]),
        is_file=is_file,
        size=long(response['size']),
        timestamp=_ParseTimeStamp(response['updated']))

  def _ListGCSObjects(self, bucket, prefix, page_token=None):
    """List Google Storage Objects from given path.

    Args:
      bucket: a bucket name.
      prefix: an object name prefix.
      page_token: an optional page token.
    Returns:
      (a response object containing information about the list of objects)
    Raises:
      GCSBucketNotFoundError
    """
    client = self._GetClient()
    try:
      return client.objects().list(
          bucket=bucket,
          delimiter=_PATH_DELIMITER,
          maxResults=_PAGE_SIZE,
          prefix=prefix,
          pageToken=page_token).execute(num_retries=constant.NUM_RETRIES)
    except apiclient.errors.HttpError as e:
      if e.resp.status == 404:
        raise GCSBucketNotFoundError('bucket %s does not exist' % bucket)

  def ListBuildItems(self, path, page_token=None, item_type=None):
    """List build items under a given path.

    Args:
      path: a build item path (e.g. bucket/git_master/taimen-userdebug).
      page_token: an optional page token.
      item_type: a type of build items to list. Returns all types if None.
    Returns:
      (a list of base.BuildItem objects, the next page token)
    """
    if path and not path.endswith(_PATH_DELIMITER):
      path = path + _PATH_DELIMITER
    bucket, object_name = _ParsePath(path)
    response = self._ListGCSObjects(bucket, object_name, page_token)
    build_items = []
    directory_prefixes = response.get('prefixes', [])
    items = response.get('items', [])
    prefix_len = len(object_name) if object_name else 0

    if not item_type or item_type == base.BuildItemType.FILE:
      for item in items:
        if item['contentType'] == _EMPTY_FOLDER_CONTENT_TYPE:
          continue
        build_items.append(
            base.BuildItem(
                name=item['name'][prefix_len:],
                path=_PATH_DELIMITER.join([bucket, item['name']]),
                is_file=True,
                size=long(item['size']),
                timestamp=_ParseTimeStamp(item['updated'])))
    if not item_type or item_type == base.BuildItemType.DIRECTORY:
      for directory_prefix in directory_prefixes:
        build_items.append(
            base.BuildItem(
                name=directory_prefix[prefix_len:],
                path=_PATH_DELIMITER.join([bucket, directory_prefix]),
                is_file=False,
                size=None,
                timestamp=None))
    next_page_token = response.get('nextPageToken')
    return (build_items, next_page_token)

  def _CreateMediaDownloader(self, bucket, object_name, fh, chunk_size, offset):
    """Create a media downloader."""
    client = self._GetClient()
    request = client.objects().get_media(bucket=bucket, object=object_name)
    downloader = apiclient.http.MediaIoBaseDownload(
        fh, request, chunksize=chunk_size)
    downloader._progress = offset      return downloader

  def DownloadFile(self, path, offset=0):
    """Download file from remote GCS.

    Args:
      path: a build item path (e.g. aa5/abc/bla/kitten.png)
      offset: byte offset to read from
    Yields:
      FileChunks (data read, current position, total file size)
    Raises:
      base.FileNotFoundError: if a path is invalid
    """
    build_item = self.GetBuildItem(path)
    if (build_item is None) or (not build_item.is_file):
      raise base.FileNotFoundError('Build item %s does not exist' % path)

    bucket, object_name = _ParsePath(path)
    buffer_ = six.StringIO()
    downloader = self._CreateMediaDownloader(
        bucket, object_name, buffer_, constant.DEFAULT_CHUNK_SIZE, offset)
    done = False
    while not done:
      status, done = downloader.next_chunk(num_retries=constant.NUM_RETRIES)
      yield file_util.FileChunk(
          data=buffer_.getvalue(),
          offset=status.resumable_progress,
          total_size=status.total_size)
      buffer_.truncate(0)

  def UploadFile(self, source_url, dst_file_path):
    """Upload content from source_url to dst_file_path.

    Args:
      source_url: a url which stores file content
      dst_file_path: a destination file path (e.g folder1/folder2/error.txt)
    """
    client = self._GetClient()

    file_info = file_util.GetFileInfo(source_url)
    total_size = file_info.total_size
    if not total_size:
      logging.info('File %s is empty', source_url)
      return

    media = stream_uploader.MediaUpload(
        url=source_url,
        total_size=total_size,
        mimetype=file_info.content_type,
        chunksize=_UPLOAD_BUFFER_SIZE,
        resumable=True)

    bucket, object_name = _ParsePath(dst_file_path)
    request = client.objects().insert(
        bucket=bucket,
        name=object_name,
        media_body=media)
    response = None
    while response is None:
      status, response = request.next_chunk(num_retries=constant.NUM_RETRIES)
      if status:
        status_str = 'Uploaded %d%%.' % int(status.progress() * 100)
        logging.debug(status_str)
    logging.debug('Upload %s Completed', dst_file_path)

base.RegisterBuildProviderClass('Google Cloud Storage', GCSBuildProvider)
