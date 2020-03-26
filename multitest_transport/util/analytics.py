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

"""Utilities for tracking Google Analytics events."""
import logging
import six
from six.moves import urllib

import webapp2
from google.appengine.ext import deferred

from multitest_transport.models import ndb_models
from multitest_transport.util import env

# GA constants
_GA_ENDPOINT = 'http://www.google-analytics.com/collect'
_API_VERSION = '1'
_EVENT_TYPE = 'event'
_TRACKING_ID = 'UA-140187490-2'

# GA categories and actions
SYSTEM_CATEGORY = 'system'
TEST_RUN_CATEGORY = 'test_run'
HEARTBEAT_ACTION = 'heartbeat'
START_ACTION = 'start'
END_ACTION = 'end'

# GA custom metrics definitions
_METRIC_KEYS = {
    'app_version': 'cd1',
    'test_name': 'cd2',
    'test_version': 'cd3',
    'state': 'cd4',
    'is_rerun': 'cd5',
    'is_google': 'cd6',
    'duration_seconds': 'cm1',
    'device_count': 'cm2',
    'attempt_count': 'cm3',
    'failed_module_count': 'cm4',
    'test_count': 'cm5',
    'failed_test_count': 'cm6',
}


def Log(category, action, **kwargs):
  """Asynchronous log event in GA if metrics are enabled."""
  private_node_config = ndb_models.GetPrivateNodeConfig()
  if env.IS_DEV_MODE or not private_node_config.metrics_enabled:
    logging.debug('Metrics disabled - skipping %s:%s', category, action)
    return
  event = _Event(private_node_config.server_uuid, category, action, **kwargs)
  deferred.defer(_Send, event)


def _Send(event):
  """Send event to GA."""
  try:
    data = urllib.parse.urlencode(dict(event))
    request = urllib.request.Request(
        url=_GA_ENDPOINT, data=data, headers={'User-Agent': 'MTT'})
    urllib.request.urlopen(request)
  except Exception as e:      logging.debug('Failed to send analytics: %s', e)


class _Event(object):
  """Holds GA event information."""

  def __init__(self, server_uuid, category, action, **kwargs):
    # Required parameters
    self.v = _API_VERSION  # API version
    self.tid = _TRACKING_ID  # Tracking ID
    self.cid = server_uuid  # Server ID
    self.t = _EVENT_TYPE  # Event type
    self.ec = category  # Event category
    self.ea = action  # Event action
    # Custom dimensions and metrics
    setattr(self, _METRIC_KEYS['app_version'], env.VERSION)
    setattr(self, _METRIC_KEYS['is_google'], env.IS_GOOGLE)
    for key, value in six.iteritems(kwargs):
      if not _METRIC_KEYS[key]:
        logging.warning('Unknown metric key: %s', key)
        continue
      setattr(self, _METRIC_KEYS[key], value)

  def __iter__(self):
    for key, value in six.iteritems(self.__dict__):
      if value is not None:
        yield key, value

  def __eq__(self, other):
    return isinstance(other, _Event) and dict(self) == dict(other)

  def __ne__(self, other):
    return not self.__eq__(other)


class HeartbeatSender(webapp2.RequestHandler):
  """Request handler which periodically logs that this instance is up."""

  def get(self):
    Log(SYSTEM_CATEGORY, HEARTBEAT_ACTION)
