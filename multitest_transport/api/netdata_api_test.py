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
"""Tests for netdata_api."""

from absl.testing import absltest
from protorpc import protojson
import requests_mock
import webtest

from multitest_transport.api import api_test_util
from multitest_transport.api import netdata_api
from multitest_transport.models import messages
from multitest_transport.util import env


class NetdataApiTest(api_test_util.TestCase):

  def setUp(self):
    super(NetdataApiTest, self).setUp(netdata_api.NetdataApi)
    env.NETDATA_URL = 'http://localhost:8008'

  @requests_mock.mock()
  def testGetAlarms(self, mock_requests):
    netdata_alarms = {
        'hostname': 'hostname',
        'alarms': {
            'disk_space._.disk_space_usage': {
                'id': 1,
                'status': 'WARNING',
                'value_string': '80.5%',
            },
            'disk_space._data.disk_space_usage': {
                'id': 2,
                'status': 'CRITICAL',
                'value_string': '98.5%',
            },
        },
    }
    mock_requests.get(
        'http://localhost:8008/host/hostname/api/v1/alarms',
        json=netdata_alarms)

    res = self.app.get(
        '/_ah/api/mtt/v1/netdata/alarms', {
            'alarm_names': ['disk_space._data.disk_space_usage'],
            'hostname': 'hostname',
        })
    res_msg = protojson.decode_message(messages.NetdataAlarmList, res.body)

    expected_alarm_list = messages.NetdataAlarmList(alarms=[
        messages.NetdataAlarm(
            hostname='hostname',
            id=2,
            name='disk_space._data.disk_space_usage',
            value='98.5%',
            status=messages.NetdataAlarmStatus.CRITICAL),
    ])
    self.assertEqual(expected_alarm_list, res_msg)

  @requests_mock.mock()
  def testGetAlarms_requestNetdataFail(self, mock_requests):
    mock_requests.get(requests_mock.ANY, json={}, status_code=404)

    with self.assertRaises(webtest.app.AppError):
      self.app.get(
          '/_ah/api/mtt/v1/netdata/alarms', {
              'alarm_names': ['disk_space._data.disk_space_usage'],
              'hostname': 'hostname',
          })


if __name__ == '__main__':
  absltest.main()
