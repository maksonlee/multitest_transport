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

"""Unit tests for sql_util."""
from unittest import mock

from absl.testing import absltest
from protorpc import messages
import sqlalchemy as sa
import sqlalchemy_utils as sa_utils


from multitest_transport.util import sql_util

# Database for testing
db = sql_util.Database(uri='sqlite:///:memory:')


class FooEnum(messages.Enum):
  """Enum for testing."""
  FOO = 0
  BAR = 1


class FooModel(db.Model):
  """Model for testing."""
  __tablename__ = 'foo'

  id = sa.Column(sa.Integer, primary_key=True)
  text = sa.Column(sa.String(255))
  enum = sa.Column(sql_util.IntEnum(FooEnum))


class SqlUtilTest(absltest.TestCase):

  def setUp(self):
    super(SqlUtilTest, self).setUp()
    db.CreateTables()

  def tearDown(self):
    db.DropTables()
    super(SqlUtilTest, self).tearDown()

  @mock.patch.object(sa_utils, 'create_database')
  @mock.patch.object(sa_utils, 'database_exists')
  @mock.patch.object(sa, 'create_engine')
  def testEngine(self, mock_create_engine, mock_db_exists, mock_create_db):
    """Tests that databases and connections can be created."""
    test_db = sql_util.Database('uri')
    mock_engine = mock.MagicMock(url='uri')
    mock_create_engine.return_value = mock_engine
    mock_db_exists.return_value = False

    self.assertEqual(test_db.engine, mock_engine)
    mock_create_engine.assert_called_once_with('uri')
    mock_create_db.assert_called_once_with('uri')

  def testSession(self):
    """Tests that entities can be inserted and queried."""
    with db.Session() as session:
      session.add(FooModel(text='hello world'))

    with db.Session() as session:
      entities = session.query(FooModel).all()
      self.assertLen(entities, 1)
      self.assertIsNotNone(entities[0].id)
      self.assertEqual(entities[0].text, 'hello world')

  def testSession_rollback(self):
    """Tests that updates are rolled back after an error."""
    with self.assertRaises(RuntimeError):
      with db.Session() as session:
        session.add(FooModel(text='hello world'))
        raise RuntimeError('Test error')

    with db.Session() as session:
      self.assertEmpty(session.query(FooModel).all())

  def testIntEnum(self):
    """Tests that IntEnums can be stored."""
    with db.Session() as session:
      session.add(FooModel(enum=FooEnum.FOO))
      session.add(FooModel(enum=FooEnum.BAR))

    with db.Session() as session:
      entities = session.query(FooModel).all()
      self.assertLen(entities, 2)
      self.assertEqual(entities[0].enum, FooEnum.FOO)
      self.assertEqual(entities[1].enum, FooEnum.BAR)


if __name__ == '__main__':
  absltest.main()
