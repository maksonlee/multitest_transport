# Copyright 2021 Google LLC
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
"""Tests for multitest_transport.scripts.gen_subnets."""

import io

from absl.testing import absltest
from multitest_transport.scripts import gen_subnets


class GenSubnetsTest(absltest.TestCase):
  """Unit test for gen_subnets."""

  def setUp(self):
    super().setUp()
    self._stdout = io.StringIO()

  def tearDown(self):
    self._stdout.close()
    super().tearDown()

  def testInvalidAddress(self):
    with self.assertRaises(SystemExit):
      gen_subnets.main(['invalid', '27', '2'], self._stdout)
    self.assertFalse(self._stdout.getvalue())

  def testNotEnoughSubnets(self):
    with self.assertRaises(ValueError):
      gen_subnets.main(['192.168.1.0/30', '31', '3'], self._stdout)
    self.assertFalse(self._stdout.getvalue())

  def testIPv4(self):
    gen_subnets.main(
        ['192.168.1.0/24', '27', '2', '192.168.1.33', '2001:db8:0:1::1'],
        self._stdout)
    self.assertEqual('192.168.1.0 192.168.1.64\n', self._stdout.getvalue())

  def testIPv6(self):
    gen_subnets.main(
        ['2001:db8::/56', '64', '2', '192.168.1.33', '2001:db8:0:1::1'],
        self._stdout)
    self.assertEqual('2001:db8:: 2001:db8:0:2::\n', self._stdout.getvalue())


if __name__ == '__main__':
  absltest.main()
