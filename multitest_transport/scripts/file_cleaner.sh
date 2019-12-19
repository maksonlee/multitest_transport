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

#
# Clean up old test output/work folders.
source /root/env.sh

readonly _OUTPUT_DIR_TTL_DAYS=7
readonly _WORK_DIR_TTL_DAYS=7
readonly _MAX_DIR_TO_PROCESS=25
readonly _ARCHIVE_FILE="FILES.zip"

log() {
  echo "$(date) ${1}"
}

# Archive old test output files.
if [[ -n "${MTT_TEST_OUTPUT_DIR}" ]]; then
  log "Archiving test output files older than ${_OUTPUT_DIR_TTL_DAYS} days..."
  find "${MTT_TEST_OUTPUT_DIR}"\
    -mindepth 4 -maxdepth 4 -type d -ctime +"${_OUTPUT_DIR_TTL_DAYS}"\
    | xargs -I {} sh -c '[ ! -f "{}/${_ARCHIVE_FILE}" ] && echo {}'\
    | head -"${_MAX_DIR_TO_PROCESS}"\
    | xargs -I {} sh -c\
      'echo {} && cd {} && zip -qrm "${_ARCHIVE_FILE}" . -x\*.zip'
  log "Archiving is finished."
fi

# Clean up old test work files.
if [[ -n "${MTT_TEST_WORK_DIR}" ]]; then
  log "Cleaning test work files older than ${_WORK_DIR_TTL_DAYS} days..."
  find "${MTT_TEST_WORK_DIR}"\
    -mindepth 1 -maxdepth 1 -type d -ctime +"${_WORK_DIR_TTL_DAYS}"\
    | head -"${_MAX_DIR_TO_PROCESS}"\
    | xargs -I {} sh -c 'echo {} && rm -rf {}'
  log "Cleaning is finished."
fi

du -h --max-depth 1 "${MTT_STORAGE_PATH}"
log "Finished"
