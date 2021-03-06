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

import {Pipe, PipeTransform} from '@angular/core';
import {TestPackageInfo} from '../services/mtt_models';


/**
 * Returns a string containing the name and version of the test package
 */
@Pipe({name: 'testPackageInfo'})
export class TestPackageInfoPipe implements PipeTransform {
  transform(testPackage: TestPackageInfo): string {
    if (!testPackage || !testPackage.name || !testPackage.version) {
      return '';
    }
    let output = `${testPackage.name} ${testPackage.version}`;
    if (testPackage.build_number) {
      output += ` (${testPackage.build_number})`;
    }
    return output;
  }
}
