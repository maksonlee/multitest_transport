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

"""Utils for operating files."""
import base64
import datetime
import hashlib
import logging
import os
import re
import six


logger = logging.getLogger(__name__)


try:
  from google.cloud import exceptions as cloud_exceptions
  from google.cloud import storage
except ImportError as e:
  storage = None
  logger.warning('Failed to import google cloud storage.')


class GCSError(Exception):
  """Google cloud storage exception."""


def CreateGCSClient(project, credential):
  """Create Google Cloud Storage client.

  Args:
    project: project of the GCS client.
    credential: credential to access GCS bucket.
  Returns:
    storage.Client object
  Raises:
    GCSError: no storage package.
  """
  if not storage:
    raise GCSError('No Google Cloud Storage package.')
  return storage.Client(project=project, credentials=credential)


def GetGCSBlob(storage_client, file_uri):
  """Get GCS blob for a given uri."""
  bucket_name, remote_path = ParseGCSPath(file_uri)
  try:
    bucket = storage_client.get_bucket(bucket_name)
  except cloud_exceptions.NotFound:
    raise GCSError('%s doesn\'t exist.' % bucket_name)
  except cloud_exceptions.Forbidden:
    raise GCSError('No access to %s.' % bucket_name)
  blob = bucket.get_blob(remote_path)
  if not blob:
    raise GCSError('%s doesn\'t exist.' % file_uri)
  return blob


def ParseGCSPath(remote_file_path):
  """Parse a Google Cloud Storage path to bucket and path.

  Args:
    remote_file_path: gs://bucket/path/to/file format path.
  Returns:
    (bucket name, remote path relative to bucket)
  """
  p = re.compile(r'gs://([^/]*)/(.*)')
  m = p.match(remote_file_path)
  if m:
    return m.group(1), m.group(2)
  return None, None


def GCSFileEnumerator(storage_client, path, filename_filter=None):
  """Read config files from gcs.

  Args:
    storage_client: GCS client.
    path: gcs file path.
    filename_filter: only return files that match the filter.
  Yields:
    file like obj that is yaml config.
  """
  bucket_name, remote_path = ParseGCSPath(path)
  if not storage_client:
    return
  bucket = storage_client.get_bucket(bucket_name)
  iterator = bucket.list_blobs(prefix=remote_path)
  for blob in iterator:
    if filename_filter and not filename_filter(blob.name):
      continue
    logger.debug('Downloading gs://%s/%s.', bucket_name, blob.name)
    string_obj = six.moves.StringIO(blob.download_as_string())
    yield string_obj


def CalculateMd5Hash(file_path):
  """Calculate base64 encoded md5hash for a local file.

  Args:
    file_path: the local file path
  Returns:
    md5hash of the file.
  """
  m = hashlib.md5()
  with open(file_path, 'rb') as f:
    m.update(f.read())
  return six.ensure_text(base64.b64encode(m.digest()))


def CreateBackupFilePath(file_path):
  """Create backup file path for existing path.

  Args:
    file_path: the current file path.
  Returns:
    the backup path.
  """
  filename = os.path.basename(file_path)
  filename, ext = os.path.splitext(filename)
  new_filename = '%s-%s%s' % (
      filename,
      datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
      ext)
  return os.path.join(
      os.path.dirname(file_path),
      new_filename)
