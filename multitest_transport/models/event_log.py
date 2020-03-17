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

"""Records application events."""
from google.appengine.ext import ndb

from multitest_transport.models import ndb_models


def GetEntries(entity_or_key=None):
  """Retrieve all log entries for an entity.

  Args:
    entity_or_key: optional entity or entity key to look up
  Returns:
    list of log entries
  """
  ancestor = _GetKey(entity_or_key)
  query = ndb_models.EventLogEntry.query(ancestor=ancestor)
  return query.order(ndb_models.EventLogEntry.create_time).fetch()


def _GetKey(entity_or_key):
  """Helper to retrieve an entity's key if needed."""
  if isinstance(entity_or_key, ndb.Model):
    return entity_or_key.key
  return entity_or_key


def Info(entity_or_key, message):
  """Convenience method to add an info entry.

  Args:
    entity_or_key: related entity or entity key
    message: log message
  """
  _Log(ndb_models.EventLogLevel.INFO, entity_or_key, message)


def Warn(entity_or_key, message):
  """Convenience method to add a warning entry.

  Args:
    entity_or_key: related entity or entity key
    message: log message
  """
  _Log(ndb_models.EventLogLevel.WARNING, entity_or_key, message)


def Error(entity_or_key, message):
  """Convenience method to add an error entry.

  Args:
    entity_or_key: related entity or entity key
    message: log message
  """
  _Log(ndb_models.EventLogLevel.ERROR, entity_or_key, message)


def _Log(level, entity_or_key, message):
  """Persists a new log entry."""
  parent = _GetKey(entity_or_key)
  ndb_models.EventLogEntry(parent=parent, level=level, message=message).put()
