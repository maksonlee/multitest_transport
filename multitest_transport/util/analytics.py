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

"""Utilities for tracking Google Analytics events."""
import json

from tradefed_cluster.services import task_scheduler
from tradefed_cluster import common


# Analytics uploading task queue
QUEUE_NAME = 'analytics-queue'

# GA categories
BUILD_CHANNEL_CATEGORY = 'build_channel'
DEVICE_ACTION_CATEGORY = 'device_action'
SYSTEM_CATEGORY = 'system'
TEST_RUN_ACTION_CATEGORY = 'test_run_action'
TEST_RUN_CATEGORY = 'test_run'
INVOCATION_CATEGORY = 'invocation'

# GA actions
DOWNLOAD_ACTION = 'download'
END_ACTION = 'end'
EXECUTE_ACTION = 'execute'
HEARTBEAT_ACTION = 'heartbeat'
START_ACTION = 'start'
TARGET_PREPARER_ACTION = 'target_preparer'


def Log(category, action, **kwargs):
  """Schedules a task to upload an event to GA."""
  payload = json.dumps(dict(category=category, action=action, **kwargs))
  task_scheduler.AddTask(queue_name=QUEUE_NAME, payload=payload)


def HeartbeatSender():
  """Request handler which periodically logs that this instance is up."""
  Log(SYSTEM_CATEGORY, HEARTBEAT_ACTION)
  return common.HTTP_OK
