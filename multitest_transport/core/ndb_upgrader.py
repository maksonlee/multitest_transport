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

"""Updates the ndb data for the host when starting the application.

Important: Updates should be lossless when possible in order to ensure backwards
compatibility (i.e. add data only, avoid deleting or editing data).
"""

import logging

from multitest_transport.models import ndb_models

# Database version numbers are formatted as {release number}{update number}.
# For example, 12001 means update 001 for R12.
CURRENT_NDB_VERSION = 25001  # Should match the latest version number
DEFAULT_NDB_VERSION = 25000  # Version number if no host version is found

# Stores the mapping of version numbers to the next update to apply
# e.g. [12000] -> Update12001 means if the current host ndb version is 12000,
#      then run Update12001.
UPDATE_FUNCTION_MAP = {}


def UpgradeNdb():
  """Update the host's ATS ndb."""

  host_ndb_version = (ndb_models.GetPrivateNodeConfig().ndb_version or
                      DEFAULT_NDB_VERSION)
  logging.info('Checking for ndb updates. Current ndb version: %s',
               host_ndb_version)

  while host_ndb_version in UPDATE_FUNCTION_MAP:
    # Find and apply update
    next_update = UPDATE_FUNCTION_MAP[host_ndb_version]
    next_update()
    host_ndb_version = ndb_models.GetPrivateNodeConfig().ndb_version

  logging.info('No more ndb updates. Current ndb version: %s',
               host_ndb_version)


def VersionUpdater(update_version, previous_version):
  """Updates the host ndb version after an update has been applied."""
  def VersionUpdaterDecorator(func):
    def Wrapper():
      # Call original function
      logging.info('Updating ndb to version %s...', update_version)
      func()

      # Update version number
      private_node_config = ndb_models.GetPrivateNodeConfig()
      private_node_config.ndb_version = update_version
      private_node_config.put()
      logging.info('Ndb update %s completed.', update_version)

    # Map version number to update function
    UPDATE_FUNCTION_MAP[previous_version] = Wrapper
    return Wrapper
  return VersionUpdaterDecorator


# Update functions (names should be formatted as 'Update#####')
@VersionUpdater(25001, 25000)
def Update25001():
  """b/204861475: Convert test plans to use test run sequences."""
  query = ndb_models.TestPlan.query()
  test_plans = query.fetch()
  for test_plan in test_plans:
    logging.info('Updating test plan %s.', test_plan.name)
    test_plan.test_run_sequences = []
    for config in test_plan.test_run_configs:
      test_plan.test_run_sequences.append(
          ndb_models.TestRunConfigList(test_run_configs=[config]))
    test_plan.put()
    logging.info('Updated test plan %s.', test_plan.name)


# Helper functions
def _TestResourcePipeToObj(pipe):
  """Converts a TestResourcePipe to a TestResourceObj."""
  return ndb_models.TestResourceObj(name=pipe.name,
                                    url=pipe.url,
                                    test_resource_type=pipe.test_resource_type)
