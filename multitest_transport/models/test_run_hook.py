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

"""Run hook execution and utilities.

Serves as an adapter between test run hooks (which define execution logic) and
actions (which define specific execution parameters).
"""
import logging
import string

from tradefed_cluster import api_messages
from tradefed_cluster.plugins import base as tfc_plugins

from multitest_transport.models import event_log
from multitest_transport.models import ndb_models
from multitest_transport.plugins import base as plugins
from multitest_transport.util import analytics
from multitest_transport.util import tfc_client


def _ApplyOptionsFromDeviceActions(test_run_id, task):
  """Apply the Tradefed options of the device actions before an attempt."""
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    return
  for action in test_run.before_device_actions:
    for tradefed_option in action.tradefed_options:
      task.extra_options.setdefault(tradefed_option.name,
                                    []).extend(tradefed_option.values)


def ExecuteHooks(test_run_id, phase, attempt_id=None, task=None):
  """Execute all hooks configured for a specific phase."""
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    return
  latest_attempt = _GetLatestAttempt(test_run, attempt_id)
  hook_context = plugins.TestRunHookContext(
      test_run=test_run,
      phase=ndb_models.TestRunPhase(phase),
      latest_attempt=latest_attempt,
      next_task=task)
  for action in test_run.test_run_actions:
    if phase in action.phases:
      _ExecuteHook(action, hook_context)


def _GetLatestAttempt(test_run, attempt_id):
  """Fetch a specific attempt or the latest finished attempt."""
  if not test_run.request_id:
    return None  # No TFC request created (no attempts to fetch)
  if attempt_id:
    # Fetch specific attempt (should also always be the latest attempt)
    return tfc_client.GetAttempt(test_run.request_id, attempt_id)
  # Fetch latest finished attempt if ID not specified
  attempts = tfc_client.GetLatestFinishedAttempts(test_run.request_id)
  return attempts[-1] if attempts else None


def _ExecuteHook(action, hook_context):
  """Construct a hook instance and execute it."""
  try:
    hook_cls = plugins.GetTestRunHookClass(action.hook_class_name)
    if hook_cls is None:
      raise ValueError('Cannot find a hook class %s' % action.hook_class_name)
    options = ndb_models.NameValuePair.ToDict(action.options)
    test_run_context = hook_context.test_run.GetContext()
    options = {
        k: string.Template(v).substitute(test_run_context)
        for k, v in options.items()
        if v is not None
    }
    if action.credentials:
      options['_credentials'] = action.credentials
    logging.debug(
        'Executing %s: ctx=%s, options=%s',
        hook_cls, test_run_context, options)
    hook = hook_cls(**options)
    analytics.Log(
        analytics.TEST_RUN_ACTION_CATEGORY,
        analytics.EXECUTE_ACTION,
        label=action.hook_class_name,
        value=int(hook_context.phase))
    hook.Execute(hook_context)
  except Exception as e:      logging.exception('Failed to execute action %s', action)
    event_log.Error(hook_context.test_run,
                    'Test run action \'%s\' failed: %s' % (action.name, e))


def GetOAuth2Config(action):
  """Fetches a hook's OAuth2 configuration."""
  hook_cls = plugins.GetTestRunHookClass(action.hook_class_name)
  return getattr(hook_cls, 'oauth2_config', None) if hook_cls else None


def GetAuthorizationState(action):
  """Determines whether a hook has been authorized."""
  if not GetOAuth2Config(action):
    return ndb_models.AuthorizationState.NOT_APPLICABLE
  if action.credentials:
    return ndb_models.AuthorizationState.AUTHORIZED
  return ndb_models.AuthorizationState.UNAUTHORIZED


class TfcTaskInterceptor(tfc_plugins.Plugin):
  """Intercepts TFC tasks before sending to runner to execute MTT run hooks."""

  def OnCommandTasksLease(self, command_tasks):
    """Executes before attempt hooks."""
    for command_task in command_tasks:
      # Find the relevant test run
      test_run_key = ndb_models.TestRun.query(
          ndb_models.TestRun.request_id == command_task.request_id).get(
              keys_only=True)
      if not test_run_key:
        logging.warn('Cannot find test run for command task %s', command_task)
        continue
      # Invoke before attempt hooks and update command task
      task = self.ConvertCommandTask(command_task)
      _ApplyOptionsFromDeviceActions(test_run_key.id(), task)
      ExecuteHooks(
          test_run_key.id(), ndb_models.TestRunPhase.BEFORE_ATTEMPT, task=task)
      self.UpdateCommandTask(command_task, task)

  def ConvertCommandTask(self, command_task):
    """Convert a TFC command task to a test run task."""
    return plugins.TestRunTask(
        task_id=command_task.task_id,
        command_line=command_task.command_line,
        extra_options=api_messages.KeyMultiValuePairMessagesToMap(
            command_task.extra_options))

  def UpdateCommandTask(self, command_task, task):
    """Apply modifications to a TFC command task."""
    command_task.extra_options = api_messages.MapToKeyMultiValuePairMessages(
        task.extra_options)
