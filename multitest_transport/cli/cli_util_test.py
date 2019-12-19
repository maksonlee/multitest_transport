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

"""Tests for cli_util."""
import os
import tempfile

from absl.testing import absltest

from multitest_transport.cli import cli_util
from multitest_transport.cli import unittest_util


class CliUtilTest(absltest.TestCase):

  def testGetVersion(self):
    f = None
    try:
      f = tempfile.NamedTemporaryFile(delete=False)
      unittest_util.CreateZipFile(
          f.name, [unittest_util.File(
              filename='VERSION',
              content='[version]\nVERSION=aversion\nBUILD_ENVIRONMENT=test')])
      self.assertEqual(
          ('aversion', 'test'),
          cli_util.GetVersion(f.name))
    finally:
      if f:
        f.close()
        os.remove(f.name)
        self.assertFalse(os.path.exists(f.name))

  def testGetVersion_notZip(self):
    f = None
    try:
      f = tempfile.NamedTemporaryFile(delete=False)
      f.write(b'afile')
      f.close()
      self.assertEqual(
          ('unknown', 'unknown'),
          cli_util.GetVersion(cli_path=f.name))
    finally:
      if f:
        f.close()
        os.remove(f.name)
        self.assertFalse(os.path.exists(f.name))

  def testGetVersion_noVersion(self):
    f = None
    try:
      f = tempfile.NamedTemporaryFile(delete=False)
      unittest_util.CreateZipFile(
          f.name,
          [unittest_util.File(filename='INVALID_VERSION', content='aversion')])
      self.assertEqual(
          ('unknown', 'unknown'),
          cli_util.GetVersion(cli_path=f.name))
    finally:
      if f:
        f.close()
        os.remove(f.name)
        self.assertFalse(os.path.exists(f.name))

  def testCreateLogger(self):
    try:
      f = tempfile.NamedTemporaryFile()
      arg_parser = cli_util. CreateLoggingArgParser()
      args = arg_parser.parse_args([
          '--logtostderr', '-v', '--log_file', f.name])
      logger = cli_util.CreateLogger(args)
      self.assertIsNotNone(logger)
    finally:
      f.close()


if __name__ == '__main__':
  absltest.main()
