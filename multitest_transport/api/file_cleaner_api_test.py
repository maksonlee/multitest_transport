# Copyright 2021 Google LLC
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
"""Tests for file_cleaner_api."""

import json

from absl.testing import absltest

from multitest_transport.api import api_test_util
from multitest_transport.api import file_cleaner_api
from multitest_transport.models import ndb_models


class FileCleanerApiTest(api_test_util.TestCase):

  def setUp(self):
    super(FileCleanerApiTest, self).setUp(file_cleaner_api.FileCleanerApi)

  def _CreateFileCleanerPolicy(self, data):
    policy = ndb_models.FileCleanerPolicy(
        name=data['name'],
        operation=ndb_models.FileCleanerOperation(
            type=ndb_models.FileCleanerOperationType.lookup_by_name(
                data['operation']['type'])),
        criteria=[
            ndb_models.FileCleanerCriterion(
                type=ndb_models.FileCleanerCriterionType.lookup_by_name(
                    obj['type'])) for obj in data['criteria']
        ])
    return policy

  def _CreateFileCleanerConfig(self, data):
    config = ndb_models.FileCleanerConfig(
        name=data['name'],
        directories=data['directories'],
        policy_names=data['policy_names'])
    return config

  def _CreateFileCleanerSettings(self, data):
    settings = ndb_models.FileCleanerSettings(
        id=ndb_models.FILE_CLEANER_SETTINGS_ID,
        policies=[
            self._CreateFileCleanerPolicy(obj) for obj in data['policies']
        ],
        configs=[self._CreateFileCleanerConfig(obj) for obj in data['configs']])
    return settings

  def testGet(self):
    data = {
        'policies': [{
            'criteria': [{
                'type': 'LAST_MODIFIED_DAYS'
            }],
            'name': 'policy name',
            'operation': {
                'type': 'DELETE'
            }
        }],
        'configs': [{
            'directories': ['/test/path'],
            'name': 'config name',
            'policy_names': ['policy name']
        }]
    }
    settings = self._CreateFileCleanerSettings(data)
    settings.put()

    res = self.app.get('/_ah/api/mtt/v1/file_cleaner/settings')

    msg = json.loads(res.body)
    self.assertEqual(data, msg)


if __name__ == '__main__':
  absltest.main()
