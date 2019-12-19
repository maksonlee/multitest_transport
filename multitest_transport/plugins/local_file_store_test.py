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

"""Unit tests for local_file_store."""


import cloudstorage as gcs

from google.appengine.ext import testbed
from absl.testing import absltest
from multitest_transport.plugins import local_file_store

_FILE_SIZE = 10 * 1024


class LocalFileStoreBuildProviderTest(absltest.TestCase):

  def setUp(self):
    super(LocalFileStoreBuildProviderTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()
    self.addCleanup(self.testbed.deactivate)
    self.provider = local_file_store.LocalFileStoreBuildProvider()

  def _CreateFile(self, filename):
    with gcs.open(local_file_store._GCS_PATH + filename, 'w') as f:
      f.write('*' * _FILE_SIZE)

  def testGetBuildItem(self):
    filename = 'foo.txt'
    self._CreateFile(filename)

    item = self.provider.GetBuildItem(filename)

    self.assertEqual(filename, item.name)
    self.assertEqual(filename, item.path)
    self.assertTrue(item.is_file)
    self.assertTrue(_FILE_SIZE, item.size)
    self.assertTrue(local_file_store._GCS_PATH + filename, item.origin_url)

  def testListBuildItem(self):
    names = ['abc.txt', 'def.txt', 'xyz.txt']
    for name in names:
      self._CreateFile(name)

    items, token = self.provider.ListBuildItems()

    self.assertEqual(len(names), len(items))
    for name, item in zip(names, items):
      self.assertEqual(name, item.name)
      self.assertEqual(name, item.path)
      self.assertTrue(item.is_file)
      self.assertTrue(_FILE_SIZE, item.size)
      self.assertTrue(local_file_store._GCS_PATH + name, item.origin_url)
    self.assertIsNone(token)

if __name__ == '__main__':
  absltest.main()
