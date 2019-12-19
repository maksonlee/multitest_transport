#!/bin/bash
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

# Builds the CLI locally with pex (c.f. release/kokoro.sh).
set -e

SCRIPT_PATH="$(realpath "$0")"
SCRIPT_ROOT="$(dirname "${SCRIPT_PATH}")"
GOOGLE3_BASE="$(realpath "${SCRIPT_ROOT}/../../../../")"

# Generate the CLI zip
cd "${SCRIPT_ROOT}"
blaze build :setup_zip

# Unzip files
CLI_ZIP="${GOOGLE3_BASE}/blaze-genfiles/third_party/py/multitest_transport/cli/setup.zip"
CLI_DIR="$(mktemp -d)"
unzip -q "${CLI_ZIP}" -d "${CLI_DIR}"
cd "${CLI_DIR}"
# Move MTT source code under src directory
mkdir src
mv -t src multitest_transport
mv -t src tradefed_cluster

# Build protobuf py with public protoc
mkdir protoc
PROTOC_ZIP=protoc-3.7.1-linux-x86_64.zip
wget -O protoc/$PROTOC_ZIP https://github.com/protocolbuffers/protobuf/releases/download/v3.7.1/$PROTOC_ZIP
unzip -q -o protoc/$PROTOC_ZIP -d protoc
./protoc/bin/protoc --python_out=. ./src/tradefed_cluster/configs/lab_config.proto

cat << EOF > src/VERSION
[version]
VERSION=dev
BUILD_ENVIRONMENT=dev
EOF

# Pex the packages (requires pip install pex==2.0.3)
# TODO: Migrate to python3 after Jan release.
pex --python="python2.7" -D src -r requirements.txt -m multitest_transport.cli.cli -o mtt
cp mtt src/mtt_binary
pex --python="python2.7" -D src -r requirements.txt -m multitest_transport.cli.lab_cli -o mtt_lab
cd -

# Move the output files
OUT_DIR="$(mktemp -d)"
mv -t "${OUT_DIR}" "${CLI_DIR}/mtt" "${CLI_DIR}/mtt_lab"
rm -rf "${CLI_DIR}"
echo "Built ${OUT_DIR}/mtt"
echo "Built ${OUT_DIR}/mtt_lab"
