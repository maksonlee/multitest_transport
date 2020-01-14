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
import enum
from tradefed_cluster.configs import lab_config

from multitest_transport.cli import command_util
from multitest_transport.cli import config
from multitest_transport.cli import gcs_file_util
from multitest_transport.cli import google_auth_util


logger = logging.getLogger(__name__)


THREAD_WAIT_TIMEOUT_SECONDS = 0.01
THREAD_POLL_INTERVAL_SECONDS = 10
_MTT_PROJECT = 'android-mtt'


class ConfigurationError(Exception):
  """Configuration-related error."""


class ExecutionError(Exception):
  """Error for execution action on host."""


class HostExecutionState(enum.Enum):
  """Execution stat for host."""
  UNKNOWN = 0
  COMPLETED = 1
  ERROR = 2


class Host(object):
  """Host is a simple wrap which has host config and host context."""

  def __init__(self, host_config, context=None):
    self._config = host_config
    self._context = context
    self._execution_state = HostExecutionState.UNKNOWN
    self._error = None

  @property
  def name(self):
    return self._config.hostname

  @property
  def config(self):
    return self._config

  @property
  def context(self):
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

  @execution_state.setter
  def execution_state(self, state):
    self._execution_state = state


def CreateHost(args):
  """Create a Host object for local host."""
  key_path = getattr(args, 'service_account_json_key_path', None)
  host_config = _GetHostConfig(
      lab_config_path=args.lab_config_path,
      key_path=key_path)
  host = Host(host_config, context=command_util.CommandContext())
  # override host configs from input args.
  if key_path:
    host.config.service_account_json_key_path = key_path
  return host


def _GetHostConfig(lab_config_path, key_path=None):
  """Get host config for local hosts."""
  if not lab_config_path:
    # Without lab config path, only MTT standalone mode will be started.
    logger.debug('No lab config path set.')
    return lab_config.LabConfigPool().BuildHostConfig(
        socket.getfqdn(), cluster_name='default')
  # For dockerized tf, there should always be a lab config.
  lab_config_pool = _BuildLabConfigPool(lab_config_path, key_path)
  for hostname in [socket.gethostname(), socket.getfqdn()]:
    host_config = lab_config_pool.GetHostConfig(hostname)
    if host_config:
      return host_config
  raise ConfigurationError(
      'There is no configuration for %s or %s in %s.' % (
          socket.gethostname(), socket.getfqdn(), lab_config_path))


def _ParallelExecute(func, args, hosts):
  """Execute a func on multiple contexts parallel.

  Args:
    func: the function to run.
    args: parsed args to pass to the function.
    hosts: a list of Hosts
  """
  logger.info('Parallel executing %r on %r hosts.', func.__name__, len(hosts))
  with futures.ThreadPoolExecutor(len(hosts)) as executor:
    future_to_host = {executor.submit(func, args, host): host
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
        except Exception as e:            logger.error('Failed %s on %s: %s.', func.__name__, host.name, e)
        else:
          logger.info('Succeeded %s on %s.', func.__name__, host.name)
      # Instead of blocking on the futures.wait, we waiting with sleep,
      # since sleep can be interrupted.
      if running_futures:
        hostnames = sorted([future_to_host[running_future].name
                            for running_future in running_futures])
        logger.info(
            'Still executing %r on %r hosts: %s',
            func.__name__, len(hostnames), ', '.join(hostnames))
        time.sleep(THREAD_POLL_INTERVAL_SECONDS)


def _SequentialExecute(func, args, hosts, exit_on_error=False):
  """Execute a func on multiple contexts sequentially.

  Args:
    func: the function to run.
    args: parsed args to pass to the function.
    hosts: a list of Hosts
    exit_on_error: exit on error or continue to execute.
  """
  # Run the function on a list of remote hosts sequentially.
  for host in hosts:
    try:
      func(args, host)
    except Exception as e:        logger.exception('Failed to run "%s" on %s.', func.__name__, host.name)
      if exit_on_error:
        raise e


def _BuildHostsWithContext(host_configs, ssh_key=None, ask_sudo_password=False,
                           sudo_user=None):
  """Create contexts for hosts.

  Args:
    host_configs: a list of HostConfig objects.
    ssh_key: ssh key to login the host.
    ask_sudo_password: bool, whether to ask for sudo password.
    sudo_user: string, user to execute sudo commands.
  Returns:
    a list of Hosts
  """
  hosts = []
  login_password = None
  sudo_password = None
  for host_config in host_configs:
    host = Host(host_config)
    hosts.append(host)
    if not sudo_password and ask_sudo_password:
      sudo_password = getpass.getpass(
          'Enter the sudo password for %s@%s:' % (
              sudo_user or host_config.host_login_name, host_config.hostname))
    try:
      if ssh_key:
        host.context = _BuildHostContext(
            host_config, ssh_key=ssh_key, sudo_password=sudo_password,
            sudo_user=sudo_user)
      if not host.context:
        host.context = _BuildHostContext(
            host_config, sudo_password=sudo_password, sudo_user=sudo_user)
      if not host.context and login_password:
        host.context = _BuildHostContext(
            host_config,
            login_password=login_password,
            sudo_password=sudo_password, sudo_user=sudo_user)
      if not host.context:
        # Get new password.
        login_password = getpass.getpass(
            'Enter the login password for %s@%s:' % (
                host_config.host_login_name, host_config.hostname))
        host.context = _BuildHostContext(
            host_config, login_password=login_password,
            sudo_password=sudo_password, sudo_user=sudo_user,
            raise_on_error=True)
    except Exception as e:        msg = 'Can\'t login %s, skip.' % host_config.hostname
      logger.exception(msg)
      host.error = e
      host.execution_state = HostExecutionState.ERROR
  return hosts


def _BuildHostContext(
    host_config, raise_on_error=False, login_password=None, ssh_key=None,
    sudo_password=None, sudo_user=None):
  """Build HostContext for host config."""
  sudo_user = sudo_user or host_config.host_login_name
  try:
    context = command_util.CommandContext(
        host_config.hostname, host_config.host_login_name,
        login_password=login_password, ssh_key=ssh_key,
        sudo_password=sudo_password, sudo_user=sudo_user)
    return context
  except command_util.AuthenticationError as e:
    logger.debug(e)
    if raise_on_error:
      raise e
  return None


def _WrapFuncForSetHost(func):
  """Create a wrapper for func so host's state will be set up."""

  @functools.wraps(func)
  def _Wrapper(args, host):
    """A wrapper over func so host's state will be set up."""
    if host.execution_state == HostExecutionState.ERROR:
      logger.debug(
          '%s already failed to run %s due to %s.',
          host.name, func.__name__, host.error)
      return
    if host.execution_state == HostExecutionState.COMPLETED:
      logger.debug('%s was completed for %s.', host.name, func.__name__)
      return
    try:
      func(args, host)
      host.execution_state = HostExecutionState.COMPLETED
    except Exception as e:        logger.debug(
          '%s failed to run %s due to %s.',
          host.name, func.__name__, e)
      host.error = e
      host.execution_state = HostExecutionState.ERROR
      raise e
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


class Executor(object):
  """Base executor that execute a function on a list of hosts."""

  def __init__(self, args):
    # TODO: refactor executor to make the logic clearer.
    self.args = args
    self.parallel = args.parallel
    self.exit_on_error = args.exit_on_error
    self.lab_config_path = self._GetLabConfigPath()
    self.lab_config_pool = _BuildLabConfigPool(
        self.lab_config_path,
        key_path=getattr(
            self.args, 'service_account_json_key_path', None))
    self.host_configs = self._GetHostConfigs()
    self.hosts = _BuildHostsWithContext(
        self.host_configs,
        ssh_key=args.ssh_key,
        ask_sudo_password=args.ask_sudo_password,
        sudo_user=args.sudo_user)

  def _GetLabConfigPath(self):
    """Get lab config path for the executor."""
    return config.config.lab_config_path

  def _GetHostConfigs(self):
    """Get host configs for hosts.

    Returns:
      a list of HostConfigs.
    Raises:
      NotImplementedError: not implemented in base.
    """
    raise NotImplementedError(
        '_GetHostConfigs should be implement in sub class.')

  def _PrintExecutionSummaries(self):
    """Check the execute result for hosts at the end."""
    state_to_hosts = collections.defaultdict(list)
    for host in self.hosts:
      state_to_hosts[host.execution_state].append(host)
    if state_to_hosts[HostExecutionState.COMPLETED]:
      logger.info('Completed "%s" on hosts:', self.args.func.__name__)
      for host in state_to_hosts[HostExecutionState.COMPLETED]:
        logger.info(host.name)
    error_msg = []
    if state_to_hosts[HostExecutionState.UNKNOWN]:
      msg = 'Skipped "%s" on hosts:' % self.args.func.__name__
      logger.error(msg)
      error_msg.append(msg)
      for host in state_to_hosts[HostExecutionState.UNKNOWN]:
        error_msg.append(host.name)
        logger.error(host.name)
    if state_to_hosts[HostExecutionState.ERROR]:
      msg = 'Failed "%s" on hosts:' % self.args.func.__name__
      logger.error(msg)
      error_msg.append(msg)
      for host in state_to_hosts[HostExecutionState.ERROR]:
        error_msg.append(host.name)
        logger.error(host.name)
    if error_msg:
      error_msg = '\n'.join(error_msg)
      raise ExecutionError(error_msg)

  def Execute(self):
    """Execute the function on a list of hosts."""
    try:
      f = _WrapFuncForSetHost(self.args.func)
      if self.parallel:
        _ParallelExecute(f, self.args, self.hosts)
      else:
        _SequentialExecute(
            f, self.args, self.hosts,
            exit_on_error=self.exit_on_error)
    except KeyboardInterrupt:
      logger.info('Receive KeyboardInterrupt.')
    finally:
      for host in self.hosts:
        try:
          if host.context:
            logger.debug('Closing %s.', host.name)
            host.context.Close()
        except Exception as e:            logger.error('Failed to close %s: %s.', host.name, e)
      self._PrintExecutionSummaries()


class LabExecutor(Executor):
  """Execute a function on a list of hosts under certain labs."""

  def _GetLabConfigPath(self):
    return self.args.lab_config_path

  def _GetHostConfigs(self):
    """Get host configs for clusters.

    Returns:
      a list of HostConfigs.
    """
    hosts_or_clusters = self.args.hosts_or_clusters
    if not hosts_or_clusters:
      return self.lab_config_pool.GetHostConfigs()
    host_configs = collections.OrderedDict()
    for host_or_cluster in hosts_or_clusters:
      host_config = self.lab_config_pool.GetHostConfig(host_or_cluster)
      if host_config:
        logger.debug('Found config for host %s.', host_or_cluster)
        host_configs[host_config.hostname] = host_config
        continue
      logger.debug('No host configured for %s.', host_or_cluster)
      host_configs_for_cluster = self.lab_config_pool.GetHostConfigs(
          host_or_cluster)
      if host_configs_for_cluster:
        logger.debug('Found config for cluster %s.', host_or_cluster)
        for host_config in host_configs_for_cluster:
          host_configs[host_config.hostname] = host_config
        continue
      logger.error('There is no config for %s, will skip.',
                   host_or_cluster)
    return host_configs.values()

