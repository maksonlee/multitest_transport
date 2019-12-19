/**
 * Copyright 2019 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Device Info
 */
export declare interface DeviceInfo {
  /** device battery_level */
  readonly battery_level: string;
  /** build_id:  Current build ID in the device */
  readonly build_id?: string;
  /** cluster: physical cluster */
  readonly cluster?: string;
  /** device_serial: Serial identifying the device. It should be unique. */
  readonly device_serial: string;
  /** device_type: device type (e.g. marlin) */
  readonly device_type?: string;
  /** hidden: device is hidden or not */
  readonly hidden?: boolean;
  /** hostname: The name of the host this device is connected to. */
  readonly hostname?: string;
  /** mac_address: device mac address */
  readonly mac_address?: string;
  /** product: Device product (e.g. flounder) */
  readonly product: string;
  /** product_variant: device product variant */
  readonly product_variant?: string;
  /** run_target: device run target */
  readonly run_target?: string;
  /** sdk_version: SDK version of the device's build */
  readonly sdk_version?: string;
  /** sim_operator: sim card operator */
  readonly sim_operator?: string;
  /** sim_state: sim card state */
  readonly sim_state?: string;
  /** state: device state */
  readonly state: string;
  /** timestamp: update timestamp */
  readonly timestamp: string;
}

/**
 * Response for device list api call
 *
 * device_infos: a list of DeviceInfo
 * more: indicate weather there are more results
 */
export declare interface DeviceInfosResponse {
  device_infos?: DeviceInfo[];
}

/**
 * The status of a test invocation
 */
export declare interface InvocationStatus {
  readonly test_group_statuses?: TestGroupStatus[];
}

/**
 *  A TFC request to run a test
 */
export declare interface Request {
  /** request id */
  readonly id: string;
  /** command to run the test */
  readonly command_line?: string;
  /** time (seconds) to wait in queue before automatically cancelling */
  readonly queue_timeout_seconds?: number;
  /** why the request was cancelled */
  readonly cancel_reason?: string;
  /** device selection rules */
  readonly run_target?: string;
  /** number of times to run the test */
  readonly run_count?: number;
  /** number of shards (devices) to use */
  readonly shard_count?: number;
  /** state of the request */
  readonly state: RequestState;
  /** maximum number of times to retry if at least one test fails */
  readonly max_retry_on_test_failures?: number;
  /** List of children command */
  commands?: Command[];
  /** List of children command attempts */
  command_attempts?: CommandAttempt[];
}

/**
 * Possibles states for a TFC request
 */
export enum RequestState {
  UNKNOWN,
  QUEUED,
  RUNNING,
  CANCELED,
  COMPLETED,
  ERROR,
}

/**
 * The progress of a test group.
 */
export declare interface TestGroupStatus {
  readonly name: string;
  readonly total_test_count?: number;
  readonly completed_test_count?: number;
  readonly failed_test_count?: number;
  readonly is_complete?: boolean;
  readonly elapsed_time?: number;
  readonly failure_message?: string;
}

/** A TFC command */
export declare interface Command {
  /** command id */
  readonly id: string;
  /** id for the parent request */
  readonly request_id: string;
  /** state of the command */
  readonly state: CommandState;
  /** timestamp when the command started executing */
  readonly start_time?: string;
  /** timestamp when the command finished executing */
  readonly end_time?: string;
  /** timestamp when the command was created */
  readonly create_time?: string;
  /** timestamp when the command was last updated */
  readonly update_time?: string;
}

/** Possible states for a command */
export enum CommandState {
  UNKNOWN = 'UNKNOWN',
  QUEUED = 'QUEUED',
  RUNNING = 'RUNNING',
  CANCELED = 'CANCELED',
  COMPLETED = 'COMPLETED',
  ERROR = 'ERROR',
  FATAL = 'FATAL',
}

/** Final states for a command */
export const FINAL_COMMAND_STATES: CommandState[] = [
  CommandState.COMPLETED,
  CommandState.ERROR,
  CommandState.FATAL,
  CommandState.CANCELED,
];

/** Returns true if the status is considered final, false otherwise */
export function isFinalCommandState(state: CommandState) {
  return FINAL_COMMAND_STATES.includes(state);
}

/** A TFC command attempt */
export declare interface CommandAttempt {
  /** id of the parent request */
  readonly request_id: string;
  /** id of the parent command */
  readonly command_id: string;
  /** id of this attempt */
  readonly attempt_id: string;
  /** state of the command attempt */
  readonly state: CommandState;
  /** timestamp when the attempt started executing */
  readonly start_time?: string;
  /** timestamp when the attempt finished executing */
  readonly end_time?: string;
  /** timestamp when the attempt was created */
  readonly create_time?: string;
  /** timestamp when the attempt was last updated */
  readonly update_time?: string;
  /** user friendly error message */
  readonly error?: string;
  /** message from the generated error */
  readonly error_reason?: string;
  /** summary of the event */
  readonly summary?: string;
  /** number of tests run */
  readonly total_test_count?: number;
  /** number of tests failed */
  readonly failed_test_count?: number;
  /** number of modules failed */
  readonly failed_test_run_count?: number;
}
