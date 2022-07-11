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

"""MTT integration tests utilities."""

import logging
import os
import socket
import tarfile
import tempfile
import time

from absl import flags
from absl.testing import absltest

import docker
import portpicker
import requests
import retry

FLAGS = flags.FLAGS
flags.DEFINE_string('docker_image', None, 'MTT docker image to use.')
flags.mark_flag_as_required('docker_image')
flags.DEFINE_multi_string('env', [],
                          'Environment variables in the format of NAME=VALUE.')
flags.DEFINE_enum(
    'server_log_level',
    'info',
    ['debug', 'info', 'warn', 'error', 'critical'],
    'Server log level')

# Retry parameters for API calls (retry after 2, 4, and 8 seconds)
RETRY_PARAMS = {'tries': 4, 'delay': 2, 'backoff': 2}

# Constants
CLUSTER = 'default'


class MttContainer(object):
  """Wrapper around an MTT docker container."""

  def __init__(self, image=None, max_local_virtual_devices=0):
    self._image = image or FLAGS.docker_image
    self._max_local_virtual_devices = max_local_virtual_devices

  def __enter__(self):
    """Start the MTT docker container."""
    self._control_server_port = portpicker.pick_unused_port()
    kwargs = {
        'cap_add': ['sys_admin'],
        'devices': ['/dev/fuse'],
        'environment': {
            'MTT_SERVER_LOG_LEVEL': FLAGS.server_log_level,
        },
        'stdin_open': True,
        'tty': True,  # interactive
        'hostname': socket.gethostname(),
        'network_mode': 'bridge',
        'ports': {
            '8000/tcp': self._control_server_port,
        },
        'security_opt': ['apparmor:unconfined'],
    }
    if self._max_local_virtual_devices:
      kwargs['cap_add'].append('net_admin')
      kwargs['devices'].extend([
          '/dev/kvm',
          '/dev/net/tun',
          '/dev/vhost-net',
          '/dev/vhost-vsock',
      ])
      kwargs['environment']['MAX_LOCAL_VIRTUAL_DEVICES'] = str(
          self._max_local_virtual_devices)
    for env in FLAGS.env:
      pair = env.split('=', 1)
      kwargs['environment'][pair[0]] = (pair[1] if len(pair) > 1 else '')

    # Create and start the docker container
    docker_client = docker.from_env()
    self._delegate = docker_client.containers.create(self._image, **kwargs)
    self._delegate.start()
    # Determine the base URLs
    self.base_url = 'http://localhost:%d' % self._control_server_port
    self.mtt_api_url = '%s/_ah/api/mtt/v1' % self.base_url
    self.tfc_api_url = '%s/_ah/api/tradefed_cluster/v1' % self.base_url
    # Wait for application start
    try:
      self._WaitForServer()
    except:
      # If a server fails to start, dump server logs.
      self.DumpLogs()
      raise
    time.sleep(5)  # Additional delay for initialization to complete
    return self

  @retry.retry(tries=60, delay=1, logger=None)
  def _WaitForServer(self):
    """Wait up to 60 seconds for the MTT server."""
    requests.get(self.base_url).raise_for_status()

  def __exit__(self, exception_type, exception_value, traceback):
    """Stop and remove the MTT docker container."""
    self._delegate.stop()
    self._delegate.remove()

  def Start(self):
    """Start the MTT docker container."""
    self.__enter__()

  def Stop(self):
    """Stop and remove the MTT docker container."""
    self.__exit__(None, None, None)

  def Exec(self, *args):
    """Execute a command in the container."""
    exit_code, output = self._delegate.exec_run(list(args), demux=True)
    if exit_code != 0:
      raise RuntimeError(output[1])
    return output[0].decode() if output[0] else None

  def DumpLogs(self):
    """Output the server logs for debugging."""
    output = self._delegate.logs()
    logging.info('Logs: %s', output.decode())
    _, output = self._delegate.exec_run(['cat', '/data/log/server/current'])
    logging.info('Server logs: %s', output.decode())

  def CopyFile(self, src_path, dest_path):
    """Copy a file into the container."""
    with tempfile.NamedTemporaryFile() as archive:
      with tarfile.open(mode='w', fileobj=archive, dereference=True) as t:
        t.add(src_path, arcname=os.path.basename(dest_path))
      archive.seek(0)
      dest_dir = os.path.dirname(dest_path)
      self.Exec('mkdir', '-p', dest_dir)
      return self._delegate.put_archive(path=dest_dir, data=archive)

  def UploadFile(self, src_path, dest_path):
    """Upload a file to the container's local file server."""
    url = '%s/fs_proxy/file/%s' % (self.base_url, dest_path)
    with open(src_path, 'rb') as f:
      content = f.read()
      content_range = 'bytes 0-%d/%d' % (len(content) - 1, len(content))
      requests.put(url, content, headers={'content-range': content_range})

  # MTT API

  @retry.retry(**RETRY_PARAMS)
  def ScheduleTestRun(self, device_serial, test_resource_objs=None, **kwargs):
    """Schedule a new test run using the MTT API."""
    test_run_config = {
        'test_id': 'noop',
        'cluster': CLUSTER,
        'device_specs': ['device_serial:%s' % device_serial],
        'max_retry_on_test_failures': 1,
        'test_resource_objs': test_resource_objs,
    }
    test_run_config.update(kwargs)
    request = {
        'test_run_config': test_run_config,
    }
    response = requests.post('%s/test_runs' % self.mtt_api_url, json=request)
    response.raise_for_status()
    return response.json()

  @retry.retry(**RETRY_PARAMS)
  def CancelTestRun(self, test_run_id):
    """Cancel an existing test run using the MTT API."""
    requests.post('%s/test_runs/%s/cancel' %
                  (self.mtt_api_url, test_run_id)).raise_for_status()

  @retry.retry(**RETRY_PARAMS)
  def GetTestRun(self, test_run_id):
    """Fetch test run information using the MTT API."""
    response = requests.get('%s/test_runs/%s' % (self.mtt_api_url, test_run_id))
    response.raise_for_status()
    return response.json()

  def WaitForState(self, test_run_id, expected_state, timeout=60):
    """Wait for a test run to be in a specific state."""
    start_time = time.time()
    while True:
      state = self.GetTestRun(test_run_id)['state']
      if expected_state == state:
        return
      if (state in ['COMPLETED', 'CANCELED', 'ERROR'] or
          time.time() >= start_time + timeout):
        # Unexpected final state or out of time
        raise AssertionError('Wrong run state %s (expected %s)' %
                             (state, expected_state))
      time.sleep(1)

  @retry.retry(**RETRY_PARAMS)
  def ImportConfig(self, yaml_content):
    data = {'value': yaml_content}
    response = requests.post(
        '%s/node_config/import' % self.mtt_api_url, json=data)
    response.raise_for_status()

  # TFC API

  @retry.retry(**RETRY_PARAMS)
  def GetAttempts(self, request_id):
    response = requests.get('%s/requests/%s' % (self.tfc_api_url, request_id))
    response.raise_for_status()
    return response.json().get('command_attempts', [])

  @retry.retry(**RETRY_PARAMS)
  def LeaseTasks(self, devices=None):
    """Used by TF to lease tasks from the TFC API."""
    time.sleep(10)  # Can take up to 10 seconds for a task to be leasable
    request = {
        'cluster': CLUSTER,
        'hostname': self.base_url,
        'device_infos': devices or [],
    }
    response = requests.post(
        '%s/tasks/leasehosttasks' % self.tfc_api_url, json=request)
    response.raise_for_status()
    return response.json().get('tasks', [])

  def LeaseTask(self, device):
    """Convenience method to lease a single task."""
    tasks = self.LeaseTasks(devices=[device])
    assert len(tasks) <= 1, 'Multiple tasks leased unexpectedly'
    return tasks[0] if len(tasks) == 1 else None

  @retry.retry(**RETRY_PARAMS)
  def SubmitCommandEvent(self, task, event_type, data=None):
    """Used by TF to send invocation status updates to the TFC API."""
    time.sleep(1)  # Timestamp rounded down, ensure it isn't older than attempt
    event = {
        'time': int(time.time()),
        'task_id': task['task_id'],
        'attempt_id': task['attempt_id'],
        'type': event_type,
        'hostname': self.base_url,
        'data': data or {},
    }
    response = requests.post(
        '%s/command_events' % self.tfc_api_url,
        json={'command_events': [event]})
    response.raise_for_status()
    return event


def DeviceInfo(serial, state='Available'):
  """Create device information."""
  return {
      'device_serial': serial,
      'run_target': '*',
      'state': state,
  }


class DockerContainerTest(absltest.TestCase):
  """Tests that share a common docker container."""
  container = None
  has_failure = False

  @classmethod
  def GetContainer(cls):
    """Factory method to construct a container. Override to customize."""
    return MttContainer()

  @classmethod
  def setUpClass(cls):
    """Start the container."""
    super(DockerContainerTest, cls).setUpClass()
    cls.container = cls.GetContainer()
    cls.container.Start()

  def run(self, result=None):
    test_result = super().run(result)
    self.__class__.has_failure = (
        self.__class__.has_failure or not test_result.wasSuccessful())
    return test_result

  @classmethod
  def tearDownClass(cls):
    """Stop the container and dump server logs for debugging if necessary."""
    super(DockerContainerTest, cls).tearDownClass()
    if cls.has_failure:
      cls.container.DumpLogs()
    cls.container.Stop()
