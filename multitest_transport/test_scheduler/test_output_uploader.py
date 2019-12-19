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

"""A module to upload output to remote path."""
import json
import logging
import os
import re
import urllib2

import webapp2

from google.appengine.api import taskqueue

from multitest_transport.models import build
from multitest_transport.models import ndb_models
from multitest_transport.util import env
from multitest_transport.util import file_util
from multitest_transport.util import tfc_client

_TEST_OUTPUT_UPLOADER_QUEUE = 'test-output-uploader-queue'
_HOST_NAME = 'localhost'


def _GetFileNames(file_info_path):
  """Read file names from file info.

  Read file names from a file called FILES, which is a browsepy file that
  contains all other file's names

  Args:
    file_info_path: path to fileinfo
    (Sample file_info_path: http://localhost:8800/
    open/app_default_bucket/test_runs/30090001/output/89001/
    cb5179e3-ea4c-48c2-b722-6ad6539d2d18/FILES)
  Returns:
    file_names (a list of file names)
  """
  file_names = []
  try:
    f = urllib2.urlopen(file_info_path)
    file_names = f.readlines()
  except urllib2.HTTPError as e:
    logging.error(e)
  return file_names


def _GetFileUrls(test_run):
  """Get file urls from test run.

  Args:
    test_run: a test_run obj
  Returns:
    file_urls: a list of file_path.
    (Sample file path: http://localhost:8800/open/app_default_bucket/
    test_runs/30090001/output/89001/cb5179e3-ea4c-48c2-b722-6ad6539d2d18)
  """
  file_urls = []
  # Standalone mode]
  if test_run.output_storage == file_util.FileStorage.LOCAL_FILE_SYSTEM:
    tfc_request = tfc_client.GetRequest(test_run.request_id)
    command_attempts = tfc_request['command_attempts']

    output_path = test_run.output_path
    if output_path.startswith('/'):
      output_path = output_path[1:]
    file_open_url = env.FILE_OPEN_URL_FORMAT.format(hostname=_HOST_NAME)
    for attempt in command_attempts:
      command_id = attempt['command_id']
      attempt_id = attempt['attempt_id']
      file_path = os.path.join(file_open_url,
                               output_path,
                               command_id,
                               attempt_id)
      file_urls.append(file_path)
  return file_urls


def ScheduleUploadJobs(test_run_id):
  """Schedule Upload Jobs.

  Put each upload job into the job queue.Each job consist of one file to upload,
  and one desginated channel.
  Test_run object will provide important information such as which channel
  to upload to, what mtt mode is currently using, what's the corresponding
  tfc request, and what is the output path.

  Args:
    test_run_id: test run identifier
  Returns:
    job_list: a list of jobs that are enqueued
    (e.g. job = {'file_name': 'a browsepy file name', 'url': 'an mtt url'})
  """
  test_run = ndb_models.TestRun.get_by_id(test_run_id)
  if not test_run:
    return

  job_list = []
  upload_configs = test_run.test_output_upload_configs
  if not upload_configs:
    return []
  file_urls = _GetFileUrls(test_run)
  # for each upload_config (contains which channel to use)
  #  for each file_info files (metadata file contains information of all files)
  #    for each file in file_info file (file contains data)
  #       put {upload_config, file} into queue
  for upload_config in upload_configs:
    url = upload_config.url
    for file_url in file_urls:
      file_info_path = os.path.join(file_url, 'FILES')
      file_names = _GetFileNames(file_info_path)
      for file_name in file_names:
        file_name = os.path.join(file_url, file_name)
        payload_content = {'file_name': file_name, 'url': url}
        job_list.append(payload_content)
        payload = json.dumps(payload_content)
        task = taskqueue.Task(payload=payload)
        task.add(queue_name=_TEST_OUTPUT_UPLOADER_QUEUE)
  return job_list


def _ParseBrowsepyFilename(browsepy_url):
  """Parse a browsepy url.

  Args:
    browsepy_url: a browsepy url that one can open and read like a file
    (e.g file_name: 'http://localhost:8800/open/app_default_bucket/
    test_runs/30032001/output/32001/9be26d52-d422-402b-abd5-da7eee09da65/
    stdout.txt')
  Returns:
    file_name: part of file_name that matched the regex
    (e.g  'test_runs/30032001/output/32001/
    9be26d52-d422-402b-abd5-da7eee09da65/stdout.txt')
  """
  m = re.match(r'.*/app_default_bucket/(.*)', browsepy_url)
  return m.group(1) if m else None


def Upload(src_url, dest_build_channel_url):
  """Process each upload event.

  Args:
    src_url: a src_url that one can open and read like a file
    (e.g src_url: 'http://localhost:8800/open/app_default_bucket/
    test_runs/30032001/output/32001/9be26d52-d422-402b-abd5-da7eee09da65/
    stdout.txt')
    dest_build_channel_url: a url that consist of channel id and upload path
    (e.g mtt:///channel id/path_to_upload)
  """
  build_locator = build.BuildLocator.ParseUrl(dest_build_channel_url)
  if not build_locator:
    return
  build_channel = build.GetBuildChannel(build_locator.build_channel_id)
  dst_file_path = os.path.join(build_locator.path,
                               _ParseBrowsepyFilename(src_url))
  build_channel.UploadFile(src_url, dst_file_path)


class TaskHandler(webapp2.RequestHandler):
  """A web request handler to handle tasks from the upload event queue."""

  def post(self):
    """Process a request message."""
    payload = json.loads(self.request.body)
    file_name = payload['file_name']
    url = payload['url']
    Upload(file_name, url)


APP = webapp2.WSGIApplication([
    ('.*', TaskHandler),
], debug=True)
