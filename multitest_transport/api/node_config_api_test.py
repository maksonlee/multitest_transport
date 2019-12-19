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

"""Tests for node_config_api."""

import json

from absl.testing import absltest

from google.appengine.ext import ndb

from multitest_transport.api import api_test_util
from multitest_transport.api import node_config_api
from multitest_transport.models import ndb_models


class NodeConfigApiTest(api_test_util.TestCase):

  def setUp(self):
    super(NodeConfigApiTest, self).setUp(node_config_api.NodeConfigApi)

  def _CreateNodeConfig(self, data):
    node_config = ndb_models.NodeConfig(
        id=ndb_models.NODE_CONFIG_ID,
        env_vars=[
            ndb_models.NameValuePair(**obj)
            for obj in data['env_vars']
        ],
        test_resource_default_download_urls=[
            ndb_models.NameValuePair(**obj)
            for obj in data['test_resource_default_download_urls']
        ],
        result_report_action_keys=[
            ndb.Key(ndb_models.ResultReportAction, id_)
            for id_ in data['result_report_action_ids']
        ],
        proxy_config=ndb_models.ProxyConfig(**data['proxy_config']))
    return node_config

  def testGet(self):
    data = {
        'env_vars': [
            {'name': 'FOO', 'value': 'foo'},
            {'name': 'BAR', 'value': 'bar'},
        ],
        'test_resource_default_download_urls': [
            {'name': 'abc', 'value': 'file://abc'},
            {'name': 'def', 'value': 'file://def'},
        ],
        'result_report_action_ids': ['zzz'],
        'proxy_config': {
            'http_proxy': 'http_proxy',
            'https_proxy': 'https_proxy',
            'ftp_proxy': 'ftp_proxy',
            'no_proxy': 'no_proxy',
        },
    }
    node_config = self._CreateNodeConfig(data)
    node_config.put()

    res = self.app.get('/_ah/api/mtt/v1/node_config')

    msg = json.loads(res.body)
    self.assertEqual(data, msg)

  def testUpdate(self):
    data = {
        'env_vars': [
            {'name': 'FOO', 'value': 'foo'},
            {'name': 'BAR', 'value': 'bar'},
        ],
        'test_resource_default_download_urls': [
            {'name': 'abc', 'value': 'file://abc'},
            {'name': 'def', 'value': 'file://def'},
        ],
        'result_report_action_ids': ['zzz'],
        'proxy_config': {
            'http_proxy': 'http_proxy',
            'https_proxy': 'https_proxy',
            'ftp_proxy': 'ftp_proxy',
            'no_proxy': 'no_proxy',
        },
    }

    self.app.post_json('/_ah/api/mtt/v1/node_config', data)

    self.assertEqual(self._CreateNodeConfig(data), ndb_models.GetNodeConfig())

if __name__ == '__main__':
  absltest.main()
