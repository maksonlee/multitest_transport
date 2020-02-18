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


readonly SCRIPT_PATH="$(realpath "$0")"
readonly SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# Set environment defaults
MTT_MASTER_PORT=8000
MTT_HOST="0.0.0.0"
ADMIN_HOST="127.0.0.1"

MTT_USER="$USER"
MTT_HOSTNAME="$(hostname)"

STORAGE_PATH="/tmp/mtt"
BLOBSTORE_ROOT="blobstore"

CONFIG_DIR="."

MTT_VERSION=${MTT_VERSION:-"dev"}
ADB_VERSION="$(adb version | grep -oP "Version \K(.*)")"
ADB_VERSION=${ADB_VERSION:-"UNKNOWN"}

FILE_WATCHER="false"

LOG_LEVEL="info"
DEV_APPSERVER_LOG_LEVEL="info"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --port) MTT_MASTER_PORT="$2";;
    --storage_path) STORAGE_PATH="$2";;
    --config_dir) CONFIG_DIR="$2";;
    --use_mtime_file_watcher) FILE_WATCHER="$2";;
    --log_level) LOG_LEVEL="$2";;
    --dev_appserver_log_level) DEV_APPSERVER_LOG_LEVEL="$2";;
    --dev_mode) DEV_MODE="$2";;
    *) echo "Unknown argument $1"; exit 1; # fail-fast on unknown key
  esac
  shift # skip key
  shift # skip value
done

# Set dependent variables
BLOBSTORE_PATH="$STORAGE_PATH/$BLOBSTORE_ROOT"
FILE_SERVER_PORT="$((${MTT_MASTER_PORT}+5))"
FILE_SERVER_PORT2="$((${MTT_MASTER_PORT}+6))"

# Create storage and blobstore folders if they don't exist
if [[ ! -d "$STORAGE_PATH" ]]; then
  echo "Storage path $STORAGE_PATH does not exist. Creating..."
  mkdir -p "$STORAGE_PATH"
fi
if [[ ! -d "$BLOBSTORE_PATH" ]]; then
  echo "Blobstore path $BLOBSTORE_PATH does not exist. Creating..."
  mkdir -p "$BLOBSTORE_PATH"
fi

# Start browsepy file server
exec browsepy \
    --directory="$STORAGE_PATH" \
    "$MTT_HOST" \
    "$FILE_SERVER_PORT" \
    &

# Start local file server
exec python3 "$SCRIPT_DIR/file_server/file_server.py" \
    --root_path="$STORAGE_PATH" \
    --port="$FILE_SERVER_PORT2" \
    &

# Start appengine server
source "$SCRIPT_DIR/scripts/api_keys.sh"
exec dev_appserver.py \
    --application=mtt \
    --host="$MTT_HOST" \
    --port="$MTT_MASTER_PORT" \
    --api_host="$ADMIN_HOST" \
    --api_port="$((${MTT_MASTER_PORT} + 3))" \
    --admin_host="$ADMIN_HOST" \
    --admin_port="$((${MTT_MASTER_PORT} + 4))" \
    --storage_path="$STORAGE_PATH" \
    --blobstore_path="$BLOBSTORE_PATH" \
    --log_level="$LOG_LEVEL" \
    --dev_appserver_log_level="$DEV_APPSERVER_LOG_LEVEL" \
    --env_var ftp_proxy="$ftp_proxy" \
    --env_var http_proxy="$http_proxy" \
    --env_var https_proxy="$https_proxy" \
    --env_var no_proxy="$no_proxy" \
    --env_var ADB_VERSION="$ADB_VERSION" \
    --env_var DEV_MODE="$DEV_MODE" \
    --env_var MTT_BLOBSTORE_PATH="$BLOBSTORE_PATH" \
    --env_var MTT_FILE_SERVER_ROOT="$STORAGE_PATH" \
    --env_var MTT_FILE_SERVER_URL="http://$MTT_HOSTNAME:$FILE_SERVER_PORT/" \
    --env_var "MTT_FILE_BROWSE_URL_FORMAT=http://{hostname}:$FILE_SERVER_PORT/browse/" \
    --env_var "MTT_FILE_OPEN_URL_FORMAT=http://{hostname}:$FILE_SERVER_PORT/open/" \
    --env_var MTT_FILE_SERVER_URL2="http://$MTT_HOSTNAME:$FILE_SERVER_PORT2/" \
    --env_var MTT_GOOGLE_API_KEY="$GOOGLE_API_KEY" \
    --env_var MTT_GOOGLE_OAUTH2_CLIENT_ID="$GOOGLE_OAUTH2_CLIENT_ID" \
    --env_var MTT_GOOGLE_OAUTH2_CLIENT_SECRET="$GOOGLE_OAUTH2_CLIENT_SECRET" \
    --env_var MTT_VERSION="$MTT_VERSION" \
    --env_var MTT_HOSTNAME="$MTT_HOSTNAME" \
    --env_var MTT_STORAGE_PATH="$STORAGE_PATH" \
    --env_var MTT_USER="$MTT_USER" \
    --automatic_restart=yes \
    --enable_host_checking=false \
    --enable_sendmail \
    --require_indexes \
    --skip_sdk_update_check=yes \
    --use_mtime_file_watcher="$FILE_WATCHER" \
    "$CONFIG_DIR/app.yaml" \
    "$CONFIG_DIR/core.yaml" \
    "$CONFIG_DIR/tfc.yaml" \
