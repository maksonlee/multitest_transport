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

"""A module to process TFC events."""
import datetime
import json
import logging

from protorpc import protojson
from tradefed_cluster import api_messages
from tradefed_cluster import common
import webapp2

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from multitest_transport.models import event_log
from multitest_transport.models import ndb_models
from multitest_transport.models import test_run_hook
from multitest_transport.util import analytics
from multitest_transport.util import file_util
from multitest_transport.util import tfc_client

TEST_RUN_STATE_MAP = {
    api_messages.RequestState.UNKNOWN: ndb_models.TestRunState.UNKNOWN,
    api_messages.RequestState.QUEUED: ndb_models.TestRunState.QUEUED,
    api_messages.RequestState.RUNNING: ndb_models.TestRunState.RUNNING,
    api_messages.RequestState.CANCELED: ndb_models.TestRunState.CANCELED,
    api_messages.RequestState.COMPLETED: ndb_models.TestRunState.COMPLETED,
    api_messages.RequestState.ERROR: ndb_models.TestRunState.ERROR,
}


@ndb.transactional()
def _AfterTestRunHandler(test_run):
  """Performs after test run tasks.

  After a test run is in one of the final states, MTT needs to do the following:
    Save the final test context.
    Invoke after run hooks.
    Schedule a job to upload test output files.
    Record test run metrics.

  Args:
    test_run: a ndb_models.TestRun object.
  """
  test_run.is_finalized = True  # Mark post-run handlers as completed

  # Query and store next test context
  if test_run.request_id:
    tfc_test_context = _GetTestContext(test_run.request_id)
    if tfc_test_context:
      test_run.next_test_context = ndb_models.TestContextObj(
          command_line=tfc_test_context.command_line,
          env_vars=[
              ndb_models.NameValuePair(name=p.key, value=p.value)
              for p in tfc_test_context.env_vars
          ],
          test_resources=[
              ndb_models.TestResourceObj(name=r.name, url=r.url)
              for r in tfc_test_context.test_resources
          ])
      logging.debug(
          'Setting the next_test_context = %s', test_run.next_test_context)
  test_run.put()

  # Invoke after run hooks
  if test_run.state == ndb_models.TestRunState.COMPLETED:
    deferred.defer(test_run_hook.ExecuteHooks, test_run.key.id(),
                   ndb_models.TestRunPhase.ON_SUCCESS, _transactional=True)
  elif test_run.state == ndb_models.TestRunState.ERROR:
    deferred.defer(test_run_hook.ExecuteHooks, test_run.key.id(),
                   ndb_models.TestRunPhase.ON_ERROR, _transactional=True)
  deferred.defer(test_run_hook.ExecuteHooks, test_run.key.id(),
                 ndb_models.TestRunPhase.AFTER_RUN, _transactional=True)

  # Record metrics
  deferred.defer(_TrackTestRun, test_run.key.id(), _transactional=True)

  # Log final state
  deferred.defer(event_log.Info, test_run.key, 'Test run reached final state',
                 _transactional=True)


def ProcessRequestEvent(message):
  """Process a TFC request state change event message.

  Args:
    message: an api_messages.RequestEventMessage object.
  """
  request_id = message.request_id
  test_run = _GetTestRunToUpdate(request_id, message)
  if test_run:
    _ProcessRequestEvent(test_run.key.id(), message)


@ndb.transactional()
def _ProcessRequestEvent(test_run_id, message):
  """Process a TFC request state change event message."""
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    return

  # Update test run information
  test_run.update_time = message.event_time
  if not test_run.IsFinal():
    test_run.state = TEST_RUN_STATE_MAP.get(
        message.new_state, ndb_models.TestRunState.UNKNOWN)
  if not test_run.test.result_file:
    # No test results file to parse, use partial test counts
    test_run.total_test_count = (message.failed_test_count +
                                 message.passed_test_count)
    test_run.failed_test_count = message.failed_test_count
    test_run.failed_test_run_count = message.failed_test_run_count
  test_run.cancel_reason =\
    message.request.cancel_reason if message.request is not None else None
  test_run.put()

  if test_run.IsFinal() and not test_run.is_finalized:
    _AfterTestRunHandler(test_run)


def ProcessCommandAttemptEvent(message):
  """Process a TFC attempt state change event message.

  Args:
    message: an api_messages.CommandAttemptEventMessage object.
  """
  test_run = _GetTestRunToUpdate(message.attempt.request_id, message)
  if test_run:
    _ProcessCommandAttemptEvent(test_run.key.id(), message)


@ndb.transactional()
def _ProcessCommandAttemptEvent(test_run_id, message):
  """Process a TFC attempt state change event message."""
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    return

  # Update test run information
  attempt = message.attempt
  test_run.update_time = message.event_time
  test_run.test_devices = _GetTestDeviceInfos(attempt.device_serials)
  summary = _GetXtsTestResultSummary(test_run, attempt)
  if summary:
    # Successfully parsed test results file, update test counts
    test_run.total_test_count = summary.passed + summary.failed
    test_run.failed_test_count = summary.failed
    test_run.failed_test_run_count = (
        summary.modules_total - summary.modules_done)
  test_run.put()

  # Invoke after attempt hooks
  if common.IsFinalCommandState(attempt.state) and not test_run.is_finalized:
    deferred.defer(test_run_hook.ExecuteHooks, test_run_id,
                   ndb_models.TestRunPhase.AFTER_ATTEMPT,
                   attempt_id=attempt.attempt_id, _transactional=True)


def _GetTestContext(request_id):
  """Retrieve the TFC test context for a request."""
  request = tfc_client.GetRequest(request_id)
  # TODO: merge test contexts if there is more than one.
  if request.commands:
    return tfc_client.GetTestContext(request.id, request.commands[0].id)
  return None


def _TrackTestRun(test_run_id):
  """Generate and send test run analytics information after completion."""
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    return
  package = test_run.test_package_info
  duration = _GetCurrentTime() - test_run.create_time

  device_count = None
  attempt_count = None
  if test_run.request_id:
    request = tfc_client.GetRequest(test_run.request_id)
    attempts = request.command_attempts
    if attempts:
      device_count = max(len(a.device_serials or []) for a in attempts)
      attempt_count = len(attempts)

  analytics.Log(analytics.TEST_RUN_CATEGORY, analytics.END_ACTION,
                test_name=package.name if package else None,
                test_version=package.version if package else None,
                state=test_run.state,
                duration_seconds=int(duration.total_seconds()),
                device_count=device_count,
                attempt_count=attempt_count,
                is_rerun=test_run.prev_test_run_key is not None,
                failed_module_count=test_run.failed_test_run_count,
                test_count=test_run.total_test_count,
                failed_test_count=test_run.failed_test_count)


def _GetCurrentTime():
  """Return current time, visible for testing."""
  return datetime.datetime.now()


def _GetTestRunToUpdate(request_id, message):
  """Retrieve the associated test run if it exists and should be updated."""
  query = ndb_models.TestRun.query(ndb_models.TestRun.request_id == request_id)
  test_run_key = query.get(keys_only=True)
  if not test_run_key:
    logging.warn('Cannot find test run for request %s', request_id)
    return None

  test_run = test_run_key.get(use_cache=False, use_memcache=False)
  if message.event_time < test_run.update_time:
    logging.warn(
        'Event timestamp too old (%s < %s); skipping message: %s',
        message.event_time, test_run.update_time, message)
    return None

  return test_run


def _GetTestDeviceInfos(device_serials):
  """Retrieve information about the test devices."""
  device_infos = []
  for serial in device_serials:
    device = tfc_client.GetDeviceInfo(serial)
    if device:
      device_info = ndb_models.TestDeviceInfo(
          device_serial=device.device_serial,
          hostname=device.hostname,
          run_target=device.run_target,
          build_id=device.build_id,
          product=device.product,
          sdk_version=device.sdk_version)
      device_infos.append(device_info)
    else:
      logging.exception('Device %s not found', serial)
  return device_infos


def _GetXtsTestResultSummary(test_run, attempt):
  """Retrieve the test result summary for a test run and attempt."""
  if not common.IsFinalCommandState(attempt.state):
    return None

  result_file = test_run.test.result_file
  if not result_file:
    return None

  url = file_util.GetOutputFileUrl(test_run, attempt, result_file)
  file_handle = file_util.FileHandle.Get(url)
  return file_util.GetXtsTestResultSummary(file_handle)


# Event message classes and handlers
_EVENT_HANDLERS = {
    common.ObjectEventType.COMMAND_ATTEMPT_STATE_CHANGED: (
        api_messages.CommandAttemptEventMessage, ProcessCommandAttemptEvent),
    common.ObjectEventType.REQUEST_STATE_CHANGED: (
        api_messages.RequestEventMessage, ProcessRequestEvent)
}


class TaskHandler(webapp2.RequestHandler):
  """A web request handler to handle tasks from the test kicker queue."""

  def post(self):
    """Process a TFC event message."""
    message_type = json.loads(self.request.body).get('type')
    message_cls, handler = _EVENT_HANDLERS[message_type]
    if not message_cls or not handler:
      raise ValueError('Unknown TFC event type %s' % message_type)
    message = protojson.decode_message(message_cls, self.request.body)
    handler(message)


APP = webapp2.WSGIApplication([
    ('.*', TaskHandler),
], debug=True)
