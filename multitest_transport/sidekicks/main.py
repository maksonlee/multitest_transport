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

"""A main app for sidekick modules."""
import webapp2

from multitest_transport.sidekicks import gcs_cleaner
from multitest_transport.test_scheduler import download_util
from multitest_transport.util import analytics


class GcsCleanerHandler(webapp2.RequestHandler):
  """A request handler for periodic schedule checks."""

  def get(self):
    """Start GCS cleaner."""
    gcs_cleaner.Start()

APP = webapp2.WSGIApplication([
    ('/sidekicks/gcs_cleaner', GcsCleanerHandler),
    ('/sidekicks/heartbeat_sender', analytics.HeartbeatSender),
    ('/sidekicks/test_resource_tracker_cleaner',
     download_util.TestResourceTrackerCleaner),
], debug=True)
