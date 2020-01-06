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

"""A plugin for a local file store.

This plugin allows users to access a node file storage where users can upload
their own files to be used in test runs.
"""
import datetime
import logging
import os

import cloudstorage as gcs
from google.appengine.api import modules
from google.appengine.api import urlfetch

from multitest_transport.plugins import base
from multitest_transport.util import env

_GCS_PATH = env.GCS_DATA_PATH + '/local_file_store/'
_GCS_PATH_DELIMITER = '/'
_PAGE_SIZE = 25


class LocalFileStoreBuildProvider(base.BuildProvider):
  """A build provider for a local file store."""
  name = 'Local File Store'

  def _ToBuildItem(self, filestat):
    path = filestat.filename[len(_GCS_PATH):]
    if path.endswith(_GCS_PATH_DELIMITER):
      path = path.rstrip(_GCS_PATH_DELIMITER)
      name = path.split(_GCS_PATH_DELIMITER)[-1]
      name += _GCS_PATH_DELIMITER
    else:
      name = path.split(_GCS_PATH_DELIMITER)[-1]
    return base.BuildItem(
        name=name,
        path=path,
        is_file=not filestat.is_dir,
        size=long(filestat.st_size) if filestat.st_size else None,
        timestamp=(
            datetime.datetime.utcfromtimestamp(filestat.st_ctime)
            if filestat.st_ctime else None),
        origin_url='gs:/' + filestat.filename)

  def GetBuildItem(self, path=None):
    """Get a build item.

    Args:
      path: a path to file or directory, (e.g. path/to/file/kitten.png -> file
      path1/path2/ -> directory)

    Returns:
      a base.BuildItem object if response is valid, otherwise, return None
    """
    # Ensure local GCS uses right hostname, see b/141946636
    os.environ['HTTP_HOST'] = modules.get_hostname('default')
    filename = _GCS_PATH + path
    try:
      filestat = gcs.stat(filename)
      return self._ToBuildItem(filestat)
    except gcs.NotFoundError as e:
      logging.error('Cannot find %s', filename)
      raise base.FileNotFoundError(e)

  def DeleteBuildItem(self, path):
    """Delete a build item.

    Args:
      path: a build item path.
    """
    # Ensure local GCS uses right hostname, see b/141946636
    os.environ['HTTP_HOST'] = modules.get_hostname('default')
    filename = _GCS_PATH + path
    try:
      gcs.delete(filename)
    except gcs.NotFoundError as e:
      logging.error('Cannot find %s', filename)
      raise base.FileNotFoundError(e)

  def ListBuildItems(self, path='', page_token=None, item_type=None):
    """List build items under a given path.

    Args:
      path: a build item path (e.g. /git_master/taimen-userdebug).
      page_token: an optional page token.
      item_type: a type of build items to list. Returns all types if None.
    Returns:
      (a list of base.BuildItem objects, the next page token)
    """
    # Ensure local GCS uses right hostname, see b/141946636
    os.environ['HTTP_HOST'] = modules.get_hostname('default')
    urlfetch.set_default_fetch_deadline(env.GCS_FETCH_DEADLINE_SECONDS)
    gcs_path = _GCS_PATH + path
    if not gcs_path.endswith(_GCS_PATH_DELIMITER):
      gcs_path += _GCS_PATH_DELIMITER
    objs = list(
        gcs.listbucket(
            gcs_path, marker=page_token, max_keys=_PAGE_SIZE,
            delimiter=_GCS_PATH_DELIMITER))
    items = []
    for obj in objs:
      if item_type == base.BuildItemType.FILE and obj.is_dir:
        continue
      if item_type == base.BuildItemType.DIRECTORY and not obj.is_dir:
        continue
      items.append(self._ToBuildItem(obj))
    next_page_token = objs[-1].filename if len(objs) == _PAGE_SIZE else None
    return (items, next_page_token)
