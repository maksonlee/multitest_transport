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

"""WebAOA flask server."""
import os

import flask


from multitest_transport.models import ndb_models
from multitest_transport.util import env

APP = flask.Flask(
    __name__,
    root_path=os.path.dirname(__file__),
    static_folder='static',
    template_folder='.')


@APP.route('/webaoa/static/<path:path>')
def Static(path):
  """Returns static files."""
  return flask.send_from_directory(APP.static_folder, path, conditional=False)


@APP.route('/webaoa/app.js')
def App():
  """Returns application script."""
  script = 'dev_sources.concat.js' if env.IS_DEV_MODE else 'compiled.js'
  return flask.send_from_directory(APP.root_path, script, conditional=False)


@APP.route('/webaoa', strict_slashes=False, defaults={'path': ''})
@APP.route('/webaoa/<path:path>')
def Root(path):
  """Routes all other requests to index.html and angular."""
  del path  # unused
  analytics_tracking_id = ''
  if not env.IS_DEV_MODE and ndb_models.GetPrivateNodeConfig().metrics_enabled:
    analytics_tracking_id = 'G-XRN33KLKER'
  return flask.render_template(
      'index.html',
      analytics_tracking_id=analytics_tracking_id,
      is_google=env.IS_GOOGLE)
