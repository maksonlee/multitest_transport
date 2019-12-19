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

"""A utility module for API tests."""

from absl.testing import absltest
import webtest

from google.appengine.ext import testbed
import endpoints


class TestCase(absltest.TestCase):
  """A base class for API test classes."""

  def setUp(self, api_class):
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.addCleanup(self.testbed.deactivate)
    self.api_server = endpoints.api_server([api_class])
    self.app = webtest.TestApp(self.api_server)
