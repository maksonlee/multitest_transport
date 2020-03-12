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

"""A utility for running actions on multiple remote hosts."""
import collections
import functools
import getpass
import logging
import socket
import time

from concurrent import futures
from tradefed_cluster.configs import lab_config

from multitest_transport.cli import command_util
from multitest_transport.cli import gcs_file_util
from multitest_transport.cli import google_auth_util


logger = logging.getLogger(__name__)


THREAD_WAIT_TIMEOUT_SECONDS = 0.01
THREAD_POLL_INTERVAL_SECONDS = 10
_DEFAULT_DOCKERIZED_TF_IMAGE = 'gcr.io/dockerized-tradefed/tradefed:golden'
_DEFAULT_MTT_IMAGE = 'gcr.io/android-mtt/mtt:prod'
_MTT_PROJECT = 'android-mtt'


class ConfigurationError(Exception):
  """Configuration-related error."""


class ExecutionError(Exception):
  """Error for execution action on host."""


class HostExecutionState(object):
  """Execution stat for host."""
  UNKNOWN = 'UNKNOWN'
  COMPLETED = 'COMPLETED'
  ERROR = 'ERROR'


class Host(object):
  """Host is a simple wrap which has host config and host context."""

  def __init__(
      self,
      host_config,
      login_password=None,
      ssh_key=None,
      sudo_user=None,
      sudo_password=None,
      context=None):
    self._config = host_config
    self._context = context
    self._ssh_key = ssh_key
    self._login_password = login_password
    self._sudo_user = sudo_user
    self._sudo_password = sudo_password
    self._execution_step = 0
    self._execution_state = HostExecutionState.UNKNOWN
    self._execution_start_time = None
    self._execution_end_time = None
    self._error = None

  def StartExecutionTimer(self):
    self._execution_start_time = _GetCurrentTime()

  def StopExecutionTimer(self):
    self._execution_end_time = _GetCurrentTime()

  @property
  def name(self):
    return self._config.hostname

  @property
  def config(self):
    return self._config

  @property
  def context(self):
    """Get remote context for the host."""
    if not self._context:
      try:
        self.execution_state = 'Connect to host'
        self._context = command_util.CommandContext(
            self.name,
            self.config.host_login_name,
            login_password=self._login_password,
            ssh_key=self._ssh_key,
            sudo_password=self._sudo_password,
            sudo_user=self._sudo_user)
      except command_util.AuthenticationError as e:
        logger.debug(e)
        raise e
    return self._context

  @context.setter
  def context(self, context):
    self._context = context

  @property
  def error(self):
    return self._error

  @error.setter
  def error(self, error):
    self._error = error

  @property
  def execution_state(self):
    return self._execution_state

  @property
  def execution_step(self):
    return self._execution_step

  @execution_state.setter
  def execution_state(self, state):
    self._execution_step += 1
    self._execution_state = state

  @property
  def execution_time_elapsed(self):
    """Get the execution time expression in text of host command."""
    if not self._execution_start_time:
      time_status = 'not started'
      time_elapsed_sec = 0
    elif not self._execution_end_time:
      time_status = 'running'
      time_elapsed_sec = _GetCurrentTime() - self._execution_start_time
    else:
      time_status = 'ended'
      time_elapsed_sec = self._execution_end_time - self._execution_start_time
    time_elapsed_text = '%d min %d s' % (
        time_elapsed_sec // 60, time_elapsed_sec % 60)
    return 'Time elapsed: %s(%s)' % (time_elapsed_text, time_status)


def CreateHost(args):
  """Create a Host object for local host."""
  key_path = getattr(args, 'service_account_json_key_path', None)
  if not args.lab_config_path:
    # MTT standalone mode
    logger.info('No lab config path set; using standalone mode config')
    host_config = lab_config.CreateHostConfig(
        cluster_name='default',
        hostname=socket.getfqdn(),
        docker_image=_DEFAULT_MTT_IMAGE)
  else:
    host_config = _GetHostConfig(
        lab_config_path=args.lab_config_path, key_path=key_path)
    if not host_config.docker_image:
      host_config.docker_image = _DEFAULT_DOCKERIZED_TF_IMAGE
  host = Host(host_config, context=command_util.CommandContext())
  # override host configs from input args.
  if key_path:
    host.config.service_account_json_key_path = key_path
  return host


def _GetHostConfig(lab_config_path, key_path=None):
  """Get host config for local hosts."""
  # For dockerized tf, there should always be a lab config.
  lab_config_pool = _BuildLabConfigPool(lab_config_path, key_path)
  for hostname in [socket.gethostname(), socket.getfqdn()]:
    host_config = lab_config_pool.GetHostConfig(hostname)
    if host_config:
      return host_config
  raise ConfigurationError(
      'There is no configuration for %s or %s in %s.' % (
          socket.gethostname(), socket.getfqdn(), lab_config_path))


def _GetMaxWorker(args, hosts):
  """Get max_worker for thread pool.

  Args:
    args: parsed args to pass to the function.
    hosts: a list of Hosts

  Returns:
    An int, the number of max worker thread.
  """
    if args.parallel is True:
    return len(hosts)
  elif args.parallel is False or args.parallel < 1:
    return 1
    else:
    return args.parallel


def _GetCurrentTime():
  """Get the current time in int sec.

  Returns:
    An int, the current time in sec.
  """
  return int(time.time())


def _ParallelExecute(host_func, args, hosts):
  """Execute a func on multiple contexts parallel.

  Args:
    host_func: the function to run.
    args: parsed args to pass to the function.
    hosts: a list of Hosts
  """
  max_workers = _GetMaxWorker(args, hosts)
  logger.info('Parallel executing %r on %r hosts with %r parallel threads.',
              host_func.__name__, len(hosts), max_workers)
  with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_host = {executor.submit(host_func, args, host): host
                      for host in hosts}
    running_futures = future_to_host.keys()
    while running_futures:
      # The timeout is important. Without timeout, the wait will block
      # all interactions such as interrupt key.
      finished_futures, running_futures = futures.wait(
          running_futures, timeout=THREAD_WAIT_TIMEOUT_SECONDS,
          return_when=futures.FIRST_COMPLETED)
      for f in finished_futures:
        host = future_to_host[f]
        try:
          f.result()
        except Exception as e:            logger.error('Failed %s on %s: %s.', host_func.__name__, host.name, e)
        else:
          logger.info('Succeeded %s on %s.', host_func.__name__, host.name)
      # Instead of blocking on the futures.wait, we waiting with sleep,
      # since sleep can be interrupted.
      if running_futures:
        _PrintExecutionState(
            [future_to_host[running_future]
             for running_future in running_futures])
        time.sleep(THREAD_POLL_INTERVAL_SECONDS)


def _PrintExecutionState(hosts):
  """Print hosts' state."""
  state_to_host = collections.defaultdict(list)
  for host in hosts:
    state_to_host[(host.execution_step, host.execution_state)].append(host)
  for state in sorted(state_to_host.keys()):
    hosts_in_state = state_to_host.get(state)
    logger.info(
        '%r host in "%s": %s',
        len(hosts_in_state), state[1],
        ' '.join(sorted([host.name for host in hosts_in_state])))


def _SequentialExecute(host_func, args, hosts, exit_on_error=False):
  """Execute a func on multiple contexts sequentially.

  Args:
    host_func: the function to run on host.
    args: parsed args to pass to the function.
    hosts: a list of Hosts
    exit_on_error: exit on error or continue to execute.
  """
  # Run the function on a list of remote hosts sequentially.
  for host in hosts:
    try:
      host_func(args, host)
    except Exception as e:        logger.exception('Failed to run "%s" on %s.',
                       host_func.__name__, host.name)
      if exit_on_error:
        raise e


def _WrapFuncForSetHost(host_func):
  """Create a wrapper for host_func so host's state will be set up."""

  @functools.wraps(host_func)
  def _Wrapper(args, host):
    """A wrapper over host_func so host's state will be set up."""
    if host.execution_state == HostExecutionState.ERROR:
      logger.debug(
          '%s already failed to run %s due to %s.',
          host.name, host_func.__name__, host.error)
      if host.error:
        raise host.error
      return
    if host.execution_state == HostExecutionState.COMPLETED:
      logger.debug('%s was completed for %s.', host.name, host_func.__name__)
      return
    host.StartExecutionTimer()
    try:
      host_func(args, host)
      host.execution_state = HostExecutionState.COMPLETED
    except Exception as e:        logger.debug(
          '%s failed to run %s due to %s.',
          host.name, host_func.__name__, e)
      host.error = e
      host.execution_state = HostExecutionState.ERROR
      raise e
    finally:
      host.StopExecutionTimer()
  return _Wrapper


def _BuildLabConfigPool(lab_config_path, key_path=None):
  """Build lab config pool based on configured config path."""
  if not lab_config_path:
    logger.debug('No lab config path set.')
    lab_config_pool = lab_config.LabConfigPool()
  elif lab_config_path.startswith('gs:'):
    logger.debug('Use lab config path %s.', lab_config_path)
    if key_path:
      cred = google_auth_util.CreateCredentialFromServiceAccount(
          key_path,
          scopes=[google_auth_util.GCS_READ_SCOPE])
    else:
      cred = google_auth_util.GetGCloudCredential(
          command_util.CommandContext())
    gcs_client = gcs_file_util.CreateGCSClient(_MTT_PROJECT, cred)
    lab_config_pool = lab_config.LabConfigPool(
        gcs_file_util.GCSFileEnumerator(
            gcs_client, lab_config_path, lab_config.IsYaml))
  else:
    logger.debug('Use lab config path %s.', lab_config_path)
    lab_config_pool = lab_config.LabConfigPool(
        lab_config.LocalFileEnumerator(
            lab_config_path, lab_config.IsYaml))
  lab_config_pool.LoadConfigs()
  return lab_config_pool


def _PrintExecutionSummaries(hosts, func_name):
  """Check the execute result for hosts at the end."""
  state_to_hosts = collections.defaultdict(list)
  for host in hosts:
    state_to_hosts[host.execution_state].append(host)
  if state_to_hosts[HostExecutionState.COMPLETED]:
    logger.info('Completed "%s" on hosts:', func_name)
    for host in state_to_hosts[HostExecutionState.COMPLETED]:
      logger.info('%s [%s]', host.name, host.execution_time_elapsed)
  error_msg = []
  if state_to_hosts[HostExecutionState.UNKNOWN]:
    msg = 'Skipped "%s" on hosts:' % func_name
    logger.error(msg)
    error_msg.append(msg)
    for host in state_to_hosts[HostExecutionState.UNKNOWN]:
      error_msg.append(host.name)
      logger.error('%s [%s]', host.name, host.execution_time_elapsed)
  if state_to_hosts[HostExecutionState.ERROR]:
    msg = 'Failed "%s" on hosts:' % func_name
    logger.error(msg)
    error_msg.append(msg)
    for host in state_to_hosts[HostExecutionState.ERROR]:
      error_msg.append(host.name)
      logger.error('%s [%s]', host.name, host.execution_time_elapsed)
  if error_msg:
    error_msg = '\n'.join(error_msg)
    raise ExecutionError(error_msg)


def _GetHostConfigs(lab_config_pool, hosts_or_clusters):
  """Get host configs for clusters.

  Args:
    lab_config_pool: a lab config pool
    hosts_or_clusters: a list of hosts or clusters.
  Returns:
    a list of HostConfigs.
  """
  if not hosts_or_clusters:
    return lab_config_pool.GetHostConfigs()
  host_configs = collections.OrderedDict()
  for host_or_cluster in hosts_or_clusters:
    host_config = lab_config_pool.GetHostConfig(host_or_cluster)
    if host_config:
      logger.debug('Found config for host %s.', host_or_cluster)
      host_configs[host_config.hostname] = host_config
      continue
    logger.debug('No host configured for %s.', host_or_cluster)
    host_configs_for_cluster = lab_config_pool.GetHostConfigs(
        host_or_cluster)
    if host_configs_for_cluster:
      logger.debug('Found config for cluster %s.', host_or_cluster)
      for host_config in host_configs_for_cluster:
        host_configs[host_config.hostname] = host_config
      continue
    logger.error('There is no config for %s, will skip.',
                 host_or_cluster)
  return list(host_configs.values())


def Execute(args):
  """Execute a command on hosts."""
  lab_config_pool = _BuildLabConfigPool(
      args.lab_config_path,
      key_path=getattr(args, 'service_account_json_key_path', None))
  host_configs = _GetHostConfigs(lab_config_pool, args.hosts_or_clusters)
  if not host_configs:
    logger.warning('No host configured in %s for %s.',
                   args.lab_config_path,
                   args.hosts_or_clusters)
    return
  login_password = None
  if args.ask_login_password:
    login_password = getpass.getpass('Enter the login password:')
  sudo_password = None
  if args.ask_sudo_password:
    sudo_password = getpass.getpass('Enter the sudo password:')

  hosts = []
  for host_config in host_configs:
    hosts.append(
        Host(host_config,
             login_password=login_password,
             ssh_key=args.ssh_key,
             sudo_password=sudo_password,
             sudo_user=args.sudo_user))
  try:
    f = _WrapFuncForSetHost(args.host_func)
    if args.parallel:
      _ParallelExecute(f, args, hosts)
    else:
      _SequentialExecute(
          f, args, hosts,
          exit_on_error=args.exit_on_error)
  except KeyboardInterrupt:
    logger.info('Receive KeyboardInterrupt.')
  finally:
    for host in hosts:
      try:
        if host.context:
          logger.debug('Closing %s.', host.name)
          host.context.Close()
      except Exception as e:          logger.error('Failed to close %s: %s.', host.name, e)
    _PrintExecutionSummaries(hosts, args.host_func.__name__)
