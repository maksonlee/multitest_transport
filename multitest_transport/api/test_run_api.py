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

"""A module to provide test run APIs."""
import logging
import zipfile
import google3

import cloudstorage as gcs
from protorpc import message_types
from protorpc import messages
from protorpc import protojson
from protorpc import remote
from tradefed_cluster import datastore_util
from tradefed_cluster.common import IsFinalCommandState

from google.appengine.api import urlfetch
from google.appengine.ext import ndb
from google3.third_party.apphosting.python.endpoints.v1_1 import endpoints

from multitest_transport.api import base
from multitest_transport.models import build
from multitest_transport.models import messages as mtt_messages
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import test_kicker
from multitest_transport.test_scheduler import test_run_manager
from multitest_transport.util import env
from multitest_transport.util import file_util
from multitest_transport.util import tfc_client


@base.MTT_API.api_class(resource_name='test_run', path='test_runs')
class TestRunApi(remote.Service):
  """A handler for Test Run API."""

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          max_results=messages.IntegerField(
              1, default=base.DEFAULT_MAX_RESULTS),
          page_token=messages.StringField(2),
          backwards=messages.BooleanField(3),
          labels=messages.StringField(4, repeated=True),
          test=messages.StringField(5),
          run_target=messages.StringField(6),
          state=messages.EnumField(ndb_models.TestRunState, 7, repeated=True),
          device_build_id=messages.StringField(8),
          test_package_info=messages.StringField(9),
          filter_query=messages.StringField(10, repeated=True)),
      mtt_messages.TestRunSummaryList,
      path='/test_runs',
      http_method='GET',
      name='list')
  def ListSummaries(self, request):
    """Returns a list of test run summaries.

    test, run_target, state, device_build_id, and test_package_info filters are
    applied only to their corresponding fields. Each value in filter_query gets
    applied to all columns.

    Args:
      request: an API request object.
    Returns:
      a mtt_messages.TestRunSummaryList object.
    """
    query = ndb_models.TestRunSummary.query().order(
        -ndb_models.TestRunSummary.create_time, ndb_models.TestRunSummary.key)
    query = self._ApplyFilters(query, request)
    test_runs, prev_cursor, next_cursor = datastore_util.FetchPage(
        query, request.max_results, page_cursor=request.page_token,
        backwards=request.backwards)
    return mtt_messages.TestRunSummaryList(
        test_runs=mtt_messages.Convert(test_runs, mtt_messages.TestRunSummary),
        prev_page_token=prev_cursor,
        next_page_token=next_cursor)

  def _ApplyFilters(self, query, request):
    """Applies filters on a test run query."""

    if request.labels:
      for label in request.labels:
        query = query.filter(ndb_models.TestRunSummary.labels == label)

    if request.test:
      query = query.filter(ndb_models.TestRunSummary.test_name == request.test)

    if request.state:
      query = query.filter(
          ndb_models.TestRunSummary.state.IN(request.state))

    if request.run_target:
      query = query.filter(
          ndb_models.TestRunSummary.run_target == request.run_target)

    if request.device_build_id:
      filter_data = request.device_build_id.split(';')
      query = query.filter(
          ndb_models.TestRunSummary.test_devices.build_id.IN(filter_data))

    if request.test_package_info:
      filter_data = request.test_package_info.split()
      query = query.filter(
          ndb_models.TestRunSummary.test_package_info.name == filter_data[0] and
          ndb_models.TestRunSummary.test_package_info.version == filter_data[1])

    for value in request.filter_query:
      query = self._ApplyFilterQuery(query, value)

    return query

  def _ApplyFilterQuery(self, query, value):
    """Applies a single filter value to multiple columns."""
    if not value:
      return query
    return query.filter(
        ndb.OR(ndb_models.TestRunSummary.labels == value,
               ndb_models.TestRunSummary.test_name == value,
               ndb_models.TestRunSummary.run_target == value,
               ndb_models.TestRunSummary.test_devices.build_id == value,
               ndb_models.TestRunSummary.test_devices.product == value,
               ndb_models.TestRunSummary.test_package_info.name == value,
               ndb_models.TestRunSummary.test_package_info.version == value))

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_run_id=messages.StringField(1, required=True)),
      mtt_messages.TestRun, path='{test_run_id}', http_method='GET',
      name='get')
  def Get(self, request):
    """Returns a test run.

    Args:
      request: an API request object.
    Returns:
      a mtt_messages.TestRun object.
    Raises:
      endpoints.NotFoundException: if a give test run ID doesn't exist.
    """
    test_run = ndb_models.TestRun.get_by_id(request.test_run_id)
    if not test_run:
      raise endpoints.NotFoundException(
          'no test run found for ID %s' % request.test_run_id)
    return mtt_messages.Convert(test_run, mtt_messages.TestRun)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_run_id=messages.StringField(1, required=True),
          page_token=messages.StringField(2),
          max_results=messages.IntegerField(
              3, default=base.DEFAULT_MAX_RESULTS)),
      mtt_messages.TestArtifactList, path='{test_run_id}/test_artifacts',
      http_method='GET', name='test_artifact.list')
  def ListTestArtifacts(self, request):
    """Returns a list of test artifacts for a test run.

    Args:
      request: an API request object.
    Returns:
      a mtt_messages.TestArtifactList object.
    """
    test_run = ndb_models.TestRun.get_by_id(request.test_run_id)
    if not test_run:
      raise endpoints.NotFoundException(
          'No test run found for ID %s' % request.test_run_id)
    test_artifacts = []
    next_page_token = None
    if test_run.output_path:
      urlfetch.set_default_fetch_deadline(env.GCS_FETCH_DEADLINE_SECONDS)
      objs = gcs.listbucket(
          test_run.output_path, marker=request.page_token,
          max_keys=request.max_results)
      test_artifacts = [
          mtt_messages.TestArtifact(
              name=obj.filename.split('/')[-1],
              path=obj.filename,
              download_url='/gcs_proxy%s' % obj.filename,
              size=obj.st_size)
          for obj in objs
      ]
      next_page_token = (
          test_artifacts[-1].path
          if len(test_artifacts) == request.max_results else None)

    return mtt_messages.TestArtifactList(
        test_artifacts=test_artifacts, next_page_token=next_page_token)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(mtt_messages.NewTestRunRequest),
      mtt_messages.TestRun, path='/test_runs', http_method='POST',
      name='new')
  def New(self, request):
    """Creates a new test run.

    Args:
      request: an API request object.
    Returns:
      a mtt_messages.TestRun object.
    """
    labels = request.labels
    test_run_config = mtt_messages.Convert(
        request.test_run_config, ndb_models.TestRunConfig)

    test_resource_objs = build.FindTestResources(request.test_resource_pipes)

    # start test run
    test_run = test_kicker.CreateTestRun(
        labels=labels,
        test_run_config=test_run_config,
        test_resources=test_resource_objs,
        rerun_context=request.rerun_context)
    return mtt_messages.Convert(test_run, mtt_messages.TestRun)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_run_id=messages.StringField(1, required=True)),
      message_types.VoidMessage,
      path='{test_run_id}/cancel',
      http_method='POST',
      name='cancel')
  def Cancel(self, request):
    """Cancels a test run.

    Args:
      request: an API request object.
    Returns:
      a void message.
    """
    try:
      test_run_manager.SetTestRunState(
          test_run_id=request.test_run_id,
          state=ndb_models.TestRunState.CANCELED)
    except test_run_manager.TestRunNotFoundError:
      raise endpoints.NotFoundException(
          'No test run found for ID %s' % request.test_run_id)
    return message_types.VoidMessage()

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_run_id=messages.StringField(1, required=True),
          attempt_id=messages.StringField(2, required=True),
          path=messages.StringField(3, required=True),
          offset=messages.IntegerField(4),
          length=messages.IntegerField(5, default=25 * 1024)),
      mtt_messages.FileSegment,
      path='{test_run_id}/output',
      http_method='GET',
      name='output')
  def TailOutputFile(self, request):
    # find test run
    test_run = ndb_models.TestRun.get_by_id(request.test_run_id)
    if not test_run:
      raise endpoints.NotFoundException(
          'Test run %s not found' % request.test_run_id)

    # get attempt and check whether it is active
    attempt = tfc_client.GetAttempt(test_run.request_id, request.attempt_id)
    if attempt is None:
      raise endpoints.NotFoundException(
          'Command attempt %s not found' % request.attempt_id)

    # determine file URL
    if IsFinalCommandState(attempt.state):
      file_url = file_util.GetOutputFileUrl(test_run, attempt, request.path)
    else:
      file_url = file_util.GetWorkFileUrl(attempt, request.path)

    # read file contents
    if request.offset is None:
      # no offset given, fetch from end of file up to length limit
      file_segment = file_util.TailFile(file_url, length=request.length)
    else:
      # offset provided, fetch bytes from offset up to length limit
      file_segment = file_util.ReadFile(file_url,
                                        offset=request.offset,
                                        length=request.length)
    if file_segment is None:
      raise endpoints.NotFoundException('File %s not found' % request.path)
    return mtt_messages.Convert(file_segment, mtt_messages.FileSegment)

  @base.convert_exception
  @endpoints.method(
      endpoints.ResourceContainer(
          message_types.VoidMessage,
          test_run_id=messages.StringField(1, required=True)),
      mtt_messages.TestRunMetadataList,
      path='{test_run_id}/metadata', http_method='GET', name='metadata')
  def GetMetadata(self, request):
    """Returns a test run's metadata."""
    test_run = ndb_models.TestRun.get_by_id(request.test_run_id)
    if not test_run:
      raise endpoints.NotFoundException(
          'No test run found for ID %s' % request.test_run_id)
    return mtt_messages.TestRunMetadataList(
        test_runs=self._GetMetadataList(test_run))

  def _GetMetadataList(self, test_run):
    """Return a list containing a test run and all of its ancestors."""
    test_runs = []
    while test_run:
      test_runs.append(self._GetMetadata(test_run))
      if not test_run.IsRerun():
        break  # no more test runs to append
      if test_run.IsRemoteRerun():
        # remaining test run metadata is in the previous context
        context_file = test_run.GetRerunContextFile()
        if context_file:
          context_file_handle = file_util.FileHandle.Get(context_file.url)
          test_runs.extend(
              self._LoadMetadataFromContextFile(context_file_handle))
        break
      test_run = test_run.prev_test_run_key.get()
    return test_runs

  def _GetMetadata(self, test_run):
    """Get the metadata for a test run."""
    completed_attempts = []
    if test_run.request_id:
      request = tfc_client.GetRequest(test_run.request_id)
      attempts = request.command_attempts or []
      completed_attempts = [attempt for attempt in attempts
                            if IsFinalCommandState(attempt.state)]

    return mtt_messages.TestRunMetadata(
        test_run=mtt_messages.Convert(test_run, mtt_messages.TestRun),
        command_attempts=completed_attempts)

  def _LoadMetadataFromContextFile(self, file_handle):
    """Parse metadata from a context file."""
    try:
      zf = zipfile.ZipFile(file_handle)
      metadata_file = zf.NameToInfo.get(test_kicker.METADATA_FILE)
      if not metadata_file:
        logging.warn('Metadata file not found')
        return []  # ignore file not found
      metadata_list = protojson.decode_message(mtt_messages.TestRunMetadataList,
                                               zf.read(metadata_file))
      # TODO: last command attempt is missing
      return metadata_list.test_runs
    except Exception as e:        logging.error('Failed to read remote metadata: %s', e)
      return []
