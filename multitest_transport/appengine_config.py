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
import os

import google3

from tradefed_cluster import common
from tradefed_cluster import env_config

from google.appengine.api import modules

from multitest_transport.models import test_run_hook

# Set TFC env_config.
env_config.CONFIG = env_config.EnvConfig(
    device_info_snapshot_file_format='/device_info_snapshots/%s.gz',
    plugin=test_run_hook.TfcTaskInterceptor(),
    should_send_report=True,
    use_admin_api=False,
    use_google_api=False,
    event_queue_name='tfc-event-queue',
    object_event_filter=[common.ObjectEventType.REQUEST_STATE_CHANGED,
                         common.ObjectEventType.COMMAND_ATTEMPT_STATE_CHANGED])


def webapp_add_wsgi_middleware(app):
  # Patch HTTP_HOST to a default module's hostname.
  # GAE's GCS library constructs local API URL using HTTP_HOST variable.
  # Thus if this variable is set to be a hostname which is unreachable from
  # a MTT machine (e.g. a proxy hostname), all GCS operations fail.
  # TODO: remove this once we removed local GCS dependency.
  os.environ['HTTP_HOST'] = modules.get_hostname('default')
  return app
