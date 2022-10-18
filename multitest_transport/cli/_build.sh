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

# This file builds CLIs with CLIs' source folder.
# It is used by local build and kokoro build.
set -eux

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --cli_dir) CLI_DIR="$2";;
    --version) VERSION="$2";;
    --release) RELEASE="$2";;
    --environment) ENVIRONMENT="$2";;
    *) echo "Unknown argument $1"; exit 1; # fail-fast on unknown key
  esac
  shift # skip key
  shift # skip value
done

CLI_DIR=$(readlink -f "${CLI_DIR}")
pushd "${CLI_DIR}"
# Move MTT source code under src directory
mkdir src
mv -t src multitest_transport tradefed_cluster setup.py

cat << EOF > src/VERSION
[version]
VERSION=${VERSION}
BUILD_ENVIRONMENT=${ENVIRONMENT}
EOF

chmod +w src/multitest_transport/cli/version.py
cat << EOF > src/multitest_transport/cli/version.py
VERSION = "${VERSION}"
BUILD_ENVIRONMENT = "${ENVIRONMENT}"
EOF

chmod +w src/setup.py
# setup.py's version must obey pep-440.
sed -i "s/VERSION =.*/VERSION = \"${RELEASE}\"/" src/setup.py

cat << EOF > Dockerfile
FROM ubuntu:18.04
ENV LANG=C.UTF-8

# Ubuntu 18.04's python3-distutils is 3.6.9-1, which support python >= 3.6.7-1
# to << 3.9. Later if we want to support new version of python, we need to
# update the python3-distutils as well (may need to drop some old version
# support).

RUN export DEBIAN_FRONTEND=noninteractive; apt update -qq; apt install -y -qq unzip wget zip software-properties-common;
# Add deadsnakes for different versions of python and distutils
RUN add-apt-repository ppa:deadsnakes/ppa
RUN export DEBIAN_FRONTEND=noninteractive; apt update -qq; apt install -y -qq \
  python3.7 python3.8 python3.9 python3.10 \
  python3-distutils python3-pip \
  python3.9-distutils python3.10-distutils python3.10-dev

# Set minimal Python version that client supports.
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1000

COPY ./requirements.txt /tmp
RUN pip3 install --upgrade setuptools pip
RUN pip3 install pex==2.1.94
RUN pip3 install -r /tmp/requirements.txt
RUN pip3 install --upgrade keyrings.alt

# Upgrade to the latest verified version of protoc which supports python3.10.
RUN mkdir -p /protoc && \
  wget --no-verbose -O /protoc/protoc-3.20.1-linux-x86_64.zip https://github.com/protocolbuffers/protobuf/releases/download/v3.20.1/protoc-3.20.1-linux-x86_64.zip && \
  unzip -q -o /protoc/protoc-3.20.1-linux-x86_64.zip -d /protoc
EOF

docker pull gcr.io/android-mtt/pex:latest
docker build -t docker_pex . --cache-from gcr.io/android-mtt/pex:latest

cat << EOF > inside_docker_build.sh
# Build python file from proto
/protoc/bin/protoc --python_out=/workspace/src/tradefed_cluster/configs/ \
  --proto_path /workspace/src/tradefed_cluster/configs/ \
  /workspace/src/tradefed_cluster/configs/lab_config.proto

cd /workspace
# Build mtt pex package.
pex --python="python3.10" --python="python3.9" --python="python3.8" --python="python3.7" \
  --python-shebang="/usr/bin/env python3" \
  -D src -r requirements.txt \
  -m multitest_transport.cli.cli \
  -o mtt
# Build zip file include all mtt source.
cd src/
zip -r /workspace/mtt.zip *
cd ..

# Build mtt_lab pex package.
cp mtt src/mtt_binary
pex --python="python3.10" --python="python3.9" --python="python3.8" --python="python3.7" \
  --python-sheban="/usr/bin/env python3" \
  -D src -r requirements.txt \
  -m multitest_transport.cli.lab_cli \
  -o mtt_lab
EOF
chmod +x inside_docker_build.sh

docker run --rm --mount type=bind,source="$CLI_DIR",target=/workspace docker_pex sh -c /workspace/inside_docker_build.sh
cd -

popd
