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

"""A utility module for GCS."""
import logging
import time

import cloudstorage as gcs

from google.appengine.api import app_identity
from google.appengine.api import urlfetch
from google.appengine.ext.cloudstorage import cloudstorage_stub

from multitest_transport.util import env
from multitest_transport.util import file_util

GCS_FILE_INFO = cloudstorage_stub._AE_GCSFileInfo_  GCS_POLL_INTERVAL = 0.5  # seconds
GCS_CHECK_MAX_ATTEMPTS = 5
PAGE_SIZE = 100


def GetDownloadUrl(filename):
  """Returns a download url for a GCS file.

  Args:
    filename: a GCS filename. Should start with a forward slash(/).
  Returns:
    a download URL.
  Raises:
    ValueError: if a file is not found.
  """
  if env.BLOBSTORE_PATH:
    return _GetLocalDownloadUrl(filename)
  return 'gs:/%s' % filename


def _GetLocalDownloadUrl(filename):
  """Returns a download URL (file URL) for local clients."""
  # File may not be available immediately after download, so try a few times.
  for _ in xrange(GCS_CHECK_MAX_ATTEMPTS):
    info = GCS_FILE_INFO.all().filter('filename = ', filename).get()
    if not info:
      time.sleep(GCS_POLL_INTERVAL)
      continue
    blob_key = info.key().id_or_name()
    return 'file://%s/%s/%s/%s' % (
        env.BLOBSTORE_PATH, env.APPLICATION_ID, blob_key[1], blob_key[1:])
  raise ValueError('Cannot find %s in local GCS' % filename)


def Exists(filename):
  """Checks whether a GCS file exists."""
  try:
    gcs.stat(filename)
  except gcs.NotFoundError:
    # file metadata not found
    return False

  if env.BLOBSTORE_PATH:
    # running in standalone mode, check if local file exists
    url = GetDownloadUrl(filename)
    info = file_util.FileHandle.Get(url).Info()
    return info is not None
  return True


def GetUploadUrl(path):
  """Returns an upload url for a GCS path.

  Args:
    path: a GCS path. Should start with a forward-slash(/).
  Returns:
    an upload URL.
  """
  if env.BLOBSTORE_PATH:
    # blobstore API expects a GCS path that doesn't start with a forward-slash.
    path = path[1:]
    return 'http://%s/gcs_proxy/%s' % (
        app_identity.get_default_version_hostname(), path)
  return 'gs:/' + path


def GetBlobstoreKey(filename):
  """Returns a Blobstore key for a GCS filename.

  In standalone mode, GCS is emulated by Blobstore and each file has a
  corresponding Blobstore key. This function always returns None if MTT is
  not running in standalone mode.

  Args:
    filename: a GCS file name.
  Returns:
    a Blobstore key. None if a file is not found.
  """
  if env.BLOBSTORE_PATH:
    info = GCS_FILE_INFO.all().filter('filename = ', filename).get()
    if info:
      return info.key().id_or_name()
  return None


def DeleteFiles(path, files_to_keep=None, max_file_age_seconds=0):
  """Delete files in GCS.

  Args:
    path: a GCS folder path.
    files_to_keep: a set of filenames to keep.
    max_file_age_seconds: max age of files to keep.
  """
  timestamp = time.time()
  max_ctime = timestamp - max_file_age_seconds
  urlfetch.set_default_fetch_deadline(env.GCS_FETCH_DEADLINE_SECONDS)
  marker = None
  deleted_count = 0
  deleted_size = 0
  while True:
    objs = list(gcs.listbucket(path, marker=marker, max_keys=PAGE_SIZE))
    count = 0
    for obj in objs:
      count += 1
      if files_to_keep and obj.filename in files_to_keep:
        continue
      if max_ctime < obj.st_ctime:
        continue
      logging.info('Deleting %s...', obj.filename)
      try:
        gcs.delete(obj.filename)
        deleted_count += 1
        deleted_size += obj.st_size
      except gcs.NotFoundError:
        logging.warn('Failed to delete %s (file not found)', obj.filename)
    if objs:
      marker = objs[-1]
    if count < PAGE_SIZE:
      break
  logging.info('Deleted %s files and restored %s bytes', deleted_count,
               deleted_size)
