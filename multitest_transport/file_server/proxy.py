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
import httplib
import logging
from six.moves import urllib
import webapp2

from multitest_transport.util import env


class FileServerProxy(webapp2.RequestHandler):
  """Proxies requests to the local file server."""

  def get(self, path):
    self._ProxyRequest('GET', path)

  def post(self, path):
    self._ProxyRequest('POST', path)

  def put(self, path):
    self._ProxyRequest('PUT', path)

  def delete(self, path):
    self._ProxyRequest('DELETE', path)

  def _ProxyRequest(self, method, path):
    # Combine target host and request URL
    path = urllib.parse.quote(path)
    target_host = env.FILE_SERVER_URL2
    (scheme, host, _, _, _) = urllib.parse.urlsplit(target_host)
    (_, _, _, query, fragment) = urllib.parse.urlsplit(self.request.url)
    url = urllib.parse.urlunsplit((scheme, host, path, query, fragment))  
    try:
      # Create and send request with body and header
      request = urllib.request.Request(
          url=url, data=self.request.body, headers=self.request.headers)
      request.get_method = lambda: method
      response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as e:
      # Relay HTTP errors back to caller
      response = e
    except urllib.error.URLError as e:
      logging.error('Error during proxy request %s: %s', url, e)
      self.response.status = httplib.INTERNAL_SERVER_ERROR
      return

    # Construct and send response
    self.response.status_int = response.code
    self.response.status_message = response.msg
    self.response.headers = response.headers
    self.response.body = response.read()
    response.close()


APP = webapp2.WSGIApplication([
    (r'/fs_proxy/(.*)', FileServerProxy),
], debug=True)
