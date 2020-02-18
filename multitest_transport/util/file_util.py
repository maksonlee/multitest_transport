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

"""A util file that stores common function that involve file operation."""
import collections
import cStringIO
import datetime
import logging
import os
import urllib2
import xml.etree.cElementTree as ElementTree
import zipfile

import apiclient
import cloudstorage as gcs
from protorpc import messages

from multitest_transport.util import env

DOWNLOAD_BUFFER_SIZE = 16 * 1024 * 1024
UPLOAD_BUFFER_SIZE = 512 * 1024

FileInfo = collections.namedtuple('FileInfo',
                                  ['total_size', 'content_type', 'timestamp'])

FileChunk = collections.namedtuple(
    'FileChunk', ['data', 'offset', 'total_size'])

TestSuiteInfo = collections.namedtuple(
    'TestSuiteInfo',
    ['build_number', 'target_architecture', 'name', 'fullname', 'version'])

XtsTestResultSummary = collections.namedtuple(
    'XtsTestResultSummary',
    ['passed', 'failed', 'modules_total', 'modules_done'])


class FileStorage(messages.Enum):
  """File storage types."""
  LOCAL_CLOUD_STORAGE = 0  # Locally emulated GCS
  LOCAL_FILE_SYSTEM = 1  # Local Filesystem
  GOOGLE_CLOUD_STORAGE = 2  # Google Cloud Storage


class FileSegment(object):
  """Partial file content."""

  def __init__(self, offset, lines):
    self.offset = offset
    self.length = sum([len(line) for line in lines])
    self.lines = lines


class FileHandle(object):
  """Wrapper around a URL that can read file metadata/content.

  Ir can also serve as a file-like object.
  """

  _MAX_LINE_LENGTH = 1024

  def __init__(self, url):
    self.url = url
    self.cursor = 0
    self.size = -1

  @classmethod
  def Get(cls, url):
    """Factory method which creates the appropriate file handle.

    Args:
      url: file URL
    Returns:
      file handle
    """
    if url.startswith('gs://'):
      return GCSFileHandle(url)  # Google cloud storage URL
    if url.startswith('file://' + env.STORAGE_PATH):
      return BrowsepyFileHandle(url)  # Local file server URL
    return HttpFileHandle(url)  # Any other URL defaults to HTTP handling

  def Info(self):
    """Get file information if file exists.

    Returns:
      file info: size (number of bytes) and type
    """
    raise NotImplementedError

  def ReadBytes(self, offset=0, length=None):
    """Read bytes.

    Args:
      offset: starting position (defaults to start of file)
      length: number of bytes to read (defaults to rest of file)
    Returns:
      data
    """
    raise NotImplementedError

  def Read(self, offset=0, length=None, split_lines=True):
    """Read partial file content.

    Args:
      offset: starting position (defaults to start of file)
      length: number of bytes to read (defaults to rest of file)
      split_lines: whether or not to split lines to an array (default true)
    Returns:
      file segment containing content (string array if split_lines is true,
        single string otherwise) and metadata
    """
    data = self.ReadBytes(offset=offset, length=length)
    if not data:
      return None
    if split_lines:
      data = data.splitlines(True)
    return FileSegment(offset, data)

  def seek(self, offset, whence=os.SEEK_SET):      """Implements file.seek()."""
    if whence == os.SEEK_SET:
      self.cursor = offset
    elif whence == os.SEEK_CUR:
      self.cursor += offset
    elif whence == os.SEEK_END:
      if self.size < 0:
        self.size = self.Info().total_size
      self.cursor = self.size + offset
    else:
      raise ValueError('%s is not supported whence value' % whence)

  def tell(self):      """Implements file.tell()."""
    return self.cursor

  def read(self, size=-1):      """Implements file.read()."""
    if size < 0:
      size = None
    data = self.ReadBytes(offset=self.cursor, length=size)
    if data:
      self.cursor += len(data)
    return data

  def readline(self, size=-1):      """Implements file.readline()."""
    if size < 0:
      size = self._MAX_LINE_LENGTH
    data = self.ReadBytes(offset=self.cursor, length=size)
    if not data:
      return None
    line = data.splitlines()[0]
    self.cursor += len(line)
    # If there was a new line char, increase cursor by 1.
    if len(line) < len(data):
      self.cursor += 1
    return line

  def readlines(self, sizehint=-1):      """Implements file.readlines()."""
    if sizehint < 0:
      sizehint = None
    data = self.ReadBytes(offset=self.cursor, length=sizehint)
    lines = data.splitlines()
    self.cursor += len(data) + 1
    return lines

  def next(self):
    """Implements file.next()."""
    return self.readline()

  def __iter__(self):
    """Implements file.__iter__()."""
    yield self.next()


class HttpFileHandle(FileHandle):
  """Reads file metadata and content via HTTP requests."""

  def _Request(self, **kwargs):
    return urllib2.Request(self.url, **kwargs)

  def _Open(self, **kwargs):
    try:
      return urllib2.urlopen(self._Request(**kwargs))
    except urllib2.HTTPError as e:
      if e.code == 404:
        return None
      raise e

  def Info(self):
    f = self._Open()
    if f is None:
      return None
    total_size = int(f.info().get('content-length'))
    content_type = f.info().get('content-type')
    last_modified = f.info().get('last-modified')
    timestamp = datetime.datetime.strptime(
        last_modified, '%a, %d %b %Y %H:%M:%S GMT') if last_modified else None
    f.close()
    return FileInfo(
        total_size=total_size, content_type=content_type, timestamp=timestamp)

  def ReadBytes(self, offset=0, length=None):
    if length is None:
      headers = {'Range': 'bytes=%s-' % offset}
    else:
      headers = {'Range': 'bytes=%s-%s' % (offset, offset + length - 1)}

    f = self._Open(headers=headers)
    if f is None:
      return None
    data = f.read()
    f.close()
    return data


class BrowsepyFileHandle(HttpFileHandle):
  """Reads file metadata and content from a local Browsepy file server."""

  def __init__(self, url):
    super(BrowsepyFileHandle, self).__init__(url)
    self.file_path = url[len('file://' + env.STORAGE_PATH):]
    self.request_url = '%sopen%s' % (env.FILE_SERVER_URL, self.file_path)

  def _Request(self, **kwargs):
    return urllib2.Request(self.request_url, **kwargs)


class GCSFileHandle(FileHandle):
  """Reads file metadata and content from Google Cloud Storage."""

  def __init__(self, url):
    super(GCSFileHandle, self).__init__(url)
    self.file_path = url[4:]

  def Info(self):
    try:
      stat = gcs.stat(self.file_path)
    except gcs.errors.NotFoundError:
      return None
    timestamp = datetime.datetime.utcfromtimestamp(
        stat.st_ctime) if stat.st_ctime else None
    return FileInfo(
        total_size=stat.st_size,
        content_type=stat.content_type,
        timestamp=timestamp)

  def ReadBytes(self, offset=0, length=None):
    try:
      f = gcs.open(self.file_path, offset=offset)
    except gcs.errors.NotFoundError:
      return None
    content = f.read(size=length or -1)
    f.close()
    return content


def GetFileInfo(file_url):
  """Convenience method to create a file handle and fetch file metadata."""
  return FileHandle.Get(file_url).Info()


def GetStorageUrl(storage, file_path):
  """Get URL for a file, prefixed according to the storage type.

  Args:
    storage: storage type
    file_path: file path
  Returns:
    a URL for a given file.
  """
  if file_path is None:
    file_path = ''
  elif file_path.startswith('/'):
    file_path = file_path[1:]

  if storage in [FileStorage.LOCAL_CLOUD_STORAGE,
                 FileStorage.GOOGLE_CLOUD_STORAGE]:
    return 'gs://%s' % file_path
  elif storage == FileStorage.LOCAL_FILE_SYSTEM:
    return 'file://%s/%s' % (env.STORAGE_PATH, file_path)
  raise ValueError(storage)  # unknown storage type


def GetWorkFileUrl(attempt, file_path=None):
  """Get URL for a command attempt's work directory.

  Args:
    attempt: command attempt
    file_path: optional file path
  Returns:
    attempt's work directory URL
  """
  path = '/tmp/%s/%s' % (attempt.attempt_id, file_path or '')
  return GetStorageUrl(FileStorage.LOCAL_FILE_SYSTEM, path)


def GetOutputFileUrl(test_run, attempt, file_path=None):
  """Get URL for a command attempt's output file.

  Args:
    test_run: test run
    attempt: command attempt
    file_path: optional file path
  Returns:
    attempt's output URL
  """
  path = '%s%s/%s/%s' % (test_run.output_path,
                         attempt.command_id, attempt.attempt_id,
                         file_path or '')
  return GetStorageUrl(test_run.output_storage, path)


def GetOutputFilenames(test_run, attempt):
  """Get a list of output filenames for a completed attempt.

  Args:
    test_run: test run
    attempt: command attempt
  Returns:
    list of output filenames
  """
  summary_url = GetOutputFileUrl(test_run, attempt, 'FILES')
  return [line.strip() for line in FileHandle.Get(summary_url).readlines()]


def ReadFile(file_url, offset=0, length=None, split_lines=True):
  """Convenience method to create a file handle and read file content."""
  return FileHandle.Get(file_url).Read(offset, length, split_lines)


def TailFile(file_url, length):
  """Read content from end of file.

  Args:
    file_url: file URL
    length: number of bytes to read
  Returns:
    file segment containing lines of content and metadata
  """
  handle = FileHandle.Get(file_url)
  info = handle.Info()
  if info is None:
    return None
  total_size = info.total_size

  offset = max(0, total_size - length)
  return handle.Read(offset)


def DownloadFile(file_url, offset=0):
  """Download a file.

  Args:
    file_url: file URL
    offset: byte offset to read from
  Yields:
    file chunk (chunk of data read, current position, total size in bytes)
  Raises:
    RuntimeError: if file not found
  """
  handle = FileHandle.Get(file_url)
  info = handle.Info()
  if not info:
    raise RuntimeError('File %s not found' % file_url)
  total_size = info.total_size

  bufsize = DOWNLOAD_BUFFER_SIZE
  size = bufsize
  while bufsize <= size:
    # Read/write until EOF (downloaded size smaller than requested size)
    logging.debug('Downloading %s-%s', offset, offset + bufsize - 1)
    data = handle.ReadBytes(offset, bufsize)
    size = len(data)
    logging.debug('size: %d bytes', size)
    offset += size
    yield FileChunk(data=data, offset=offset, total_size=total_size)


def GetTestSuiteInfo(file_handle):
  """Get the test package information.

  Args:
    file_handle: A XTS zip file handle.
  Returns:
    package_info dictionary
  """
  try:
    zf = zipfile.ZipFile(file_handle)
    for file_name in zf.namelist():
      # Find a tradefed jar file inside the test package zip.
      if file_name.endswith('-tradefed.jar'):
        jar = zipfile.ZipFile(cStringIO.StringIO(zf.read(file_name)))
        jar_info = jar.NameToInfo.get('test-suite-info.properties')
        if not jar_info:
          continue  # Test suite information not found, skip.
        # Parse test suite information.
        suite_info = {}
        for line in jar.open(jar_info):
          if not line or line.startswith('#') or '=' not in line:
            continue
          key, value = line.split('=', 1)
          suite_info[key.strip()] = value.strip()
        return TestSuiteInfo(build_number=suite_info.get('build_number'),
                             target_architecture=suite_info.get('target_arch'),
                             name=suite_info.get('name'),
                             fullname=suite_info.get('fullname'),
                             version=suite_info.get('version'))
  except Exception as e:      logging.error('Failed to get test suite info: %s', e)
  return None


def GetXtsTestResultSummary(file_handle):
  """Get the test result summary. Assumes a CTS test_result.xml format.

  Args:
    file_handle: XTS XML test result file handle.
  Returns:
    test result summary dict.
  See Also:
    https://source.android.com/compatibility/cts/interpret
    https://android.googlesource.com/platform/test/suite_harness/+/1b95692/common/util/src/com/android/compatibility/common/util/ResultHandler.java
  """
  try:
    for _, elem in ElementTree.iterparse(file_handle):
      if elem.tag == 'Summary':
        return XtsTestResultSummary(
            passed=int(elem.attrib['pass']),
            failed=int(elem.attrib['failed']),
            modules_done=int(elem.attrib['modules_done']),
            modules_total=int(elem.attrib['modules_total']))
      elem.clear()
  except Exception as e:      logging.error('Failed to get test result summary: %s', e)
  return None


class FileHandleMediaUpload(apiclient.http.MediaIoBaseUpload):
  """MediaUpload which uploads a file handle without streaming."""

  def __init__(self, handle, chunksize=UPLOAD_BUFFER_SIZE, resumable=False):
    info = handle.Info()
    super(FileHandleMediaUpload, self).__init__(fd=handle,
                                                mimetype=info.content_type,
                                                chunksize=chunksize,
                                                resumable=resumable)

  def has_stream(self):
    # Disable streaming to issue a single request per chunk.
    return False
