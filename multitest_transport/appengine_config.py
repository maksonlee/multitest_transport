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

"""Google App Engine module configuration."""
import logging
import os

import google3

from tradefed_cluster import common
from tradefed_cluster import env_config

from multitest_transport.models import ndb_models

# Set TFC env_config.
env_config.CONFIG = env_config.EnvConfig(
    device_info_snapshot_file_format='/device_info_snapshots/%s.gz',
    should_send_report=True,
    use_admin_api=False,
    use_google_api=False,
    event_queue_name='tfc-event-queue',
    object_event_filter=[common.ObjectEventType.REQUEST_STATE_CHANGED,
                         common.ObjectEventType.COMMAND_ATTEMPT_STATE_CHANGED])


def apply_proxy_config():
  """Apply proxy config."""
  node_config = ndb_models.GetNodeConfig()
  proxy_config = node_config.proxy_config
  if not proxy_config:
    return
  logging.info('Applying proxy config: %s', proxy_config)
  if proxy_config.http_proxy:
    os.environ['http_proxy'] = proxy_config.http_proxy
  if proxy_config.https_proxy:
    os.environ['https_proxy'] = proxy_config.https_proxy
  if proxy_config.ftp_proxy:
    os.environ['ftp_proxy'] = proxy_config.ftp_proxy
  if proxy_config.no_proxy:
    # Append 127.0.0.1 to no proxy list to exclude in-server API calls.
    os.environ['no_proxy'] = proxy_config.no_proxy + ',127.0.0.1'


def webapp_add_wsgi_middleware(app):
  apply_proxy_config()
  return app
