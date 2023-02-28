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
from typing import List, Optional

import apiclient
import httplib2
from protorpc import protojson
import requests
from tradefed_cluster import api_messages
from tradefed_cluster.common import IsFinalCommandState
from tradefed_cluster.services import app_manager


from multitest_transport.util import env

API_NAME = 'tradefed_cluster'
API_VERSION = 'v1'
API_DISCOVERY_URL_FORMAT = 'http://%s/_ah/api/discovery/v1/apis/%s/%s/rest'
HTTP_TIMEOUT_SECONDS = 5 * 60

_tls = threading.local()


class _Http:
  """A httplib2.Http-like object based on requests."""

  def request(  
      self,
      uri,
      method='GET',
      body=None,
      headers=None,
      redirections=None,
      connection_type=None):
    """Makes an HTTP request using httplib2 semantics."""
    del connection_type  # Unused

    with requests.Session() as session:
      session.max_redirects = redirections
      response = session.request(
          method, uri, data=body, headers=headers, timeout=HTTP_TIMEOUT_SECONDS)
      headers = dict(response.headers)
      headers['status'] = response.status_code
      content = response.content
    return httplib2.Response(headers), content


def _GetAPIClient():
  """Returns a API client for TFC."""
  if not hasattr(_tls, 'api_client'):
    hostname = app_manager.GetInfo('default').hostname.replace(
        env.HOSTNAME, 'localhost')
    discovery_url = API_DISCOVERY_URL_FORMAT % (hostname, API_NAME, API_VERSION)
    _tls.api_client = apiclient.discovery.build(
        API_NAME,
        API_VERSION,
        discoveryServiceUrl=discovery_url,
        http=_Http())
  return _tls.api_client


def BackfillCommands():
  """Backfill commands for timeout monitoring."""
  _GetAPIClient().coordinator().backfillCommands().execute()


def BackfillCommandAttempts():
  """Backfill command attempts for timeout monitoring."""
  _GetAPIClient().coordinator().backfillCommandAttempts().execute()


def BackfillRequestSyncs():
  """Backfill command attempts for timeout monitoring."""
  _GetAPIClient().coordinator().backfillRequestSyncs().execute()


def NewRequest(
    new_request_msg: api_messages.NewMultiCommandRequestMessage
) -> api_messages.RequestMessage:
  """Creates a new request.

  Args:
    new_request_msg: an api_messages.NewMultiCommandRequest object.
  Returns:
    A api_messages.Request object.
  """
  body = json.loads(protojson.encode_message(new_request_msg))  # pytype: disable=module-attr
  res = _GetAPIClient().requests().newMultiCommandRequest(body=body).execute()
  return protojson.decode_message(api_messages.RequestMessage, json.dumps(res))  # pytype: disable=module-attr


def GetRequest(request_id: int) -> api_messages.RequestMessage:
  """Gets a TFC request.

  Args:
    request_id: a request ID.
  Returns:
    A TFC Request object.
  """
  res = _GetAPIClient().requests().get(request_id=request_id).execute()
  return protojson.decode_message(api_messages.RequestMessage, json.dumps(res))  # pytype: disable=module-attr


def CancelRequest(request_id: int):
  """Cancels a request.

  Args:
    request_id: a request ID.
  """
  _GetAPIClient().requests().cancel(request_id=request_id).execute()


def GetTestContext(request_id: int,
                   command_id: str) -> api_messages.TestContext:
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
  return protojson.decode_message(api_messages.TestContext, json.dumps(res))  # pytype: disable=module-attr


def GetAttempt(request_id: int,
               attempt_id: str) -> Optional[api_messages.CommandAttemptMessage]:
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


def GetLatestFinishedAttempts(
    request_id: int) -> List[api_messages.CommandAttemptMessage]:
  """Find the latest TFC command attempts in a final state.

  Args:
    request_id: request ID.
  Returns:
    A list of finished TFC command attempts
  """
  request = GetRequest(request_id)
  attempt_map = {}
  for attempt in request.command_attempts:
    if not IsFinalCommandState(attempt.state):
      continue
    attempt_map[attempt.command_id] = attempt
  return list(attempt_map.values())


def ListDevices() -> Optional[api_messages.DeviceInfoCollection]:
  """Gets a list of all devices.

  Returns:
    A DeviceInfoCollection object.
  """
  res = _GetAPIClient().devices().list().execute()
  return protojson.decode_message(  # pytype: disable=module-attr
      api_messages.DeviceInfoCollection, json.dumps(res))


def GetDeviceInfo(serial_num: str) -> Optional[api_messages.DeviceInfo]:
  """Gets device info.

  Args:
    serial_num: a serial number.
  Returns:
    A device info object or None if not found.
  """
  try:
    res = _GetAPIClient().devices().get(device_serial=serial_num).execute()
    return protojson.decode_message(api_messages.DeviceInfo, json.dumps(res))  # pytype: disable=module-attr
  except apiclient.errors.HttpError as e:
    if e.resp.status == 404:
      return None
    raise


def GetRequestInvocationStatus(
    request_id: int) -> api_messages.InvocationStatus:
  """Fetches the invocation status for a request."""
  res = _GetAPIClient().requests().invocationStatus().get(
      request_id=request_id).execute()
  return protojson.decode_message(  # pytype: disable=module-attr
      api_messages.InvocationStatus, json.dumps(res))
