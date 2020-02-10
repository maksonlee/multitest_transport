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

"""An API server module."""

from tradefed_cluster import api as tfc_api

import endpoints

from multitest_transport.api import base
from multitest_transport.api import build_channel_api  from multitest_transport.api import build_channel_provider_api  from multitest_transport.api import config_set_api  from multitest_transport.api import device_action_api  from multitest_transport.api import node_config_api  from multitest_transport.api import private_node_config_api  from multitest_transport.api import test_api  from multitest_transport.api import test_plan_api  from multitest_transport.api import test_run_api  from multitest_transport.api import test_run_hook_api  
APP = endpoints.api_server([base.MTT_API] + tfc_api.API_HANDLERS)
