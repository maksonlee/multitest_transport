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

cd /mtt

# Check if running in standalone mode
if [[ -z "${MTT_MASTER_URL}" ]]
then
  # Export environment variables for cron jobs
  printenv | sed "s/^\(.*\)$/export \1/g" > /root/env.sh

  # Start cron
  crontab /mtt/scripts/crontab
  cron

  # Start MTT server
  MTT_MASTER_URL=localhost:${MTT_MASTER_PORT}
  MTT_MASTER_LOG_DIR="${MTT_LOG_DIR}/server"
  mkdir -p "${MTT_MASTER_LOG_DIR}"
  /mtt/serve.sh \
      --storage_path "${MTT_STORAGE_PATH}" \
      --port "${MTT_MASTER_PORT}" \
      2>&1 > /dev/null | multilog s10485760 n10 "${MTT_MASTER_LOG_DIR}" &
fi

# Construct TF global config
TF_CONFIG_FILE=scripts/host-config.xml
if [[ -f "${MTT_CUSTOM_TF_CONFIG_FILE}" ]]
then
  cp "${MTT_CUSTOM_TF_CONFIG_FILE}" "${TF_CONFIG_FILE}"
fi
sed -i s/\${MTT_MASTER_URL}/"${MTT_MASTER_URL}"/g "${TF_CONFIG_FILE}"

# Start ADB and load keys
export ADB_VENDOR_KEYS=$(ls -1 /root/.android/*.adb_key | paste -sd ":" -)
adb start-server

# Start TF
mkdir -p "${MTT_TEST_WORK_DIR}"
TF_GLOBAL_CONFIG="${TF_CONFIG_FILE}"\
  TRADEFED_OPTS=-Djava.io.tmpdir="${MTT_TEST_WORK_DIR}"\
  tradefed.sh
