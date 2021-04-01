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

"""A no-op web handler, responds to every request with a '200 OK'."""
import flask
from tradefed_cluster import common

APP = flask.Flask(__name__)


@APP.route("/")
# This matchs all path start with "/".
@APP.route("/<path:fake>")
def NoopHandler(fake):
  del fake
  return common.HTTP_OK
