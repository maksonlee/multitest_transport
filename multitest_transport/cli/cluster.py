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

"""A module to handle cluster commands.

Cluster commands use Docker Swarm to manage multiple MTT slave nodes. However,
this feature is currently not working because Docker Swarm does not support
--privilege option when creating a service. See the link below for details:
https://github.com/docker/swarmkit/issues/1030
"""

import copy

from multitest_transport.cli import command_util
from multitest_transport.cli import config

CONFIG_PATH_FORMAT = '~/.config/mtt/clusters/%s.ini'


class ClusterRegistry(object):
  """A class to store cluster configs."""

  def __init__(self):
    # A model cluster config.
    self._config = config.Config(filename=None)
    self._config.DefineField('manager_host')
    self._config.DefineField('manager_join_token')
    self._config.DefineField('worker_join_token')
    self._config_map = {}

  def _GetConfigPath(self, name):
    return CONFIG_PATH_FORMAT % name

  def GetConfig(self, name):
    """Return a cluster config for a given name.

    Args:
      name: a cluster name.
    Returns:
      a cluster config.
    """
    name = name.lower()
    if name not in self._config_map:
      filename = self._GetConfigPath(name)
      field_map = copy.deepcopy(self._config.field_map)
      self._config_map[name] = config.Config(filename, field_map=field_map)
      self._config_map[name].Load()
    return self._config_map[name]


class ClusterCommandHandler(object):
  """A handler for cluster commands."""

  def __init__(self):
    self._command_map = {
        'create': self.Create,
        'add_node': self.AddNode,
        'remove_node': self.RemoveNode,
    }
    self._registry = ClusterRegistry()

  def Run(self, args):
    self._command_map[args.command](args)

  def AddParser(self, subparsers):
    """Add a command argument parser.

    Args:
      subparsers: an argparse subparsers object.
    """
    parser = subparsers.add_parser(
        'cluster', help='Create and manage MTT clusters.')
    parser.add_argument(
        'command', choices=self._command_map.keys())
    parser.add_argument('--name')
    parser.add_argument('--host', default=None)
    parser.add_argument('--token', default=None)
    parser.add_argument('--ssh_user', default=None)
    parser.set_defaults(func=self.Run)

  def Create(self, args):
    """Creates a cluster.

    This actually creates a Docker swarm and deploy a MTT service on it.

    Args:
      args: an argparse.ArgumentParser object.
    Raises:
      ValueError: if mtt_master_url or host is not set.
    """
    if not config.config.mtt_master_url:
      raise ValueError('mtt_master_url must be set.')
    if not args.host:
      raise ValueError('--host option must be set')
    context = command_util.CommandContext(host=args.host, user=args.ssh_user)
    docker_context = command_util.DockerContext(context, try_use_gcloud=False)
    cluster_config = self._registry.GetConfig(args.name)
    docker_context.Run(['swarm', 'init'])
    # TODO: get token ID and store it.
    docker_context.Run(
        [
            'service', 'create',
            '--name', 'mtt',
            '--env', 'MTT_MASTER_URL=%s' % config.config.mtt_master_url,
            '--mode', 'global',
            'gcr.io/android-mtt/mtt'])
    cluster_config.manager_host = args.host
    cluster_config.Save()

  def AddNode(self, args):
    """Adds a node to an existing cluster.

    Args:
      args: an argparse.ArgumentParser object.
    Raises:
      ValueError: if a host or a token is missing.
    """
    if not args.host:
      raise ValueError('--host must be provided')
    if not args.token:
      raise ValueError('--token must be provided')
    context = command_util.CommandContext(host=args.host, user=args.ssh_user)
    docker_context = command_util.DockerContext(context, try_use_gcloud=False)
    cluster_config = self._registry.GetConfig(args.name)
    if args.host == cluster_config.manager_host:
      raise ValueError(
          '%s is already a manager node for %s cluster' % (
              args.host, args.name))
    docker_context.Run(
        [
            'swarm', 'join',
            '--token', args.token,
            '%s:2377' % cluster_config.manager_host])

  def RemoveNode(self, args):
    """Removes a node from an existing cluster.

    Args:
      args: an argparse.ArgumentParser object.
    Raises:
      ValueError: if a host or a token is missing.
    """
    if not args.host:
      raise ValueError('--host must be provided')
    context = command_util.CommandContext(host=args.host, user=args.ssh_user)
    docker_context = command_util.DockerContext(context, try_use_gcloud=False)
    docker_context.Run(
        ['swarm', 'leave', '--force'])
