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

from google.appengine.ext import deferred
from google.appengine.ext import ndb

from multitest_transport.core import config_loader
from multitest_transport.core import cron_kicker
from multitest_transport.models import ndb_models
from multitest_transport.test_scheduler import download_util
from multitest_transport.test_scheduler import test_scheduler
from multitest_transport.util import tfc_client


class AppStartHandler(webapp2.RequestHandler):
  """App start event handler."""

  def get(self):
    # TODO: remove once users have initialized summaries
    oldest_summary = ndb_models.TestRunSummary.query().order(
        ndb_models.TestRunSummary.create_time).get()
    deferred.defer(_InitTestRunSummaries, starting_from=oldest_summary)

    config_loader.Load()
    cron_kicker.Init()

    # Release any remaining test resource download trackers.
    download_util.ReleaseDownloadLocks()

    # Requeue non-final commands and command attempts for timeout monitoring.
    tfc_client.BackfillCommands()
    tfc_client.BackfillCommandAttempts()

    # Requeue or Cancel the pending test runs.
    test_scheduler.CheckPendingTestRuns()


def _InitTestRunSummaries(starting_from=None, cursor=None, batch_size=100):
  """Initialize test run summaries."""
  query = ndb_models.TestRun.query().order(-ndb_models.TestRun.create_time)
  if starting_from:
    query = query.filter(
        ndb_models.TestRun.create_time < starting_from.create_time)
  test_runs, next_cursor, more = query.fetch_page(
      batch_size, start_cursor=cursor)
  summaries = [test_run.ToSummary() for test_run in test_runs]
  ndb.put_multi(summaries)
  if more:
    deferred.defer(_InitTestRunSummaries, cursor=next_cursor)


APP = webapp2.WSGIApplication([
    ('/_ah/start', AppStartHandler)
], debug=True)
