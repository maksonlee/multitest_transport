import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import {assertRequiredInput} from 'google3/third_party/py/multitest_transport/ui2/app/shared/util';


/** Displays extra info list of a device. */
@Component({
  selector: 'device-details-extra-infos',
  styleUrls: ['device_details_extra_infos.css'],
  templateUrl: 'device_details_extra_infos.ng.html',
})
export class DeviceDetailsExtraInfos implements OnChanges, OnInit {
  @Input() extraInfos!: string[];

  displayedColumns: string[] = [
    'extraInfo',
  ];

  ngOnChanges(changes: SimpleChanges) {
  }

  ngOnInit() {
    assertRequiredInput(
        this.extraInfos, 'extraInfos', 'host-details-extra-infos');
  }
}
