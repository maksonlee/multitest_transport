# Copyright 2020 Google LLC
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

"""Unit tests for event_log."""
from absl.testing import absltest
from tradefed_cluster import testbed_dependent_test
from tradefed_cluster.util import ndb_shim as ndb


from multitest_transport.models import event_log
from multitest_transport.models import ndb_models


class EventLogTest(testbed_dependent_test.TestbedDependentTest):

  def _VerifyEntry(self, actual, level, message):
    """Verifies a log entry's level and message."""
    self.assertEqual(actual.level, level)
    self.assertEqual(actual.message, message)

  def testGetKey(self):
    """Tests that entity and keys can both be processed."""
    test_run = ndb_models.TestRun(id='test_run_id')
    self.assertIsNone(event_log._GetKey(None))
    self.assertEqual(event_log._GetKey(test_run.key), test_run.key)
    self.assertEqual(event_log._GetKey(test_run), test_run.key)

  def testLog_level(self):
    """Tests that log entries with different levels can be written."""
    event_log.Info(None, 'info message')
    event_log.Warn(None, 'warn message')
    event_log.Error(None, 'error message')

    # Can retrieve log entries
    entries = event_log.GetEntries()
    self.assertLen(entries, 3)
    self._VerifyEntry(entries[0], ndb_models.EventLogLevel.INFO, 'info message')
    self._VerifyEntry(entries[1], ndb_models.EventLogLevel.WARNING,
                      'warn message')
    self._VerifyEntry(entries[2], ndb_models.EventLogLevel.ERROR,
                      'error message')

  def testLog_entity(self):
    """Tests that log entries can be written and retrieved per entity."""
    test_run = ndb_models.TestRun(id='test_run_id')  # Actual entity
    system_key = ndb.Key('System', 1)  # Fake 'system' entity
    event_log.Info(test_run, 'entity message')
    event_log.Info(system_key, 'system message')

    # Can retrieve entity log entries
    entity_entries = event_log.GetEntries(test_run)
    self.assertLen(entity_entries, 1)
    self._VerifyEntry(entity_entries[0], ndb_models.EventLogLevel.INFO,
                      'entity message')

    # Can retrieve system log entries
    system_entries = event_log.GetEntries(system_key)
    self.assertLen(system_entries, 1)
    self._VerifyEntry(system_entries[0], ndb_models.EventLogLevel.INFO,
                      'system message')


if __name__ == '__main__':
  absltest.main()
