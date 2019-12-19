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

"""Unit tests for build."""

from absl.testing import absltest

from google.appengine.ext import testbed

from multitest_transport import plugins
from multitest_transport.plugins import base
from multitest_transport.models import build

MOCK_BUILD_PROVIDER_NAME = 'name'


class MockBuildProvider(plugins.BuildProvider):

  def __init__(self):
    super(MockBuildProvider, self).__init__(
        url_patterns=[
            build.UrlPattern(r'http://abc.def/xyz/(?P<path>.*)', '{path}')
        ])

plugins.RegisterBuildProviderClass(MOCK_BUILD_PROVIDER_NAME, MockBuildProvider)


class BuildTest(absltest.TestCase):

  def setUp(self):
    super(BuildTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()

  def tearDown(self):
    self.testbed.deactivate()
    super(BuildTest, self).tearDown()

  def testGetBuildProviderClass(self):
    cls = build.GetBuildProviderClass(MOCK_BUILD_PROVIDER_NAME)

    self.assertEqual(MockBuildProvider, cls)

  def testListBuildProviderNames(self):
    names = build.ListBuildProviderNames()

    self.assertIn(MOCK_BUILD_PROVIDER_NAME, names)

  def testBuildUrl(self):
    item = base.BuildItem(
        name='z z z.txt', path='a/b/c/z z z.txt', is_file=True)
    encoded_url = build.BuildUrl('local_file_store', item)
    self.assertEqual(encoded_url, 'mtt:///local_file_store/a/b/c/z%20z%20z.txt')
    item = base.BuildItem(name='d/e.txt', path='a/b/c/d/e.txt', is_file=True)
    encoded_url = build.BuildUrl('local_file_store', item)
    self.assertEqual(encoded_url, 'mtt:///local_file_store/a/b/c/d%2Fe.txt')

  def testFindBuildChannel(self):
    build_channel_config = build.AddBuildChannel(
        'foo', MOCK_BUILD_PROVIDER_NAME, {})
    url = 'http://abc.def/xyz/path/to/file'
    build_channel, path = build.FindBuildChannel(url)
    self.assertEqual(build_channel_config.key.id(), build_channel.id)
    self.assertEqual('path/to/file', path)


class BuildLocatorTest(absltest.TestCase):

  def setUp(self):
    super(BuildLocatorTest, self).setUp()
    self.testbed = testbed.Testbed()
    self.testbed.activate()
    self.testbed.init_all_stubs()

  def tearDown(self):
    self.testbed.deactivate()
    super(BuildLocatorTest, self).tearDown()

  def testBuildLocator(self):
    build_locator = build.BuildLocator.ParseUrl(
        'mtt:///local_file_store/file.txt')
    self.assertEqual(build_locator.build_channel_id, 'local_file_store')
    self.assertEqual(build_locator.directory, None)
    self.assertEqual(build_locator.filename, 'file.txt')
    self.assertEqual(build_locator.path, 'file.txt')

    build_locator = build.BuildLocator.ParseUrl(
        'mtt:///local_file_store/a/b/c/file.txt')
    self.assertEqual(build_locator.build_channel_id, 'local_file_store')
    self.assertEqual(build_locator.directory, 'a/b/c')
    self.assertEqual(build_locator.filename, 'file.txt')
    self.assertEqual(build_locator.path, 'a/b/c/file.txt')

    build_locator = build.BuildLocator.ParseUrl('http://file.img')
    self.assertEqual(build_locator, None)

    build_locator = build.BuildLocator.ParseUrl(
        'mtt:///drive/a/b/c/file%201.txt')
    self.assertEqual(build_locator.build_channel_id, 'drive')
    self.assertEqual(build_locator.directory, 'a/b/c')
    self.assertEqual(build_locator.filename, 'file 1.txt')
    self.assertEqual(build_locator.path, 'a/b/c/file 1.txt')

    build_locator = build.BuildLocator.ParseUrl(
        'mtt:///drive/a/b/c/signed%2Fbuild.img')
    self.assertEqual(build_locator.build_channel_id, 'drive')
    self.assertEqual(build_locator.directory, 'a/b/c')
    self.assertEqual(build_locator.filename, 'signed/build.img')
    self.assertEqual(build_locator.path, 'a/b/c/signed/build.img')


if __name__ == '__main__':
  absltest.main()
