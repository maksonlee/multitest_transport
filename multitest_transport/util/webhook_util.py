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

"""Webhook utility module."""

import logging
import string
import urllib2


def InvokeWebhook(webhook, context=None):
  """Invoke a webhook.

  Args:
    webhook: a ndb_models.Webhook object.
    context: a context dict to use to extend vars in webhook URL/data.
  """
  logging.info('context=%s', context)
  url = string.Template(webhook.url).safe_substitute(context)
  data = None
  if webhook.data:
    data = string.Template(webhook.data).safe_substitute(context)
  logging.info(
      'Invoking a webhook: url=%s, method=%s, data=%s',
      url, webhook.http_method, data)
  req = urllib2.Request(url=url, data=data)
  req.get_method = lambda: webhook.http_method.name
  f = urllib2.urlopen(req)
  logging.info('Response: %s', f.read())
