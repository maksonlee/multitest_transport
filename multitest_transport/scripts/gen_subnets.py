#!/usr/bin/env python3
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
"""This script divides an IPv4 or IPv6 network into subnets.

Sample I/O:

$ ./gen_subnets.py 192.168.1.0/24 27 2 192.168.1.33
192.168.1.0 192.168.1.64

$ ./gen_subnets.py 2001:db8::/56 64 2 2001:db8:0:1::1
2001:db8:: 2001:db8:0:2::
"""

import argparse
import ipaddress
import sys


class PrintToStderrParser(argparse.ArgumentParser):
  """Print to stderr so that the caller doesn't get unexpected output."""

  def print_usage(self, file=None):
    super().print_usage(file if file else sys.stderr)

  def print_help(self, file=None):
    super().print_help(file if file else sys.stderr)


def main(argv, stdout):
  parser = PrintToStderrParser()
  parser.add_argument(
      'network',
      type=ipaddress.ip_network,
      help='the network to be divided into subnets. '
      'e.g., 2001:db8::/56, 192.168.1.0/24.')
  parser.add_argument(
      'subnet_prefix_length',
      type=int,
      help='the prefix length of the subnets.')
  parser.add_argument(
      'subnet_count', type=int, help='number of output subnets.')
  parser.add_argument(
      'exclude_addresses',
      metavar='exclude_address',
      nargs='*',
      type=ipaddress.ip_address,
      help='the address that the subnets should not overlap with.')
  args = parser.parse_args(argv)

  subnets = (subnet for subnet in
             args.network.subnets(new_prefix=args.subnet_prefix_length) if
             not any(addr in subnet for addr in args.exclude_addresses))
  try:
    out = [str(next(subnets).network_address) for _ in range(args.subnet_count)]
  except StopIteration as e:
    raise ValueError('%s does not have enough subnets.' % args.network) from e
  print(' '.join(out), file=stdout)


if __name__ == '__main__':
  main(sys.argv[1:], sys.stdout)
