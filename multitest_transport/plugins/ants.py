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

"""Android test storage result reporting hook."""
import logging
import apiclient
import httplib2

from tradefed_cluster import api_messages

from multitest_transport.models import ndb_models
from multitest_transport.plugins import base
from multitest_transport.plugins import constant
from multitest_transport.util import env

OAUTH2_SCOPES = ['https://www.googleapis.com/auth/androidbuild.internal']
ANDROID_BUILD_API_NAME = 'androidbuildinternal'
ANDROID_BUILD_API_VERSION = 'v3'

SCHEDULER = 'MTT'
INVOCATION_ID = 'ants_invocation_id'
WORK_UNIT_ID = 'ants_work_unit_id'

# Maps test run states to AnTS scheduler states
TEST_RUN_STATE_MAP = {
    ndb_models.TestRunState.UNKNOWN: 'SCHEDULER_STATE_UNSPECIFIED',
    ndb_models.TestRunState.PENDING: 'PENDING',
    ndb_models.TestRunState.QUEUED: 'QUEUED',
    ndb_models.TestRunState.RUNNING: 'RUNNING',
    ndb_models.TestRunState.COMPLETED: 'COMPLETED',
    ndb_models.TestRunState.CANCELED: 'CANCELLED',
    ndb_models.TestRunState.ERROR: 'ERROR',
}

# Maps attempt states to AnTS work unit states
ATTEMPT_STATE_MAP = {
    api_messages.CommandState.UNKNOWN: 'SCHEDULER_STATE_UNSPECIFIED',
    api_messages.CommandState.QUEUED: 'QUEUED',
    api_messages.CommandState.RUNNING: 'RUNNING',
    api_messages.CommandState.CANCELED: 'CANCELLED',
    api_messages.CommandState.COMPLETED: 'COMPLETED',
    api_messages.CommandState.ERROR: 'ERROR',
    api_messages.CommandState.FATAL: 'ERROR',
}


class AntsHook(base.TestRunHook):
  """Hook which uploads results to AnTS."""
  name = 'AnTS'
  oauth2_config = base.OAuth2Config(
      client_id=env.GOOGLE_OAUTH2_CLIENT_ID,
      client_secret=env.GOOGLE_OAUTH2_CLIENT_SECRET,
      scopes=OAUTH2_SCOPES)

  def __init__(self, _credentials=None, build_id=None, build_target=None, **_):      self._credentials = _credentials
    self.build_id = build_id
    self.build_target = build_target

  def _GetClient(self):
    """Initializes an Android Build client."""
    http = httplib2.Http(timeout=constant.HTTP_TIMEOUT_SECONDS)
    if self._credentials:
      http = self._credentials.authorize(http)
    return apiclient.discovery.build(
        ANDROID_BUILD_API_NAME,
        ANDROID_BUILD_API_VERSION,
        http=http,
        developerKey=env.GOOGLE_API_KEY)

  def Execute(self, context):
    """Create or update AnTS invocation and work units."""
    if context.phase == ndb_models.TestRunPhase.BEFORE_RUN:
      self._CreateInvocation(context.test_run)
    if context.phase == ndb_models.TestRunPhase.BEFORE_ATTEMPT:
      self._CreateWorkUnit(context.test_run, context.next_task)
    if context.phase == ndb_models.TestRunPhase.AFTER_ATTEMPT:
      self._UpdateWorkUnit(context.test_run, context.latest_attempt)
    elif context.phase == ndb_models.TestRunPhase.AFTER_RUN:
      self._UpdateInvocation(context.test_run)

  def _CreateInvocation(self, test_run):
    """Creates a new AnTS invocation and stores its ID."""
    if test_run.hook_data.get(INVOCATION_ID):
      return  # Invocation already created

    # TODO: Parse build ID and target from test resources
    # TODO: Add invocation metadata (test name, labels, properties)
    response = self._GetClient().invocation().insert(
        body={
            'primaryBuild': {
                'buildId': self.build_id,
                'buildTarget': self.build_target,
            },
            'scheduler': SCHEDULER,
        }).execute(num_retries=constant.NUM_RETRIES)
    invocation_id = response['invocationId']
    logging.info('Created AnTS invocation %s', invocation_id)

    # Store invocation ID
    test_run.hook_data[INVOCATION_ID] = invocation_id
    test_run.put()

  def _CreateWorkUnit(self, test_run, task):
    """Creates a new AnTS work unit and injects it into the task."""
    invocation_id = test_run.hook_data[INVOCATION_ID]

    response = self._GetClient().workunit().insert(body={
        'invocationId': invocation_id,
    }).execute(num_retries=constant.NUM_RETRIES)
    work_unit_id = response['id']
    logging.info('Created AnTS work unit %s', work_unit_id)

    # Store work unit ID
    test_run.hook_data[WORK_UNIT_ID] = work_unit_id
    test_run.put()

    # Pass build and AnTS information to runner
    task.extra_options.setdefault('cluster:build-id', []).append(self.build_id)
    task.extra_options.setdefault('cluster:build-target',
                                  []).append(self.build_target)
    task.extra_options.setdefault('invocation-data', []).extend(
        ['invocation_id=%s' % invocation_id,
         'work_unit_id=%s' % work_unit_id])

  def _UpdateWorkUnit(self, test_run, attempt):
    """Updates an existing AnTS work unit to a final state."""
    work_unit_id = test_run.hook_data[WORK_UNIT_ID]
    client = self._GetClient()
    state = ATTEMPT_STATE_MAP[attempt.state]

    work_unit = client.workunit().get(resourceId=work_unit_id).execute(
        num_retries=constant.NUM_RETRIES)
    work_unit['state'] = state
    client.workunit().update(
        resourceId=work_unit_id,
        body=work_unit).execute(num_retries=constant.NUM_RETRIES)
    logging.info('Updated AnTS work unit %s to %s', work_unit_id, state)

  def _UpdateInvocation(self, test_run):
    """Updates an existing AnTS invocation to a final state."""
    invocation_id = test_run.hook_data[INVOCATION_ID]
    client = self._GetClient()
    state = TEST_RUN_STATE_MAP[test_run.state]

    invocation = client.invocation().get(resourceId=invocation_id).execute(
        num_retries=constant.NUM_RETRIES)
    invocation['schedulerState'] = state
    client.invocation().update(
        resourceId=invocation_id,
        body=invocation).execute(num_retries=constant.NUM_RETRIES)
    logging.info('Updated AnTS invocation %s to %s', invocation_id, state)
