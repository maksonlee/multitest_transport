/**
 * @license
 * Copyright 2020 Google LLC
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
 * Keeps the window active when executing actions by playing inaudible audio.
 * This prevents timers from being throttled, which would cause issues for
 * actions that require sending multiple HID events.
 */
export class ExecutionWakeLock {
  private audioContext: AudioContext|undefined;
  private gainNode: GainNode|undefined;
  private oscillator: OscillatorNode|undefined;

  /**
   * Lazily creates a 1Hz inaudible audio wave since the audio context must be
   * created in response to user interaction.
   */
  private initialize() {
    if (!this.audioContext) {
      this.audioContext = new AudioContext();
    }
    if (!this.gainNode) {
      this.gainNode = this.audioContext.createGain();
      this.gainNode.gain.value = 0.001;  // low non-zero volume
      this.gainNode.connect(this.audioContext.destination);
    }
    if (!this.oscillator) {
      this.oscillator = this.audioContext.createOscillator();
      this.oscillator.frequency.value = 1;  // 1Hz inaudible sine wave
      this.oscillator.start();  // not yet connected to the output
    }
  }

  /** Plays the audio by connecting it the output. */
  acquire() {
    this.initialize();
    this.oscillator!.connect(this.gainNode!);
  }

  /** Stops the audio by disconnecting it from the output. */
  release() {
    if (this.oscillator) {
      this.oscillator.disconnect();
    }
  }
}
