# Copyright 2020 Google LLC
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

"""A core service checker.

A module to check availability of the core services.
"""
import logging
import requests
from tradefed_cluster.util import ndb_shim as ndb

from multitest_transport.util import file_util


class ServiceChecker(object):
  """A service checker."""
  pass


class DatastoreChecker(ServiceChecker):
  """Cloud Datastore availability checker."""
  name = 'Cloud Datastore'

  @classmethod
  def Run(cls):
    """Check Datastore availability."""
    ndb.Key('Kind', 1).get()


class RabbitMQChecker(ServiceChecker):
  """RabbitMQ availability checker."""
  name = 'RabbitMQ'
  label = 'rabbitmq'

  @classmethod
  def Run(cls):
    """Check RabbitMQ service availability using its management plugin."""
    response = requests.get('http://localhost:15672/api/vhosts',
                            auth=requests.auth.HTTPBasicAuth('guest', 'guest'))
    response.raise_for_status()


class FileServerChecker(ServiceChecker):
  """Local file server availability checker."""
  name = 'File Server'

  @classmethod
  def Run(cls):
    """Check local file server availability."""
    files = file_util.RemoteFileHandle('file:///').ListFiles()
    if files is None:
      raise RuntimeError('File server root directory not found')


def Check():
  """Check availability of dependent services."""
  checkers = [DatastoreChecker, FileServerChecker, RabbitMQChecker]
  logging.info('Checking availability of dependent services...')
  for checker in checkers:
    try:
      checker.Run()
      logging.info('\t%s: OK', checker.name)
    except Exception:        logging.exception('\t%s: ERROR', checker.name)
