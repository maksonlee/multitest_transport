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

from multitest_transport import plugins
from multitest_transport.models import ndb_models


def ExecuteHooks(test_run_id, phase):
  """Execute all hooks configured for a specific phase."""
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    return
  for hook_config in test_run.hook_configs:
    if phase in hook_config.phases:
      _ExecuteHook(test_run, phase, hook_config)


def _ExecuteHook(test_run, phase, hook_config):
  """Construct a hook instance and execute it."""
  try:
    hook_cls = plugins.GetTestRunHookClass(hook_config.hook_name)
    options = ndb_models.NameValuePair.ToDict(hook_config.options)
    hook = hook_cls(**options)
    hook.Execute(test_run, phase)
  except Exception as e:      logging.error('Failed to execute hook %s: %s', hook_config, e)
