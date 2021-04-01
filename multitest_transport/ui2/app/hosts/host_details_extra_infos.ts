/**
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

import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import {assertRequiredInput} from '../shared/util';


/** Displaying extra info list of a host. */
@Component({
  selector: 'host-details-extra-infos',
  styleUrls: ['host_details_extra_infos.css'],
  templateUrl: 'host_details_extra_infos.ng.html',
})
export class HostDetailsExtraInfos implements OnChanges, OnInit {
  @Input() extraInfos!: string[];

  displayedColumns: string[] = [
    'extraInfo',
  ];

  ngOnChanges(changes: SimpleChanges) {
    if (changes['extraInfos']) {
      this.extraInfos = changes['extraInfos'].currentValue;
    }
  }

  ngOnInit() {
    assertRequiredInput(
        this.extraInfos, 'extraInfos', 'host-details-extra-infos');
  }
}
