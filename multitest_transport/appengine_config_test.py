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

"""Tests for appengine_confg.py."""

import os

from absl.testing import absltest

from google.appengine.ext import testbed

from multitest_transport import appengine_config
from multitest_transport.models import ndb_models


class AppengineConfigTest(absltest.TestCase):

  def setUp(self):
    super(AppengineConfigTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.addCleanup(self.testbed.deactivate)

  def test_apply_proxy_config(self):
    proxy_config = ndb_models.ProxyConfig()
    proxy_config.http_proxy = 'http_proxy'
    proxy_config.https_proxy = 'https_proxy'
    proxy_config.ftp_proxy = 'ftp_proxy'
    proxy_config.no_proxy = 'no_proxy'
    node_config = ndb_models.GetNodeConfig()
    node_config.proxy_config = proxy_config
    node_config.put()

    appengine_config.apply_proxy_config()

    self.assertEqual('http_proxy', os.environ['http_proxy'])
    self.assertEqual('https_proxy', os.environ['https_proxy'])
    self.assertEqual('ftp_proxy', os.environ['ftp_proxy'])
    self.assertEqual('no_proxy,127.0.0.1', os.environ['no_proxy'])


if __name__ == '__main__':
  absltest.main()
