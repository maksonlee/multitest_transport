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

"""Client used to upload Google Analytics events."""
import ctypes
import logging
import multiprocessing
from typing import Iterator, Optional, Tuple
import urllib.parse
import urllib.request

import flask

from multitest_transport.models import ndb_models
from multitest_transport.util import analytics
from multitest_transport.util import env

# Error tracking (uploading disabled after too many consecutive upload errors)
MAX_CONSECUTIVE_UPLOAD_ERRORS = 20
_UPLOAD_ERROR_COUNT = multiprocessing.Value(ctypes.c_int, 0)

# WSGI application
APP = flask.Flask(__name__)

# GA constants
_GA_ENDPOINT = 'http://www.google-analytics.com/collect'
_API_VERSION = '1'
_EVENT_TYPE = 'event'
_TRACKING_ID = 'UA-140187490-2'

# GA custom metrics definitions
_METRIC_KEYS = {
    'app_version': 'cd1',
    'test_name': 'cd2',
    'test_version': 'cd3',
    'state': 'cd4',
    'is_rerun': 'cd5',
    'is_google': 'cd6',
    'command': 'cd7',
    'failed_test_count_threshold': 'cd8',
    'test_run_command': 'cd9',
    'test_run_retry_command': 'cd10',
    'missing_previous_run': 'cd11',
    'test_id': 'cd12',
    'is_sequence_run': 'cd13',
    'user_tag': 'cd14',
    'operation_mode': 'cd15',
    'worker_id': 'cd16',
    'duration_seconds': 'cm1',
    'device_count': 'cm2',
    'attempt_count': 'cm3',
    'failed_module_count': 'cm4',
    'test_count': 'cm5',
    'failed_test_count': 'cm6',
    'elapsed_time_seconds': 'cm7',
    'prev_total_test_count': 'cm8',
    'prev_failed_module_count': 'cm9',
    'prev_failed_test_count': 'cm10',
    'total_disk_size_byte': 'cm11',
    'used_disk_size_byte': 'cm12',
    'free_disk_size_byte': 'cm13',
    'worker_count': 'cm14'
}


@APP.route('/_ah/queue/' + analytics.QUEUE_NAME, methods=['POST'])
def UploadEvent() -> flask.Response:
  """Parses event parameters from the request body and uploads to GA."""
  params = flask.request.get_json(force=True)
  category = params.pop('category')
  action = params.pop('action')
  uploaded = _UploadEvent(category, action, **params)
  return flask.Response(status=201 if uploaded else 204)


def _UploadEvent(category: str, action: str, **kwargs) -> bool:
  """Uploads an event to GA if metrics are enabled."""
  private_node_config = ndb_models.GetPrivateNodeConfig()
  if (env.IS_DEV_MODE or not private_node_config.metrics_enabled or
      _UPLOAD_ERROR_COUNT.value >= MAX_CONSECUTIVE_UPLOAD_ERRORS):  # pytype: disable=attribute-error  # re-none
    logging.debug('Metrics disabled - skipping %s:%s', category, action)
    return False
  event = _Event(private_node_config.server_uuid, category, action, **kwargs)
  data = urllib.parse.urlencode(dict(event)).encode()
  request = urllib.request.Request(
      url=_GA_ENDPOINT, data=data, headers={'User-Agent': 'MTT'})
  try:
    urllib.request.urlopen(request)
    _UPLOAD_ERROR_COUNT.value = 0
  except:
    with _UPLOAD_ERROR_COUNT.get_lock():
      _UPLOAD_ERROR_COUNT.value += 1  # pytype: disable=attribute-error  # re-none
    raise
  return True


class _Event(object):
  """Holds GA event information."""

  def __init__(self,
               server_uuid: str,
               category: str,
               action: str,
               label: Optional[str] = None,
               value: Optional[str] = None,
               **kwargs):
    private_node_config = ndb_models.GetPrivateNodeConfig()
    # Required parameters
    self.v = _API_VERSION  # API version
    self.tid = _TRACKING_ID  # Tracking ID
    self.cid = server_uuid  # Server ID
    self.t = _EVENT_TYPE  # Event type
    self.ec = category  # Event category
    self.ea = action  # Event action
    # Optional parameters
    if label:
      self.el = label
    if value:
      self.ev = value
    # Custom dimensions and metrics
    setattr(self, _METRIC_KEYS['app_version'], env.VERSION)
    setattr(self, _METRIC_KEYS['is_google'], env.IS_GOOGLE)
    setattr(self, _METRIC_KEYS['user_tag'], private_node_config.gms_client_id)
    for key, value in kwargs.items():
      if not _METRIC_KEYS[key]:
        logging.warning('Unknown metric key: %s', key)
        continue
      setattr(self, _METRIC_KEYS[key], value)

  def __iter__(self) -> Iterator[Tuple[str, str]]:
    for key, value in self.__dict__.items():
      if value is not None:
        yield key, value

  def __eq__(self, other) -> bool:
    return isinstance(other, _Event) and dict(self) == dict(other)

  def __ne__(self, other) -> bool:
    return not self.__eq__(other)
