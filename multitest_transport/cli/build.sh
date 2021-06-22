#!/bin/bash
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

# Builds the CLI locally on a Corp host in a citc client.
set -e

SCRIPT_PATH="$(realpath "$0")"
SCRIPT_ROOT="$(dirname "${SCRIPT_PATH}")"
GOOGLE3_BASE="$(realpath "${SCRIPT_ROOT}/../../../../")"

# Generate the CLI zip
cd "${SCRIPT_ROOT}"
blaze build :setup_zip

CLI_ZIP="${GOOGLE3_BASE}/blaze-bin/third_party/py/multitest_transport/cli/setup.zip"
CLI_DIR="$(mktemp -d)"
# Unzip files
unzip -q "${CLI_ZIP}" -d "${CLI_DIR}"
CANDIDATE="$(date +%Y%m%d%H%M)"
$SCRIPT_ROOT/_build.sh --cli_dir $CLI_DIR --version dev --environment dev --release "${CANDIDATE}"

# Move the output files
OUT_DIR="$(mktemp -d)"
mv -t "${OUT_DIR}" "${CLI_DIR}/mtt" "${CLI_DIR}/mtt_lab" "${CLI_DIR}/install.sh" "${CLI_DIR}/mtt.zip"
rm -rf "${CLI_DIR}"
echo "Built ${OUT_DIR}/mtt"
echo "Built ${OUT_DIR}/mtt_lab"
echo "Built ${OUT_DIR}/install.sh"
echo "Built ${OUT_DIR}/mtt.zip"
