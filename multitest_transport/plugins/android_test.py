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

"""Unit tests for android module."""
from absl.testing import absltest
import mock

from multitest_transport.plugins import android


class AndroidBuildProviderTest(absltest.TestCase):

  def setUp(self):
    super(AndroidBuildProviderTest, self).setUp()
    self.provider = android.AndroidBuildProvider()
    self.mock_client = mock.MagicMock()
    self.provider._client = self.mock_client

  def testGetBuildItem(self):
    size = 12345
    creation_timestamp = 0
    self.mock_client.buildartifact().get().execute.return_value = {
        'name': 'yyy/zzz.txt',
        'size': size,
        'creationTime': creation_timestamp
    }

    item = self.provider.GetBuildItem('foo/bar/12345/yyy/zzz.txt')

    self.assertIsNotNone(item)
    self.assertEqual('yyy/zzz.txt', item.name)
    self.assertEqual('foo/bar/12345/yyy/zzz.txt', item.path)
    self.assertEqual(size, item.size)
    self.mock_client.buildartifact.assert_called()
    self.mock_client.buildartifact().get.assert_called_with(
        target='bar', buildId='12345', attemptId='latest',
        resourceId='yyy/zzz.txt')
    self.mock_client.buildartifact().get().execute.assert_called()

  def testListBuildItemsWithLatest(self):
    self.mock_client.build().list().execute.return_value = {
        'builds': [{
            'buildId': '123'
        }]
    }
    items, _ = self.provider.ListBuildItems(path='abc/def')
    self.assertIsNotNone(items)
    self.assertLen(items, 2)
    self.assertEqual(items[0].name, 'LATEST')
    self.assertEqual(items[1].name, '123')


if __name__ == '__main__':
  absltest.main()
