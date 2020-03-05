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

"""A TFC client module."""
import json
import threading

import apiclient
import httplib2
from protorpc import protojson
from tradefed_cluster import api_messages

from google.appengine.api import modules

API_NAME = 'tradefed_cluster'
API_VERSION = 'v1'
API_DISCOVERY_URL_FORMAT = 'http://%s/_ah/api/discovery/v1/apis/%s/%s/rest'
HTTP_TIMEOUT_SECONDS = 60

_tls = threading.local()


def _GetAPIClient():
  if not hasattr(_tls, 'api_client'):
    http = httplib2.Http(timeout=HTTP_TIMEOUT_SECONDS)
    hostname = modules.get_hostname('default')
    discovery_url = API_DISCOVERY_URL_FORMAT % (hostname, API_NAME, API_VERSION)
    _tls.api_client = apiclient.discovery.build(
        API_NAME, API_VERSION, http=http, discoveryServiceUrl=discovery_url)
  return _tls.api_client


def BackfillCommands():
  """Backfill commands for timeout monitoring."""
  _GetAPIClient().coordinator().backfillCommands().execute()


def BackfillCommandAttempts():
  """Backfill command attempts for timeout monitoring."""
  _GetAPIClient().coordinator().backfillCommandAttempts().execute()


def NewRequest(new_request_msg):
  """Creates a new request.

  Args:
    new_request_msg: an api_messages.NewRequest object.
  Returns:
    A api_messages.Request object.
  """
  body = json.loads(protojson.encode_message(new_request_msg))
  res = _GetAPIClient().requests().new(body=body).execute()
  return protojson.decode_message(api_messages.RequestMessage, json.dumps(res))


def GetRequest(request_id):
  """Gets a TFC request.

  Args:
    request_id: a request ID.
  Returns:
    A TFC Request object.
  """
  res = _GetAPIClient().requests().get(request_id=request_id).execute()
  return protojson.decode_message(api_messages.RequestMessage, json.dumps(res))


def CancelRequest(request_id):
  """Cancels a request.

  Args:
    request_id: a request ID.
  """
  _GetAPIClient().requests().cancel(request_id=request_id).execute()


def GetTestContext(request_id, command_id):
  """Gets a test context.

  Args:
    request_id: a request ID.
    command_id: a command ID.
  Returns:
    A TFC TestContext object.
  """
  req = _GetAPIClient().requests().testContext().get(
      request_id=request_id, command_id=command_id)
  res = req.execute()
  return protojson.decode_message(api_messages.TestContext, json.dumps(res))


def GetAttempt(request_id, attempt_id):
  """Find a TFC command attempt.

  Args:
    request_id: request ID.
    attempt_id: attempt ID.
  Returns:
    TFC command attempt, or None if not found
  """
  request = GetRequest(request_id)
  attempts = request.command_attempts or []
  return next((a for a in attempts if a.attempt_id == attempt_id), None)


def GetDeviceInfo(serial_num):
  """Gets device info.

  Args:
    serial_num: a serial number.
  Returns:
    A device info object or None if not found.
  """
  try:
    res = _GetAPIClient().devices().get(device_serial=serial_num).execute()
    return protojson.decode_message(api_messages.DeviceInfo, json.dumps(res))
  except apiclient.errors.HttpError as e:
    if e.resp.status == 404:
      return None
    raise e
