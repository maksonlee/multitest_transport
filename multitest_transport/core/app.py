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

"""A module to handle app lifecycle events."""
import google3

import webapp2

from multitest_transport.core import config_loader
from multitest_transport.core import cron_kicker
from multitest_transport.test_scheduler import download_util
from multitest_transport.test_scheduler import test_scheduler
from multitest_transport.util import tfc_client


class AppStartHandler(webapp2.RequestHandler):
  """App start event handler."""

  def get(self):
    config_loader.Load()
    cron_kicker.Init()

    # Release any remaining test resource download trackers.
    download_util.ReleaseDownloadLocks()

    # Requeue non-final commands and command attempts for timeout monitoring.
    tfc_client.BackfillCommands()
    tfc_client.BackfillCommandAttempts()

    # Requeue or Cancel the pending test runs.
    test_scheduler.CheckPendingTestRuns()


APP = webapp2.WSGIApplication([
    ('/_ah/start', AppStartHandler)
], debug=True)
