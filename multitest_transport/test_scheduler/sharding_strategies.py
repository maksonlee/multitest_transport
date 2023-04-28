# Copyright 2023 Google LLC
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

"""Sharding strategies."""
import string
import more_itertools

from multitest_transport.models import ndb_models
from multitest_transport.util import file_util
from tradefed_cluster import api_messages

# Large modules that should be kept separate from other modules.
LARGE_MODULES = frozenset([
    'CtsDeqpTestCases',
    'CtsAutoFillServiceTestCases',
    'CtsMediaStressTestCases',
    'CtsSecurityTestCases',
    'CtsVideoTestCases',
    'CtsKeystoreWycheproofTestCases',
    'CtsCameraTestCases',
    'CtsWindowManagerDeviceTestCases',
    'CtsLibcoreOjTestCases',
    'CtsInstallHostTestCases',
])


def ShardModules(
    test_run: ndb_models.TestRun,
    command_line: str,
    test_bench: api_messages.TestBenchRequirement,
    max_command: int = 500,
) -> list[api_messages.CommandInfo]:
  """Shards modules to a list of CommandInfos."""
  command_infos = []

  test_package_urls = [
      r.cache_url
      for r in test_run.test_resources
      if r.test_resource_type == ndb_models.TestResourceType.TEST_PACKAGE
  ]
  # get module infos
  module_infos = file_util.GetTestModuleInfos(
      file_util.OpenFile(test_package_urls[0]),
      test_run.test.module_config_pattern,
  )
  tmpl = string.Template(test_run.test.module_execution_args)
  ordered_module_groups = []
  rest_module_infos = []
  for info in sorted(module_infos, key=lambda x: x.name):
    if info.name in LARGE_MODULES:
      ordered_module_groups.append([info])
    else:
      rest_module_infos.append(info)
  command_limit = max_command - len(ordered_module_groups)
  ordered_module_groups += more_itertools.divide(
      min(command_limit, len(rest_module_infos)), rest_module_infos
  )
  for infos in ordered_module_groups:
    names = [info.name for info in infos]
    module_args = ' '.join(
        [tmpl.safe_substitute({'MODULE_NAME': name}) for name in names]
    )
    command_info = api_messages.CommandInfo(
        name=' '.join(names),
        command_line=f'{command_line} {module_args}',
        test_bench=test_bench,
        run_count=test_run.test_run_config.run_count,
        shard_count=1,
        allow_partial_device_match=(
            test_run.test_run_config.allow_partial_device_match
        ),
    )
    command_infos.append(command_info)
  return command_infos
