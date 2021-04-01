import {Inject, Injectable} from '@angular/core';

import {APP_DATA, AppData} from './app_data';


/** A interface to collect user feedbacks. */
@Injectable({
  providedIn: 'root',
})
export class FeedbackService {
  constructor(
      @Inject(APP_DATA) readonly appData: AppData,
  ) {}

  startSurvey(trigger: string) {
    // TODO: Implement feedbackService.
  }
}
