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

"""Run hook execution and utilities."""
import logging

from tradefed_cluster.common import IsFinalCommandState

from multitest_transport.models import ndb_models
from multitest_transport.plugins import base as plugins
from multitest_transport.util import tfc_client


def ExecuteHooks(test_run_id, phase, attempt_id=None):
  """Execute all hooks configured for a specific phase."""
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    return
  latest_attempt = _GetLatestAttempt(test_run, attempt_id)
  hook_context = plugins.TestRunHookContext(
      test_run=test_run, latest_attempt=latest_attempt, phase=phase)
  for hook_config in test_run.hook_configs:
    if phase in hook_config.phases:
      _ExecuteHook(hook_config, hook_context)


def _GetLatestAttempt(test_run, attempt_id):
  """Fetch a specific attempt or the latest finished attempt."""
  if not test_run.request_id:
    return None  # No TFC request created (no attempts to fetch)
  if attempt_id:
    # Fetch specific attempt (should also always be the latest attempt)
    return tfc_client.GetAttempt(test_run.request_id, attempt_id)
  # Fetch latest finished attempt if ID not specified
  request = tfc_client.GetRequest(test_run.request_id)
  attempts = reversed(request.command_attempts or [])
  return next((a for a in attempts if IsFinalCommandState(a.state)), None)


def _ExecuteHook(hook_config, hook_context):
  """Construct a hook instance and execute it."""
  try:
    hook_cls = plugins.GetTestRunHookClass(hook_config.hook_name)
    options = ndb_models.NameValuePair.ToDict(hook_config.options)
    hook = hook_cls(**options)
    hook.Execute(hook_context)
  except Exception as e:      logging.error('Failed to execute hook %s: %s', hook_config, e)
