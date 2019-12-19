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

"""A module to provide test plan APIs."""

import logging

import croniter
from protorpc import message_types
from protorpc import messages
from protorpc import remote

from google.appengine.ext import ndb
import endpoints

from multitest_transport.api import base
from multitest_transport.models import build
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import test_plan_kicker
from multitest_transport.test_scheduler import test_scheduler


def _IsValidCronExpression(cron_exp):
  """Check validity of a given cron expression.

  Args:
    cron_exp: a cron expression.
  Returns:
    True if valid. Otherwise False.
  """
  try:
    croniter.croniter(cron_exp)
  except ValueError:
    return False
  return True


def _ValidateTestPlan(test_plan):
  """Check validity of a given test plan.

  Args:
    test_plan: a ndb_models.TestPlan object.
  """
  if test_plan.cron_exp and not _IsValidCronExpression(test_plan.cron_exp):
    raise endpoints.BadRequestException(
        ('Invalid cron expression (%s). Cron expression should be ordered as '
         'minute, hour, day of month, month, day of week.')
        % test_plan.cron_exp)
  for config in test_plan.test_run_configs:
    if not config.test_key.get():
      raise endpoints.BadRequestException(
          'test %s does not exist' % config.test_key.id())
  for pipe in test_plan.test_resource_pipes:
    build_locator = build.BuildLocator.ParseUrl(pipe.url)
    if build_locator and not ndb.Key(ndb_models.BuildChannelConfig,
                                     build_locator.build_channel_id).get():
      raise endpoints.BadRequestException('build channel %s does not exist' %
                                          build_locator.build_channel_id)


@base.MTT_API.api_class(resource_name='test_plan', path='test_plans')
class TestPlanApi(remote.Service):
  """A handler for Test Plan API."""

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(message_types.VoidMessage),
      mtt_messages.TestPlanList, path='/test_plans', http_method='GET',
      name='list')
  def List(self, request):
    test_plans = list(ndb_models.TestPlan.query()
                      .order(ndb_models.TestPlan.name))
    test_plan_msgs = mtt_messages.Convert(test_plans, mtt_messages.TestPlan)
    return mtt_messages.TestPlanList(test_plans=test_plan_msgs)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(mtt_messages.TestPlan),
      mtt_messages.TestPlan, path='/test_plans', http_method='POST',
      name='create')
  def Create(self, request):
    logging.info(request)
    test_plan = mtt_messages.Convert(
        request, ndb_models.TestPlan, from_cls=mtt_messages.TestPlan)
    _ValidateTestPlan(test_plan)
    test_plan.key = None
    test_plan.put()
    test_scheduler.ScheduleTestPlanCronJob(test_plan.key.id())
    return mtt_messages.Convert(test_plan, mtt_messages.TestPlan)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_plan_id=messages.StringField(1, required=True)),
      mtt_messages.TestPlan, path='{test_plan_id}', http_method='GET',
      name='get')
  def Get(self, request):
    test_plan = None
    # For test plan ID 0, it should return a default test plan object which can
    # be used as a template in UI.
    if request.test_plan_id == '0':
      test_plan = ndb_models.TestPlan(id=0, name='')
    else:
      test_plan = mtt_messages.ConvertToKey(
          ndb_models.TestPlan, request.test_plan_id).get()
    if not test_plan:
      raise endpoints.NotFoundException(
          'No test plan with ID %s' % request.test_plan_id)
    return mtt_messages.Convert(test_plan, mtt_messages.TestPlan)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          mtt_messages.TestPlan,
          test_plan_id=messages.StringField(1, required=True)),
      mtt_messages.TestPlan, path='{test_plan_id}', http_method='POST',
      name='update')
  def Update(self, request):
    test_plan_key = mtt_messages.ConvertToKey(
        ndb_models.TestPlan, request.test_plan_id)
    if not test_plan_key.get():
      raise endpoints.NotFoundException()
    test_plan = mtt_messages.Convert(
        request, ndb_models.TestPlan, from_cls=mtt_messages.TestPlan)
    _ValidateTestPlan(test_plan)
    test_plan.key = test_plan_key
    test_plan.put()
    test_scheduler.ScheduleTestPlanCronJob(test_plan.key.id())
    return mtt_messages.Convert(test_plan, mtt_messages.TestPlan)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_plan_id=messages.StringField(1, required=True)),
      message_types.VoidMessage, path='{test_plan_id}/delete',
      http_method='POST', name='delete')
  def Delete(self, request):
    test_plan_key = mtt_messages.ConvertToKey(
        ndb_models.TestPlan, request.test_plan_id)
    test_plan_key.delete()
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_plan_id=messages.StringField(1, required=True)),
      message_types.VoidMessage, path='{test_plan_id}/run', http_method='POST',
      name='run')
  def Run(self, request):
    test_plan = mtt_messages.ConvertToKey(
        ndb_models.TestPlan, request.test_plan_id).get()
    if not test_plan:
      raise endpoints.NotFoundException('Test plan %s does not exist'
                                        % request.test_plan_id)
    if not test_plan.test_run_configs:
      raise endpoints.BadRequestException(
          'No test run configs with ID %s' % request.test_plan_id)
    test_plan_kicker.KickTestPlan(test_plan.key.id())
    # TODO: returns a test plan job object.
    return message_types.VoidMessage()
