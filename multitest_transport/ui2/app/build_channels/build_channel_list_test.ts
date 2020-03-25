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

import {LiveAnnouncer} from '@angular/cdk/a11y';
import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {of as observableOf} from 'rxjs';

import {MttClient} from '../services/mtt_client';
import {AuthorizationState} from '../services/mtt_models';
import {getTextContent} from '../testing/jasmine_util';

import {BuildChannelList} from './build_channel_list';
import {BuildChannelsModule} from './build_channels_module';
import {BuildChannelsModuleNgSummary} from './build_channels_module.ngsummary';

describe('BuildChannelList', () => {
  const BUILD_CHANNELS = [
    {
      id: 'google_drive',
      name: 'Google Drive Name',
      provider_name: 'Google Drive',
      auth_state: AuthorizationState.UNAUTHORIZED,
    },
    {id: 'local_file_store', name: 'name2', provider_name: 'Local File Store'}
  ];

  let buildChannels: BuildChannelList;
  let buildChannelsFixture: ComponentFixture<BuildChannelList>;
  let mttClient: jasmine.SpyObj<MttClient>;
  let el: DebugElement;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    mttClient = jasmine.createSpyObj('mttClient', ['getBuildChannels']);
    mttClient.getBuildChannels.and.returnValue(
        observableOf({build_channels: [...BUILD_CHANNELS]}));

    TestBed.configureTestingModule({
      imports: [BuildChannelsModule, NoopAnimationsModule, RouterTestingModule],
      aotSummaries: BuildChannelsModuleNgSummary,
      providers: [
        {provide: MttClient, useValue: mttClient},
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });
    buildChannelsFixture = TestBed.createComponent(BuildChannelList);
    el = buildChannelsFixture.debugElement;
    buildChannels = buildChannelsFixture.componentInstance;
    buildChannelsFixture.detectChanges();
  });

  it('gets initialized correctly', () => {
    expect(buildChannels).toBeTruthy();
  });

  it('calls API correctly', () => {
    expect(mttClient.getBuildChannels).toHaveBeenCalled();
    expect(buildChannels.buildChannels.length).toBe(2);
  });

  it('displays build channels correctly', () => {
    const text = getTextContent(el);
    for (const buildChannel of BUILD_CHANNELS) {
      expect(text).toContain(buildChannel.name);
    }
  });

  it('displays and announces a loading mask', () => {
    expect(liveAnnouncer.announce).toHaveBeenCalledWith('Loading', 'polite');
    expect(liveAnnouncer.announce)
        .toHaveBeenCalledWith('Build channels loaded', 'assertive');
  });
});
