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
CLI_ZIP="${GOOGLE3_BASE}/blaze-bin/third_party/py/multitest_transport/cli/setup.zip"
CLI_DIR="$(mktemp -d)"
unzip -q "${CLI_ZIP}" -d "${CLI_DIR}"
cd "${CLI_DIR}"
# Move MTT source code under src directory
mkdir src
mv -t src multitest_transport tradefed_cluster setup.py

cat << EOF > src/VERSION
[version]
VERSION=dev
BUILD_ENVIRONMENT=dev
EOF

# We build the command line from a docker, since the local envirnoment
# changes all the time.
cat > Dockerfile << EOF
FROM ubuntu:18.04

# Ubuntu 18.04's python3-distutils is 3.6.9-1, which support python >= 3.6.7-1
# to << 3.9. Later if we want to support new version of python, we need to
# update the python3-distutils as well (may need to drop some old version
# support).

RUN apt update; apt install -y python3.6 python3.7 python3.8 python3-distutils python3-pip unzip wget zip
COPY ./requirements.txt /tmp
RUN pip3 install --upgrade setuptools pip
RUN pip3 install pex==2.0.3
RUN pip3 install -r /tmp/requirements.txt

RUN mkdir -p /protoc && \
  wget -O /protoc/protoc-3.7.1-linux-x86_64.zip https://github.com/protocolbuffers/protobuf/releases/download/v3.7.1/protoc-3.7.1-linux-x86_64.zip && \
  unzip -q -o /protoc/protoc-3.7.1-linux-x86_64.zip -d /protoc
EOF

docker build -t docker_pex .
docker run --rm --mount type=bind,source="$CLI_DIR",target=/workspace docker_pex sh -c \
  '/protoc/bin/protoc --python_out=/workspace/src/tradefed_cluster/configs/ \
    --proto_path /workspace/src/tradefed_cluster/configs/ \
    /workspace/src/tradefed_cluster/configs/lab_config.proto && \
  cd /workspace && \
  pex --python="python3.8" --python="python3.7" --python="python3.6" \
    --python-shebang="/usr/bin/env python3" \
    -D src -r requirements.txt \
    -m multitest_transport.cli.cli \
    -o mtt && \
  cd src/ && zip -r /workspace/mtt.zip * && cd .. &&
  cp mtt src/mtt_binary && \
  pex --python="python3.8" --python="python3.7" --python="python3.6" \
    --python-sheban="/usr/bin/env python3" \
    -D src -r requirements.txt \
    -m multitest_transport.cli.lab_cli \
    -o mtt_lab'
cd -

# Move the output files
OUT_DIR="$(mktemp -d)"
mv -t "${OUT_DIR}" "${CLI_DIR}/mtt" "${CLI_DIR}/mtt_lab" "${CLI_DIR}/install.sh" "${CLI_DIR}/mtt.zip"
rm -rf "${CLI_DIR}"
echo "Built ${OUT_DIR}/mtt"
echo "Built ${OUT_DIR}/mtt_lab"
echo "Built ${OUT_DIR}/install.sh"
echo "Built ${OUT_DIR}/mtt.zip"
