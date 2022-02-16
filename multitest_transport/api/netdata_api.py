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

"""A module to provide netdata APIs."""
# Non-standard docstrings are used to generate the API documentation.
import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote
import requests

from multitest_transport.api import base
from multitest_transport.models import messages as mtt_messages
from multitest_transport.util import env


@base.MTT_API.api_class(resource_name='netdata', path='netdata')
class NetdataApi(remote.Service):
  """A handler for Netdata API."""

  @base.ApiMethod(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          alarm_names=messages.StringField(1, repeated=True),
          hostname=messages.StringField(2, required=True)),
      mtt_messages.NetdataAlarmList,
      http_method='GET',
      path='/netdata/alarms',
      name='get')
  def GetAlarms(self, request):
    """Fetches raised netdata alarms."""
    url = f'{env.NETDATA_URL}/host/{request.hostname}/api/v1/alarms'
    netdata_response = requests.get(url)
    netdata_response.raise_for_status()

    alarm_names = set(request.alarm_names)
    alarms = []
    for name, alarm in netdata_response.json().get('alarms', {}).items():
      if name in alarm_names:
        alarms.append(
            mtt_messages.NetdataAlarm(
                hostname=request.hostname,
                id=alarm['id'],
                name=name,
                value=alarm['value_string'],
                status=mtt_messages.NetdataAlarmStatus.lookup_by_name(
                    alarm['status'])))
    return mtt_messages.NetdataAlarmList(alarms=alarms)
