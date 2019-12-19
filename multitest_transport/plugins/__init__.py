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

"""A plugin package."""

import importlib
import logging
import os
import pkgutil

from multitest_transport.plugins.base import *  

def Discover():
  """Import all plugin modules."""
  logging.info('Discovering plugin modules...')
  for _, name, ispkg in pkgutil.iter_modules([os.path.dirname(__file__)]):
    if ispkg or name in ['base', 'constant']:
      continue
    name = __package__ + '.' + name
    logging.info('Importing plugin %s...', name)
    importlib.import_module(name)

Discover()
