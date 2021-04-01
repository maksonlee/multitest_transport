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

"""Android Test Station local file server proxy."""
import logging

import flask
import flask.views
import six
from six.moves import http_client
from six.moves import urllib

from multitest_transport.util import env

APP = flask.Flask(__name__)


class FileServerProxy(flask.views.MethodView):
  """Proxies requests to the local file server."""

  def get(self, path):
    return self._ProxyRequest('GET', path)

  def post(self, path):
    return self._ProxyRequest('POST', path)

  def put(self, path):
    return self._ProxyRequest('PUT', path)

  def delete(self, path):
    return self._ProxyRequest('DELETE', path)

  def _ProxyRequest(self, method, path):
    # Combine target host and request URL
    target_host = env.FILE_SERVER_URL
    (scheme, host, _, _, _) = urllib.parse.urlsplit(target_host)
    (_, _, _, query, fragment) = urllib.parse.urlsplit(flask.request.url)
    url = urllib.parse.urlunsplit((scheme, host, path, query, fragment))  
    try:
      # Create and send request with body and header
      data = flask.request.get_data()
      headers = {}
      # urllib in python2.7 can only handle 'str' (binary).
      # We make sure they are binary before passing it to urllib.
      url = str(url)
      for key, value in flask.request.headers.items():
        headers[str(key)] = str(value)
      data = six.ensure_binary(data)
      request = urllib.request.Request(url=url, data=data, headers=headers)
      request.get_method = lambda: method
      response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as e:
      # Relay HTTP errors back to caller
      r = flask.Response(e.read(), headers=dict(e.headers))
      r.status = e.reason
      r.status_code = int(e.code)
      return r
    except urllib.error.URLError:
      logging.exception('Error during proxy request %s', url)
      return flask.Response(status=http_client.INTERNAL_SERVER_ERROR)

    r = flask.Response(response.read(), headers=dict(response.headers))
    r.status = getattr(response, 'msg')
    r.status_code = int(response.code)
    response.close()
    return r


APP.add_url_rule(
    '/fs_proxy/<path:path>', view_func=FileServerProxy.as_view('fs_proxy'))
