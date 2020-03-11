import {LiveAnnouncer} from '@angular/cdk/a11y';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {ActivatedRoute} from '@angular/router';
import {RouterTestingModule} from '@angular/router/testing';
import {beforeEach, bootstrapTemplate, describe, it, setupModule} from 'google3/javascript/angular2/testing/catalyst';
import {BuildChannelsModule} from 'google3/third_party/py/multitest_transport/ui2/app/build_channels/build_channels_module';
// TODO Add copybara rule to exlucde absolute path
import {BuildChannelsModuleNgSummary} from 'google3/third_party/py/multitest_transport/ui2/app/build_channels/build_channels_module.ngsummary';
import {MttClient} from 'google3/third_party/py/multitest_transport/ui2/app/services/mtt_client';
import {KarmaTestEnv} from 'google3/third_party/py/multitest_transport/ui2/scuba_tests/testing/karma_env';
import {of as observableOf} from 'rxjs';

describe('BuildChannelEditPage scuba test', () => {
  const env = new KarmaTestEnv(module, {
    scuba: true,
    axe: false,
  });

  let mttClient: jasmine.SpyObj<MttClient>;
  let liveAnnouncer: jasmine.SpyObj<LiveAnnouncer>;

  beforeEach(() => {
    liveAnnouncer =
        jasmine.createSpyObj('liveAnnouncer', ['announce', 'clear']);
    mttClient = jasmine.createSpyObj(
        'mttClient', ['getBuildChannel', 'getBuildChannelProviders']);

    setupModule({
      imports: [BuildChannelsModule, NoopAnimationsModule, RouterTestingModule],
      summaries: [BuildChannelsModuleNgSummary],
      providers: [
        {provide: MttClient, useValue: mttClient},
        {
          provide: ActivatedRoute,
          useValue: {params: observableOf({'id': '123'})},
        },
        {provide: LiveAnnouncer, useValue: liveAnnouncer},
      ],
    });
  });

  it.async('can display a form with no option', async () => {
    const BUILD_CHANNEL_CONFIG = {
      id: 'google_drive',
      name: 'Test Google Drive',
      provider_name: 'Google Drive',
    };

    const BUILD_CHANNEL_PROVIDERS = [{name: 'Google Drive'}];
    mttClient.getBuildChannel.and.returnValue(
        observableOf(BUILD_CHANNEL_CONFIG));
    mttClient.getBuildChannelProviders.and.returnValue(
        observableOf({build_channel_providers: [...BUILD_CHANNEL_PROVIDERS]}));
    bootstrapTemplate(`<build-channel-edit-page></build-channel-edit-page>`);
    await env.verifyState(
        `build-channel-edit-page_no_option`, 'build-channel-edit-page');
  });

  it.async('can display a form with option', async () => {
    const BUILD_CHANNEL_CONFIG = {
      id: 'google_cloud_storage',
      name: 'Test Google Cloud Storage',
      provider_name: 'Google Cloud Storage',
      options: [{name: 'account_id', value: '3333333'}],
    };

    const BUILD_CHANNEL_PROVIDERS = [{name: 'Google Cloud Storage'}];
    mttClient.getBuildChannel.and.returnValue(
        observableOf(BUILD_CHANNEL_CONFIG));
    mttClient.getBuildChannelProviders.and.returnValue(
        observableOf({build_channel_providers: [...BUILD_CHANNEL_PROVIDERS]}));
    bootstrapTemplate(`<build-channel-edit-page></build-channel-edit-page>`);
    await env.verifyState(
        `build-channel-edit-page_with_option`, 'build-channel-edit-page');
  });
});
