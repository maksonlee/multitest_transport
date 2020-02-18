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

"""Service environment variables."""

import os

IS_DEV_MODE = os.environ.get('DEV_MODE') == 'true'

DEFAULT_QUEUE_TIMEOUT_SECONDS = 86400  # one day
DEFAULT_OUTPUT_IDLE_TIMEOUT_SECONDS = 3600  # one hour
APPLICATION_ID = os.environ.get('APPLICATION_ID')
GCS_BUCKET_NAME = os.environ.get('BUCKET_NAME', 'app_default_bucket')
GCS_FETCH_DEADLINE_SECONDS = 60
GCS_ROOT_PATH = '/%s' % GCS_BUCKET_NAME
GCS_TEMP_PATH = '/%s/tmp' % GCS_BUCKET_NAME
GCS_DATA_PATH = '/%s/data' % GCS_BUCKET_NAME

# The following variables are passed by mtt.cli.cli.Serve function.
BLOBSTORE_PATH = os.environ.get('MTT_BLOBSTORE_PATH')
STORAGE_PATH = os.environ.get('MTT_STORAGE_PATH')
FILE_SERVER_ROOT = os.environ.get('MTT_FILE_SERVER_ROOT')
FILE_SERVER_URL = os.environ.get('MTT_FILE_SERVER_URL')
FILE_BROWSE_URL_FORMAT = os.environ.get('MTT_FILE_BROWSE_URL_FORMAT')
FILE_OPEN_URL_FORMAT = os.environ.get('MTT_FILE_OPEN_URL_FORMAT')
FILE_SERVER_URL2 = os.environ.get('MTT_FILE_SERVER_URL2')
UNKNOWN = 'UNKNOWN'
USER = os.environ.get('MTT_USER', UNKNOWN)
HOSTNAME = os.environ.get('MTT_HOSTNAME', UNKNOWN)
VERSION = os.environ.get('MTT_VERSION', UNKNOWN)
ADB_VERSION = os.environ.get('ADB_VERSION', UNKNOWN)
GOOGLE_OAUTH2_CLIENT_ID = os.environ.get('MTT_GOOGLE_OAUTH2_CLIENT_ID', UNKNOWN)
GOOGLE_OAUTH2_CLIENT_SECRET = os.environ.get(
    'MTT_GOOGLE_OAUTH2_CLIENT_SECRET', UNKNOWN)
GOOGLE_API_KEY = os.environ.get('MTT_GOOGLE_API_KEY', UNKNOWN)
