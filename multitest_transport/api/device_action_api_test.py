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

"""Tests for device_action_api."""

from protorpc import protojson

from absl.testing import absltest

from multitest_transport.api import api_test_util
from multitest_transport.api import device_action_api
from multitest_transport.models import messages
from multitest_transport.models import ndb_models


class DeviceActionApiTest(api_test_util.TestCase):
  """Unit tests for device action APIs."""

  def setUp(self):
    super(DeviceActionApiTest, self).setUp(device_action_api.DeviceActionApi)

  def _CreateDeviceAction(self, name='action'):
    obj = ndb_models.DeviceAction(name=name)
    obj.put()
    return obj

  def testList(self):
    device_actions = [self._CreateDeviceAction()]

    res = self.app.get('/_ah/api/mtt/v1/device_actions')

    res_msg = protojson.decode_message(messages.DeviceActionList, res.body)
    for obj, msg in zip(device_actions, res_msg.device_actions):
      self.assertEqual(messages.Convert(obj, messages.DeviceAction), msg)

  def testCreate(self):
    data = {
        'name': 'foo',
        'description': 'description',
        'test_resource_defs': [
            {'name': 'resource', 'default_download_url': 'resource_url'},
        ],
        'tradefed_target_preparers': [{
            'class_name': 'com.android.foo',
            'option_values': [
                {'name': 'option', 'values': ['value', 'value2']}
            ]
        }]
    }

    res = self.app.post_json('/_ah/api/mtt/v1/device_actions', data)
    msg = protojson.decode_message(messages.DeviceAction, res.body)
    device_action = messages.ConvertToKey(ndb_models.DeviceAction, msg.id).get()
    self.assertIsNotNone(device_action)
    self.assertEqual(data['name'], device_action.name)
    self.assertEqual(data['description'], device_action.description)
    for d, obj in zip(
        data['test_resource_defs'], device_action.test_resource_defs):
      self.assertEqual(d['name'], obj.name)
      self.assertEqual(d['default_download_url'], obj.default_download_url)
    self.assertEqual(
        data['tradefed_target_preparers'][0]['class_name'],
        device_action.tradefed_target_preparers[0].class_name)
    for d, obj in zip(data['tradefed_target_preparers'][0]['option_values'],
                      device_action.tradefed_target_preparers[0].option_values):
      self.assertEqual(d['name'], obj.name)
      self.assertEqual(d['values'], obj.values)

  def testGet(self):
    device_action = self._CreateDeviceAction()
    device_action_id = str(device_action.key.id())

    res = self.app.get('/_ah/api/mtt/v1/device_actions/%s' % device_action_id)

    msg = protojson.decode_message(messages.DeviceAction, res.body)
    self.assertEqual(
        messages.Convert(device_action, messages.DeviceAction), msg)

  def testGet_stubAction(self):
    res = self.app.get('/_ah/api/mtt/v1/device_actions/0')

    msg = protojson.decode_message(messages.DeviceAction, res.body)
    self.assertIsNone(msg.id)
    self.assertEqual('', msg.name)

  def testUpdate(self):
    device_action = self._CreateDeviceAction()
    device_action_id = str(device_action.key.id())
    data = {
        'id': device_action_id,
        'name': 'bar'
    }

    res = self.app.put_json(
        '/_ah/api/mtt/v1/device_actions/%s' % device_action_id, data)

    device_action = device_action.key.get()
    msg = protojson.decode_message(messages.DeviceAction, res.body)
    self.assertEqual(
        messages.Convert(device_action, messages.DeviceAction), msg)
    self.assertEqual(data['name'], device_action.name)

  def testDelete(self):
    device_action = self._CreateDeviceAction()
    device_action_id = str(device_action.key.id())

    self.app.delete('/_ah/api/mtt/v1/device_actions/%s' % device_action_id)

    device_action = device_action.key.get()
    self.assertIsNone(device_action)


if __name__ == '__main__':
  absltest.main()
