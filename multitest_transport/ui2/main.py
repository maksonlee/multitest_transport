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

"""Main handler for MTT."""
import os

import javascript_sources
import jinja2
import webapp2

from google.appengine.api import modules

from multitest_transport.models import ndb_models
from multitest_transport.util import env


BASE_PATH = os.path.dirname(__file__)
MANIFEST_PATH = BASE_PATH + '/dev_sources.MF'

JINJA = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__))))

APP_JS = 'dev.js' if env.IS_DEV_MODE else 'app.js'


class BaseHandler(webapp2.RequestHandler):
  """A base class for all page request handlers."""

  def __init__(self, request, response):
    super(BaseHandler, self).__init__(request, response)
    self.context = {}
    self.context['env'] = env
    self.context['hostname'] = modules.get_hostname('default').split(':', 2)[0]

    private_node_config = ndb_models.GetPrivateNodeConfig()
    self.context['private_node_config'] = private_node_config

    self.context['analytics_tracking_id'] = ''
    if not env.IS_DEV_MODE and private_node_config.metrics_enabled:
      self.context['analytics_tracking_id'] = 'UA-140187490-1'


class MainHandler(BaseHandler):
  """Always returns index.html. Routing handled by angular."""

  def get(self):
    self.context['app_js'] = APP_JS
    template = JINJA.get_template('index.html')
    self.response.write(template.render(self.context))


class DevJavascriptHandler(webapp2.RequestHandler):
  """Development JavaScript handler.

  In development mode, the app.yaml provides a path to a manifest
  file for serving concatenated JS.  The production app.yaml maps
  app_bundle.js to a compiled static file served by App Engine.

  """

  def get(self):
    self.response.out.write(
        javascript_sources.compile_js_from_manifest(MANIFEST_PATH))


ROUTES = [('/.*', MainHandler)]
if env.IS_DEV_MODE:
  ROUTES = [('/dev.js', DevJavascriptHandler)] + ROUTES

APP = webapp2.WSGIApplication(ROUTES)
