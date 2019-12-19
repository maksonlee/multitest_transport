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

"""A handler to provide proxied access to GCS files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import webapp2

from google.appengine.ext.webapp import blobstore_handlers

from multitest_transport.util import gcs_util


class FileHandler(blobstore_handlers.BlobstoreDownloadHandler):
  """A request handler to serve files in GCS."""

  def get(self, filename):
    """Handles a GET request for a GCS file.

    Args:
      filename: a GCS filename.
    """
    key = gcs_util.GetBlobstoreKey('/' + filename)
    if not key:
      self.error(404)
    self.send_blob(key)


APP = webapp2.WSGIApplication([
    (r'/gcs_proxy/(.*)', FileHandler),
], debug=True)
