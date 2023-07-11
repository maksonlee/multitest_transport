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

"""Unit tests for sharding strategies."""
from unittest import mock
from absl.testing import absltest
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import sharding_strategies
from multitest_transport.util import file_util
from tradefed_cluster import api_messages


class ShardingStrategiesTest(absltest.TestCase):

  def _AssertCommandInfos(
      self,
      names: list[str],
      command_lines: list[str],
      command_infos: list[api_messages.CommandInfo],
      test_bench=None,
      run_count=1,
      shard_count=1,
      allow_partial_device_match=False,
  ):
    for name, command, info in zip(names, command_lines, command_infos):
      self.assertEqual(name, info.name)
      self.assertEqual(command, info.command_line)
      self.assertEqual(test_bench, info.test_bench)
      self.assertEqual(run_count, info.run_count)
      self.assertEqual(shard_count, info.shard_count)
      self.assertEqual(
          allow_partial_device_match, info.allow_partial_device_match
      )

  def setUp(self):
    super().setUp()
    self.test_run = ndb_models.TestRun(
        test=ndb_models.Test(
            name='name',
            command='command',
            module_config_pattern='path/to/.*\\.config',
            module_execution_args='-m ${MODULE_NAME}',
        ),
        test_run_config=ndb_models.TestRunConfig(
            cluster='cluster',
            command='command',
            retry_command='retry_command',
            run_count=1,
            shard_count=6,
        ),
        test_resources=[
            ndb_models.TestResourceObj(
                name='test_package',
                url='test_package_url',
                cache_url='test_package_cache_url',
                test_resource_type=ndb_models.TestResourceType.TEST_PACKAGE,
            )
        ],
    )
    self.test_bench = api_messages.TestBenchRequirement()

  @mock.patch.object(file_util, 'OpenFile', autospec=True)
  @mock.patch.object(file_util, 'GetTestModuleInfos', autospec=True)
  def testShardModules(self, mock_get_test_module_infos, mock_open_file):
    mock_get_test_module_infos.return_value = [
        file_util.TestModuleInfo(name='CtsFooTestCases'),
        file_util.TestModuleInfo(name='CtsBarTestCases'),
        file_util.TestModuleInfo(name='CtsBazTestCases'),
    ]

    command_infos = sharding_strategies.ShardModules(
        self.test_run, 'command', self.test_bench
    )

    self._AssertCommandInfos(
        ['CtsBarTestCases', 'CtsBazTestCases', 'CtsFooTestCases'],
        [
            'command -m CtsBarTestCases',
            'command -m CtsBazTestCases',
            'command -m CtsFooTestCases',
        ],
        command_infos,
        test_bench=self.test_bench,
        shard_count=1,
    )
    mock_open_file.assert_called_with('test_package_cache_url')
    mock_get_test_module_infos.assert_called_with(
        mock_open_file.return_value, 'path/to/.*\\.config'
    )

  @mock.patch.object(file_util, 'OpenFile', autospec=True)
  @mock.patch.object(file_util, 'GetTestModuleInfos', autospec=True)
  def testShardModules_largeModules(self, mock_get_test_module_infos, _):
    mock_get_test_module_infos.return_value = [
        file_util.TestModuleInfo(name='CtsFooTestCases'),
        file_util.TestModuleInfo(name='CtsBarTestCases'),
        file_util.TestModuleInfo(name='CtsMediaStressTestCases'),
    ]

    command_infos = sharding_strategies.ShardModules(
        self.test_run, 'command', self.test_bench
    )

    self._AssertCommandInfos(
        ['CtsMediaStressTestCases', 'CtsBarTestCases', 'CtsFooTestCases'],
        [
            'command -m CtsMediaStressTestCases',
            'command -m CtsBarTestCases',
            'command -m CtsFooTestCases',
        ],
        command_infos,
        test_bench=self.test_bench,
        shard_count=1,
    )

  @mock.patch.object(file_util, 'OpenFile', autospec=True)
  @mock.patch.object(file_util, 'GetTestModuleInfos', autospec=True)
  def testShardModules_exceedMaxCommand(self, mock_get_test_module_infos, _):
    mock_get_test_module_infos.return_value = [
        file_util.TestModuleInfo(name='CtsFooTestCases'),
        file_util.TestModuleInfo(name='CtsBarTestCases'),
        file_util.TestModuleInfo(name='CtsBazTestCases'),
        file_util.TestModuleInfo(name='CtsMediaStressTestCases'),
    ]

    command_infos = sharding_strategies.ShardModules(
        self.test_run, 'command', self.test_bench, 3
    )

    self._AssertCommandInfos(
        [
            'CtsMediaStressTestCases',
            'CtsBarTestCases CtsBazTestCases',
            'CtsFooTestCases',
        ],
        [
            'command -m CtsMediaStressTestCases',
            'command -m CtsBarTestCases -m CtsBazTestCases',
            'command -m CtsFooTestCases',
        ],
        command_infos,
        test_bench=self.test_bench,
        shard_count=1,
    )

  @mock.patch.object(file_util, 'OpenFile', autospec=True)
  @mock.patch.object(file_util, 'GetTestModuleInfos', autospec=True)
  def testShardModules_shardSingleModule(self, mock_get_test_module_infos, _):
    mock_get_test_module_infos.return_value = [
        file_util.TestModuleInfo(name='CtsFooTestCases'),
        file_util.TestModuleInfo(name='CtsBarTestCases'),
        file_util.TestModuleInfo(name='CtsDeqpTestCases'),
    ]
    self.test_run.test_run_config.shard_count = 2

    command_infos = sharding_strategies.ShardModules(
        self.test_run, 'command', self.test_bench, 3
    )

    self._AssertCommandInfos(
        [
            'CtsDeqpTestCases shard 0',
            'CtsDeqpTestCases shard 1',
            'CtsBarTestCases CtsFooTestCases',
        ],
        [
            'command -m CtsDeqpTestCases --shard-count 2 --shard-index 0',
            'command -m CtsDeqpTestCases --shard-count 2 --shard-index 1',
            'command -m CtsBarTestCases -m CtsFooTestCases',
        ],
        command_infos,
        test_bench=self.test_bench,
        shard_count=1,
    )


if __name__ == '__main__':
  absltest.main()
