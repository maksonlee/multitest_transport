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

"""SQL utilities."""
import contextlib
import logging

import sqlalchemy as sa
from sqlalchemy.ext import declarative
import sqlalchemy_utils as sa_utils


class IntEnum(sa.TypeDecorator):
  """Stores enums as integers, supports enum.IntEnum and messages.Enum."""
  impl = sa.Integer

  def __init__(self, enum_cls, *args, **kwargs):
    super(IntEnum, self).__init__(*args, **kwargs)
    self.enum_cls = enum_cls

  def process_bind_param(self, value, _):
    return int(value) if value is not None else None

  def process_result_value(self, value, _):
    return self.enum_cls(value) if value is not None else None


class Database(object):
  """Database session and model manager."""
  _engine = None

  def __init__(self, uri, **options):
    self.uri = uri
    self.options = options
    self.Model = declarative.declarative_base()  
  @property
  def engine(self):
    """Returns the sqlalchemy engine, connecting and create DB if necessary."""
    if not self._engine:
      logging.info('Connecting to %s', self.uri)
      self._engine = sa.create_engine(self.uri, **self.options)
      if not sa_utils.database_exists(self._engine.url):
        sa_utils.create_database(self._engine.url)
    return self._engine

  @contextlib.contextmanager
  def Session(self):
    """Context manager that provides an sqlalchemy session."""
    session_factory = sa.orm.sessionmaker(
        bind=self.engine, expire_on_commit=False)
    scoped_session = sa.orm.scoped_session(session_factory)
    try:
      yield scoped_session
      scoped_session.commit()
    except:
      scoped_session.rollback()
      raise
    finally:
      scoped_session.remove()

  def CreateTables(self):
    """Creates or updates database tables."""
    self.Model.metadata.create_all(self.engine)

  def DropTables(self):
    """Drops database tables (for testing)."""
    self.Model.metadata.drop_all(self.engine)
