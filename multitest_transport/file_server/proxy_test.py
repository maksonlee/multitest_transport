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

"""Android Test Station local file server proxy tests."""
import httplib
from absl.testing import absltest
import mock
from six.moves import urllib
import webapp2

from multitest_transport.file_server import proxy
from multitest_transport.util import env


class MockProxyResponse(object):
  """Fake response to return from the proxy's urllib request."""

  def __init__(self, status=200, data='', headers=None):
    self.code = status
    self.msg = httplib.responses[status]
    self.headers = headers or {}
    self.data = data

  def read(self):      return self.data

  def close(self):      pass


class MockProxyError(urllib.error.HTTPError, MockProxyResponse):
  """Fake error response to return from the proxy's urllib request."""

  def __init__(self, status=500, **kwargs):
    urllib.error.HTTPError.__init__(self, None, status, None, None, None)
    MockProxyResponse.__init__(self, status=status, **kwargs)


class FileServerProxyTest(absltest.TestCase):

  def setUp(self):
    super(FileServerProxyTest, self).setUp()
    env.FILE_SERVER_URL2 = 'http://localhost:8006/'
    self.patcher = mock.patch.object(urllib.request, 'urlopen')
    self.mock_urlopen = self.patcher.start()

  def tearDown(self):
    super(FileServerProxyTest, self).tearDown()
    self.patcher.stop()

  def SendMockRequest(self, url, method='GET', data='', headers=None):
    """Send a request to the proxy handler and return the response."""
    request = webapp2.Request.blank(url)
    request.method = method
    request.body = data
    for key, value in (headers or {}).iteritems():
      request.headers[key] = value
    return request.get_response(proxy.APP)

  def GetProxyRequest(self):
    """Fetch the request that was sent by the proxy."""
    return self.mock_urlopen.call_args[0][0]

  def AssertRequest(self, request, url='', method='GET', data='', headers=None):
    """Verifies the URL, method, data, and headers of a request."""
    self.assertEqual(url, request.get_full_url())
    self.assertEqual(method, request.get_method())
    self.assertEqual(data, request.get_data())
    for key, value in (headers or {}).iteritems():
      self.assertEqual(value, request.headers[key])

  def AssertResponse(self, response, status=500, data='', headers=None):
    """Verifies the status, data, and headers of a response."""
    self.assertEqual(status, response.status_int)
    self.assertEqual(data, response.body)
    for key, value in (headers or {}).iteritems():
      self.assertEqual(value, response.headers[key])

  def testProxyRequest_get(self):
    """Tests that a GET request can be sent."""
    self.mock_urlopen.return_value = MockProxyResponse()
    response = self.SendMockRequest('/fs_proxy/path/to/file')
    self.AssertResponse(response, status=200)
    proxy_request = self.GetProxyRequest()
    self.AssertRequest(proxy_request, url='http://localhost:8006/path/to/file')

  def testProxyRequest_post(self):
    """Tests that a POST request can be sent."""
    self.mock_urlopen.return_value = MockProxyResponse()
    self.SendMockRequest('/fs_proxy/path', method='POST')
    proxy_request = self.GetProxyRequest()
    self.AssertRequest(proxy_request, method='POST', url=mock.ANY)

  def testProxyRequest_put(self):
    """Tests that a PUT request can be sent."""
    self.mock_urlopen.return_value = MockProxyResponse()
    self.SendMockRequest('/fs_proxy/path', method='PUT')
    proxy_request = self.GetProxyRequest()
    self.AssertRequest(proxy_request, method='PUT', url=mock.ANY)

  def testProxyRequest_delete(self):
    """Tests that a DELETE request can be sent."""
    self.mock_urlopen.return_value = MockProxyResponse()
    self.SendMockRequest('/fs_proxy/path', method='DELETE')
    proxy_request = self.GetProxyRequest()
    self.AssertRequest(proxy_request, method='DELETE', url=mock.ANY)

  def testProxyRequest_encodedUrl(self):
    """Tests that encoded URLs are passed to the proxy request."""
    self.mock_urlopen.return_value = MockProxyResponse()
    response = self.SendMockRequest('/fs_proxy/hello%20world')
    self.AssertResponse(response, status=200)
    proxy_request = self.GetProxyRequest()
    self.AssertRequest(proxy_request, url='http://localhost:8006/hello%20world')

  def testProxyRequest_requestData(self):
    """Tests that data is passed to the proxy request."""
    self.mock_urlopen.return_value = MockProxyResponse()
    self.SendMockRequest('/fs_proxy/path', data='test')
    proxy_request = self.GetProxyRequest()
    self.AssertRequest(proxy_request, data='test', url=mock.ANY)

  def testProxyRequest_requestHeader(self):
    """Tests that headers are passed to the proxy request."""
    self.mock_urlopen.return_value = MockProxyResponse()
    self.SendMockRequest('/fs_proxy/path', headers={'Key': 'value'})
    proxy_request = self.GetProxyRequest()
    self.AssertRequest(proxy_request, headers={'Key': 'value'}, url=mock.ANY)

  def testProxyRequest_responseStatus(self):
    """Tests that the proxy response status is returned."""
    self.mock_urlopen.return_value = MockProxyResponse(status=303)
    response = self.SendMockRequest('/fs_proxy/path')
    self.AssertResponse(response, status=303)

  def testProxyRequest_responseData(self):
    """Tests that the proxy response data is returned."""
    self.mock_urlopen.return_value = MockProxyResponse(data='test')
    response = self.SendMockRequest('/fs_proxy/path')
    self.AssertResponse(response, status=200, data='test')

  def testProxyRequest_responseHeader(self):
    """Tests that the proxy response headers are returned."""
    self.mock_urlopen.return_value = MockProxyResponse(headers={'Key': 'value'})
    response = self.SendMockRequest('/fs_proxy/path')
    self.AssertResponse(response, status=200, headers={'Key': 'value'})

  def testProxyRequest_errorResponse(self):
    """Tests that an error response can be returned."""
    self.mock_urlopen.side_effect = MockProxyError(
        status=400, data='error', headers={'Key': 'value'})
    response = self.SendMockRequest('/fs_proxy/path')
    self.AssertResponse(
        response, status=400, data='error', headers={'Key': 'value'})

  def testProxyRequest_proxyError(self):
    """Tests that an error can be handled."""
    self.mock_urlopen.side_effect = urllib.error.URLError('error')
    response = self.SendMockRequest('/fs_proxy/path')
    self.AssertResponse(response, status=500)


if __name__ == '__main__':
  absltest.main()
