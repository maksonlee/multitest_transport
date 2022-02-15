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

set -e

# Kill all subprocesses when this script stops.
trap "echo cleaning up... && pkill -P $$ -TERM" SIGINT SIGTERM EXIT

readonly SCRIPT_PATH="$(realpath "$0")"
readonly SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"
readonly NETDATA_STREAM_API_KEY="2ba5b231-875d-4d39-82b0-adafd4c977d9"

# Set environment defaults
ADB_VERSION="$(adb version | grep -oP "Version \K(.*)")"
ADB_VERSION=${ADB_VERSION:-"UNKNOWN"}
HTTPLIB2_CA_CERTS=${HTTPLIB2_CA_CERTS:-"/etc/ssl/certs/ca-certificates.crt"}
MTT_HOSTNAME="$(hostname)"
MTT_VERSION=${MTT_VERSION:-"dev"}
MTT_USER="$USER"

# Parse command line arguments
WORKING_DIR="."
LIVE_RELOAD="false"
LOG_LEVEL="info"
MTT_HOST="0.0.0.0"
MTT_CONTROL_SERVER_PORT=8000
STORAGE_PATH="/tmp/mtt"
FILE_SERVICE_ONLY="false"
SQL_DATABASE_URI="mysql+pymysql://root@/ats_db"
MTT_CONTROL_SERVER_URL="http://localhost:8000"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --bind_address) MTT_HOST="$2";;
    --port) MTT_CONTROL_SERVER_PORT="$2";;
    --storage_path) STORAGE_PATH="$2";;
    --working_dir) WORKING_DIR="$2";;
    --live_reload) LIVE_RELOAD="$2";;
    --file_service_only) FILE_SERVICE_ONLY="$2";;
    --log_level) LOG_LEVEL="$2";;
    --dev_mode) DEV_MODE="$2";;
    --sql_database_uri) SQL_DATABASE_URI="$2";;
    --control_server_url) MTT_CONTROL_SERVER_URL="$2";;
    *) echo "Unknown argument $1"; exit 1; # fail-fast on unknown key
  esac
  shift # skip key
  shift # skip value
done

# Change working directory
cd "${WORKING_DIR}"
MTT_PYTHON_PATH="$(pwd):${PYTHONPATH}"
MTT_PYTHON="python3.8"

# Set dependent variables
MTT_PORT="${MTT_CONTROL_SERVER_PORT}"
MTT_CORE_PORT="$((${MTT_CONTROL_SERVER_PORT}+1))"
MTT_TFC_PORT="$((${MTT_CONTROL_SERVER_PORT}+2))"
FILE_SERVER_PORT="$((${MTT_CONTROL_SERVER_PORT}+6))"
DATASTORE_EMULATOR_PORT="$((${MTT_CONTROL_SERVER_PORT}+7))"
NETDATA_PORT="$((${MTT_CONTROL_SERVER_PORT}+8))"

# Create storage directory if it doesn't exist
if [[ ! -d "$STORAGE_PATH" ]]; then
  echo "Storage path $STORAGE_PATH does not exist. Creating..."
  mkdir -p "$STORAGE_PATH"
fi

# Create netdata directories if they don't exist
if [[ ! -d "$STORAGE_PATH/netdata" ]]; then
  echo "Netdata path does not exist. Creating..."
  mkdir -p "$STORAGE_PATH/netdata/cache"
  mkdir -p "$STORAGE_PATH/netdata/lib"
  mkdir -p "$STORAGE_PATH/netdata/log"
fi

function start_rabbitmq_puller {
  # Start RabbitMQ puller
  echo "Starting RabbitMQ puller..."
  PYTHONPATH="${MTT_PYTHON_PATH}" \
  "${MTT_PYTHON}" -m multitest_transport.app_helper.rabbitmq_puller \
      --rabbitmq_node_port "${RABBITMQ_NODE_PORT:-5672}" \
      --target "default=http://localhost:${MTT_PORT}/_ah/queue/{queue}" \
      --target "core=http://localhost:${MTT_CORE_PORT}/_ah/queue/{queue}" \
      --target "tfc=http://localhost:${MTT_TFC_PORT}/_ah/queue/{queue}" \
      "queue.yaml" \
      &
}

function start_local_file_server {
  # Start local file server
  echo "Starting local file server..."
  NUM_FILE_SERVER_WORKERS=2
  # Uses gthread workers since the default sync workers would time out when sending large files:
  # https://docs.gunicorn.org/en/stable/design.html?highlight=gthread#asyncio-workers
  NUM_THREADS=10
  PYTHONPATH="${MTT_PYTHON_PATH}" \
  "${MTT_PYTHON}" -m gunicorn.app.wsgiapp \
      multitest_transport.file_server.file_server:flask_app \
      --chdir "${SCRIPT_DIR}" \
      --config "${SCRIPT_DIR}/file_server/gunicorn_config.py" \
      --env "STORAGE_PATH=${STORAGE_PATH}" \
      --bind ":${FILE_SERVER_PORT}" \
      --log-level "${LOG_LEVEL}" --access-logfile - \
      --workers "${NUM_FILE_SERVER_WORKERS}" \
      --worker-class "gthread" \
      --threads "${NUM_THREADS}" \
      &
}

function start_datastore_emulator {
  # Start datastore emulator
  echo "Starting datastore emulator..."
  export CLOUDSDK_PYTHON="${MTT_PYTHON}"
  GCLOUD_SDK_ROOT=$(gcloud info --format="value(installation.sdk_root)")
  DATASTORE_EMULATOR="${GCLOUD_SDK_ROOT}/platform/cloud-datastore-emulator/cloud_datastore_emulator"
  # Allocate at least 512MB of RAM to prevent OOM errors and data corruption
  JAVA="${JAVA:="java"} -Xms512m" "${DATASTORE_EMULATOR}" start \
      --host=localhost \
      --port="${DATASTORE_EMULATOR_PORT}" \
      --index_file="index.yaml" \
      --storage_file="${STORAGE_PATH}/datastore.db" \
      --consistency=1 \
      --require_indexes \
      "${STORAGE_PATH}" \
      &
}

function wait_for_datastore {
  echo "Waiting for datastore..."
  local status_url="http://localhost:${DATASTORE_EMULATOR_PORT}/"
  timeout 5m \
    bash -c "while [[ \$(curl -s ${status_url}) != \"Ok\" ]]; do sleep 1; done"
}

function start_mysql_database {
  # Skip starting DB if URI already set
  if [[ -n "${SQL_DATABASE_URI}" ]]; then return; fi

  echo "Starting MySQL database..."
  local db_name="ats_db"
  local datadir="${STORAGE_PATH}/${db_name}"
  local socket="${datadir}/mysqld.sock"
  local pidfile="${datadir}/mysqld.pid"
  # Ensure DB directory is created and initialized
  mkdir -p "${datadir}"
  chown mysql:mysql "${datadir}"
  # Start DB with specific socket/pid to prevent clashes. Does not check access
  # (system/grant tables don't need to exist), but network access is disabled.
  mysqld_safe \
    --socket="${socket}" \
    --pid-file="${pidfile}" \
    --skip-grant-tables \
    --skip-networking \
    --datadir="${datadir}" \
    &
  SQL_DATABASE_URI="mysql+pymysql://root@/${db_name}?unix_socket=${socket}"
}

function start_main_server {
  # ATS may fail to start (e.g. config not reloaded, cron jobs not started) if
  # the datastore is not ready, so wait for it.
  wait_for_datastore
  # Start Android Test Station
  echo "Starting main server..."
  PYTHONFAULTHANDLER=1 \
  PYTHONPATH="${MTT_PYTHON_PATH}" \
  FTP_PROXY="$FTP_PROXY" \
  HTTP_PROXY="$HTTP_PROXY" \
  HTTPS_PROXY="$HTTPS_PROXY" \
  NO_PROXY="$NO_PROXY" \
  HTTPLIB2_CA_CERTS="$HTTPLIB2_CA_CERTS" \
  ADB_VERSION="$ADB_VERSION" \
  DEV_MODE="$DEV_MODE" \
  MTT_FILE_SERVER_ROOT="$STORAGE_PATH" \
  MTT_FILE_SERVER_URL="http://localhost:$FILE_SERVER_PORT/" \
  MTT_NETDATA_URL="http://localhost:$NETDATA_PORT/" \
  MTT_GOOGLE_OAUTH2_CLIENT_ID="$MTT_GOOGLE_OAUTH2_CLIENT_ID" \
  MTT_GOOGLE_OAUTH2_CLIENT_SECRET="$MTT_GOOGLE_OAUTH2_CLIENT_SECRET" \
  MTT_VERSION="$MTT_VERSION" \
  MTT_HOSTNAME="$MTT_HOSTNAME" \
  MTT_STORAGE_PATH="$STORAGE_PATH" \
  MTT_SQL_DATABASE_URI="${SQL_DATABASE_URI}" \
  MTT_USER="$MTT_USER" \
  "${MTT_PYTHON}" -m multitest_transport.app_helper.launcher \
      --application_id="mtt" \
      --host="${MTT_HOST}" \
      --port="${MTT_CONTROL_SERVER_PORT}" \
      --datastore_emulator_host="localhost:$DATASTORE_EMULATOR_PORT" \
      --log_level="${LOG_LEVEL}" \
      --live_reload="${LIVE_RELOAD}" \
      --module "default=multitest_transport.server:APP" \
      --module "core=multitest_transport.server:CORE" \
      --module "tfc=tradefed_cluster.server:TFC" \
      --init "core:/init" \
      &
}

function start_file_cleaner {
  # Start file cleaner
  echo "Starting file cleaner..."
  PYTHONPATH="${MTT_PYTHON_PATH}" \
  MTT_STORAGE_PATH="$STORAGE_PATH" \
  "${MTT_PYTHON}" -m multitest_transport.file_cleaner.file_cleaner \
      --control_server_url="${MTT_CONTROL_SERVER_URL}" \
      &
}

function start_netdata {
  # Start Netdata
  echo "Starting Netdata..."

cat << EOF > ${STORAGE_PATH}/netdata/stream.conf
[${NETDATA_STREAM_API_KEY}]
  enabled = yes
EOF

  netdata -c "${SCRIPT_DIR}/scripts/netdata/netdata.conf" \
      -p "${NETDATA_PORT}" \
      -W set global "cache directory" "${STORAGE_PATH}/netdata/cache" \
      -W set global "config directory" "${STORAGE_PATH}/netdata" \
      -W set global "lib directory" "${STORAGE_PATH}/netdata/lib" \
      -W set global "log directory" "${STORAGE_PATH}/netdata/log" \
      -W set health "health configuration directory" "${SCRIPT_DIR}/scripts/netdata/health.d" \
      &
}

function start_netdata_headless_collector {
  # Start Netdata headless collector
  echo "Starting Netdata..."

  local control_server_hostname=$(echo ${MTT_CONTROL_SERVER_URL} | sed "s,^\([^:/]\+://\)\?\([^:/]\+\)\(:\([0-9]\{1\,5\}\)\)\?\+.*$,\2,g")
  local control_server_port=$(echo ${MTT_CONTROL_SERVER_URL} | sed "s,^\([^:/]\+://\)\+\([^:/]\+\)\(:\([0-9]\{1\,5\}\)\)\?\+.*$,\4,g")
  local control_server_stream_port=$((${control_server_port:-80}+8))

cat << EOF > ${STORAGE_PATH}/netdata/stream.conf
[stream]
  enabled = yes
  destination = ${control_server_hostname}
  api key = ${NETDATA_STREAM_API_KEY}
  default port = ${control_server_stream_port}
EOF

  echo "Streaming Netdata metrics to ${control_server_hostname}:${control_server_stream_port}"

  netdata -c "${SCRIPT_DIR}/scripts/netdata/netdata.conf" \
      -W set global "cache directory" "${STORAGE_PATH}/netdata/cache" \
      -W set global "config directory" "${STORAGE_PATH}/netdata" \
      -W set global "lib directory" "${STORAGE_PATH}/netdata/lib" \
      -W set global "log directory" "${STORAGE_PATH}/netdata/log" \
      -W set global "memory mode" none \
      -W set health enabled no \
      -W set web enabled no \
      &
}

if [ $FILE_SERVICE_ONLY == "false" ]
then
  start_local_file_server
  start_datastore_emulator
  start_mysql_database
  start_rabbitmq_puller
  start_main_server
  start_file_cleaner
  start_netdata
else
  start_local_file_server
  start_file_cleaner
  start_netdata_headless_collector
fi
wait
