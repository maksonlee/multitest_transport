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

"""A base class for API handlers."""
import functools
import httplib
import json
import sys
import traceback

import endpoints

DEFAULT_MAX_RESULTS = 25  # The default number of max results per page.

MTT_API = endpoints.api(
    name='mtt',
    version='v1',
    description='MTT API',
    allowed_client_ids=['anonymous', endpoints.API_EXPLORER_CLIENT_ID],
    scopes=[endpoints.EMAIL_SCOPE])


class ApiError(endpoints.ServiceException):
  """Base class for all API errors."""

  def __init__(self, cause=None, status=None, message=None, **kwargs):
    self.cause = cause
    self.http_status = status or httplib.INTERNAL_SERVER_ERROR
    kwargs['message'] = message or httplib.responses[self.status]
    kwargs['stacktrace'] = traceback.extract_tb(sys.exc_info()[2])
    super(ApiError, self).__init__(json.dumps(kwargs))


def convert_exception(func):
  """Converts exception into ApiErrors, to include error and stacktrace."""

  @functools.wraps(func)
  def wrap(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except Exception as e:        raise ApiError(
          cause=e, status=getattr(e, 'http_status', None), message=str(e))

  return wrap
