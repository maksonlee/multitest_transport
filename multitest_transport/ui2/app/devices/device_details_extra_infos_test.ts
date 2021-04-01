import {DebugElement} from '@angular/core';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {NoopAnimationsModule} from '@angular/platform-browser/animations';
import {RouterTestingModule} from '@angular/router/testing';
import {getTextContent} from 'google3/third_party/py/multitest_transport/ui2/app/testing/jasmine_util';
import {DeviceDetailsExtraInfos} from './device_details_extra_infos';
import {DevicesModule} from './devices_module';
import {DevicesModuleNgSummary} from './devices_module.ngsummary';

describe('DeviceDetailsExtraInfos', () => {
  let deviceDetailsExtraInfos: DeviceDetailsExtraInfos;
  let deviceDetailsExtraInfosFixture: ComponentFixture<DeviceDetailsExtraInfos>;
  let el: DebugElement;
  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [
        DevicesModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      aotSummaries: DevicesModuleNgSummary,
      providers: [],
    });
    deviceDetailsExtraInfosFixture =
        TestBed.createComponent(DeviceDetailsExtraInfos);
    deviceDetailsExtraInfos = deviceDetailsExtraInfosFixture.componentInstance;
    deviceDetailsExtraInfos.extraInfos = [];
    deviceDetailsExtraInfosFixture.detectChanges();
    el = deviceDetailsExtraInfosFixture.debugElement;
  });

  afterEach(() => {
    deviceDetailsExtraInfosFixture.destroy();
  });

  it('should get initialized correctly', () => {
    expect(deviceDetailsExtraInfos).toBeTruthy();
  });

  it('correctly displays a given empty list', () => {
    deviceDetailsExtraInfos.extraInfos = [];
    deviceDetailsExtraInfosFixture.detectChanges();
    expect(getTextContent(el)).toContain('No device extra infos found.');
  });

  it('correctly displays a given extra infos', () => {
    const batteryLevel = 'battery_level:80';
    deviceDetailsExtraInfos.extraInfos = [batteryLevel];
    deviceDetailsExtraInfosFixture.detectChanges();
    expect(getTextContent(el)).toContain(batteryLevel);
  });
});
