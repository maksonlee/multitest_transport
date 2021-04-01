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

"""ATS UI flask server."""
import os

import flask

from multitest_transport.models import ndb_models
from multitest_transport.util import env

ROOT_PATH = os.path.dirname(__file__)
STATIC_PATH = os.path.join(ROOT_PATH, 'static')

APP = flask.Flask(
    __name__,
    root_path=ROOT_PATH,
    static_folder=None,
    template_folder=ROOT_PATH)


@APP.route('/static/<path:path>')
def Static(path):
  """Returns static files."""
  return flask.send_from_directory(STATIC_PATH, path, conditional=False)


@APP.route('/app.js')
def App():
  """Returns application script."""
  script = 'dev_sources.concat.js' if env.IS_DEV_MODE else 'app.js'
  return flask.send_from_directory(ROOT_PATH, script, conditional=False)


@APP.route('/', defaults={'_': ''})
@APP.route('/<path:_>')
def Root(_):
  """Routes all other requests to index.html and angular."""
  private_node_config = ndb_models.GetPrivateNodeConfig()
  analytics_tracking_id = ''
  if not env.IS_DEV_MODE and private_node_config.metrics_enabled:
    analytics_tracking_id = 'UA-140187490-1'
  return flask.render_template(
      'index.html',
      analytics_tracking_id=analytics_tracking_id,
      env=env,
      private_node_config=private_node_config)
