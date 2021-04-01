# Lint as: python2, python3
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

"""Unit tests for the launcher module."""
import os
import socket

from absl.testing import absltest
from absl.testing import parameterized
import mock
import requests

from multitest_transport.app_helper import launcher


class RawPathMiddlewareTest(absltest.TestCase):
  """"Tests RawPathMiddleware functionality."""

  def test_call(self):
    app = mock.MagicMock()
    middleware = launcher.RawPathMiddleware(app)
    raw_uri = 'http://localhost:8000/hello%20world?query'
    middleware({'RAW_URI': raw_uri, 'PATH_INFO': '/hello world'}, None)
    app.assert_called_once_with(
        {'RAW_URI': raw_uri, 'PATH_INFO': '/hello%20world'}, None)


class InMemoryAppManagerTest(absltest.TestCase):
  """"Tests InMemoryAppManager functionality."""

  @mock.patch.object(socket, 'gethostname')
  def test_GetInfo(self, mock_gethostname):
    mock_gethostname.return_value = 'localhost'
    module = launcher.Module(name='module_name', path='module_path', port=8000)
    app_manager = launcher.InMemoryAppManager({'module_name': module})
    info = app_manager.GetInfo('module_name')
    self.assertEqual('module_name', info.name)
    self.assertEqual('localhost:8000', info.hostname)


class ModuleApplicationTest(parameterized.TestCase):
  """"Tests ModuleApplication functionality."""

  def test_format_host_port(self):
    self.assertEqual('[::]:8000',
                     launcher.ModuleApplication.format_host_port('::', 8000))
    self.assertEqual('0.0.0.0:80',
                     launcher.ModuleApplication.format_host_port('0.0.0.0', 80))

  @mock.patch.dict('os.environ', clear=True)
  @mock.patch.object(socket, 'gethostname')
  def test_load_config(self, mock_gethostname):
    mock_gethostname.return_value = 'hostname'
    module = launcher.Module(name='name', path='path', port=8000)
    module_app = launcher.ModuleApplication(
        module, host='::', log_level='ERROR', live_reload=True)
    module_app.load_config()
    self.assertEqual(
        {
            'DEFAULT_VERSION_HOSTNAME': 'hostname:8000',
            'CURRENT_MODULE_ID': 'name'
        }, os.environ)
    self.assertEqual(['[::]:8000'], module_app.cfg.bind)
    self.assertEqual('ERROR', module_app.cfg.logconfig_dict['root']['level'])
    self.assertTrue(module_app.cfg.reload)

  @parameterized.parameters((200, True), (404, True), (500, False))
  @mock.patch.object(requests, 'get')
  def test_start_server(self, status_code, success, mock_request):
    module = launcher.Module(name='name', path='path', port=8000)
    module_app = launcher.ModuleApplication(module)
    mock_request.return_value = mock.MagicMock(status_code=status_code)
    self.assertEqual(success, module_app.start_server())


if __name__ == '__main__':
  absltest.main()
