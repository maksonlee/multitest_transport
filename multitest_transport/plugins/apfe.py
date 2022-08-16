# Copyright 2022 Google LLC
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
"""Android Partner Front End plugins."""
import json
import re

import apiclient
import httplib2

from multitest_transport.models import event_log
from multitest_transport.models import ndb_models
from multitest_transport.plugins import base
from multitest_transport.plugins import constant
from multitest_transport.util import env
from multitest_transport.util import file_util
from multitest_transport.util import oauth2_util

_OAUTH2_SCOPES = ('https://www.googleapis.com/auth/androidPartner',)

_API_NAME = 'androidpartner'
_API_VERSION = 'v1'


class APFEReportUploadHook(base.TestRunHook):
  """Hook which uploads reports to APFE."""
  name = 'APFEReportUploadHook'
  oauth2_config = oauth2_util.OAuth2Config(
      client_id=env.GOOGLE_OAUTH2_CLIENT_ID,
      client_secret=env.GOOGLE_OAUTH2_CLIENT_SECRET,
      scopes=list(_OAUTH2_SCOPES))

  def __init__(self, _credentials=None, company_id=None, **_):      if not company_id:
      raise ValueError('Company id is required')

    self._authorized_http = None
    self._client = None
    self._credentials = _credentials
    self.company_id = company_id

  def _GetHttp(self):
    """Initializes an authorized http objcet if necessary."""
    if not self._authorized_http:
      http = httplib2.Http(timeout=constant.HTTP_TIMEOUT_SECONDS)
      self._authorized_http = oauth2_util.AuthorizeHttp(
          http, self._credentials, scopes=list(_OAUTH2_SCOPES))

    return self._authorized_http

  def _GetClient(self):
    """Initializes an APFE client if necessary."""
    if not self._client:
      # Discovery api does not accept credentials
      self._client = apiclient.discovery.build(
          _API_NAME,
          _API_VERSION,
          # Use raw model as the response of media api is not json
          model=apiclient.model.RawModel(),
      )

    return self._client

  def Execute(self, context):
    if context.phase == ndb_models.TestRunPhase.ON_SUCCESS:
      self._UploadReport(context.test_run, context.latest_attempt)

  def _UploadReport(self, test_run, attempt):
    context_file_pattern = test_run.test.context_file_pattern
    if not context_file_pattern:
      event_log.Warn(
          test_run,
          '[APFE Report Upload] Context parameters not set, skipping upload.')
      return

    # Prepare the results file to upload
    result_file_regex = re.compile('^' + context_file_pattern + '$')
    output_files = file_util.GetOutputFilenames(test_run, attempt)
    result_file = next((f for f in output_files if result_file_regex.match(f)),
                       None)
    if not result_file:
      event_log.Warn(
          test_run,
          '[APFE Report Upload] Result file not found, skipping upload.')
      return
    result_url = file_util.GetOutputFileUrl(test_run, attempt, result_file)
    result_handle = file_util.FileHandle.Get(result_url)
    result_info = result_handle.Info()
    if not result_info or result_info.content_type != 'application/zip':
      event_log.Warn(
          test_run,
          '[APFE Report Upload] Result file type is not zip, skipping upload.')
      return

    # Start upload session
    raw_response = self._GetClient().compatibility().report().startUploadReport(
    ).execute(
        http=self._GetHttp(), num_retries=constant.NUM_RETRIES)
    resource_name = json.loads(raw_response)['ref']['name']

    # Upload result
    result_media = file_util.FileHandleMediaUpload(
        result_handle, chunksize=constant.UPLOAD_CHUNK_SIZE, resumable=False)
    self._GetClient().media().upload(
        resourceName=resource_name, media_body=result_media).execute(
            http=self._GetHttp(), num_retries=constant.NUM_RETRIES)

    # Create report
    self._GetClient().compatibility().report().create(body={
        'reportRef': {
            'name': resource_name,
        },
        'companyId': self.company_id,
    }).execute(
        http=self._GetHttp(), num_retries=constant.NUM_RETRIES)
    event_log.Info(test_run, f'[APFE Report Upload] Uploaded {result_url}.')


# BEGIN-INTERNAL

_STAGING_API_NAME = 'staging-androidpartner.sandbox'


class StagingAPFEReportUploadHook(APFEReportUploadHook):
  """Hook which uploads reports to staging APFE."""
  name = 'StagingAPFEReportUploadHook'

  def __init__(self, _credentials=None, company_id=None, api_key=None, **_):
    super(StagingAPFEReportUploadHook, self).__init__(
        _credentials=_credentials, company_id=company_id)
    self.api_key = api_key

  def _GetClient(self):
    """Initializes a staging APFE client if necessary."""
    if not self._client:
      # Discovery api does not accept credentials
      self._client = apiclient.discovery.build(
          _STAGING_API_NAME,
          _API_VERSION,
          # Use raw model as the response of media api is not json
          model=apiclient.model.RawModel(),
          developerKey=self.api_key,
      )

    return self._client


# END_INTERNAL
