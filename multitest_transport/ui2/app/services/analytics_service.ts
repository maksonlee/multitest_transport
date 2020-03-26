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

import {HttpEvent, HttpHandler, HttpInterceptor, HttpParams, HttpRequest} from '@angular/common/http';
import {Inject, Injectable} from '@angular/core';
import {Observable} from 'rxjs';
import {finalize, tap} from 'rxjs/operators';
import {APP_DATA, AppData} from './app_data';

// Google Analytics global site tag
declare let gtag: Function;

/** Records Google Analytics page views, events, and timing information. */
@Injectable({providedIn: 'root'})
export class AnalyticsService {
  // Google Analytics tracking ID
  private readonly trackingId?: string;
  // Metrics added to all events
  private readonly baseMetrics: object;

  constructor(@Inject(APP_DATA) data: AppData) {
    this.trackingId = data && data.analyticsTrackingId;
    this.baseMetrics = {'is_google': data && data.isGoogle ? 'True' : 'False'};
  }

  /**
   * Track a page view.
   * @param path page URL to record
   * @param title page title to record
   */
  trackLocation(path: string, title?: string) {
    if (!this.trackingId) return;
    gtag('config', this.trackingId, {
      ...this.baseMetrics,
      'page_path': path,
      'page_title': title || '',
      'custom_map': {'dimension1': 'is_google'},
    });
  }

  /**
   * Track an event.
   * @param category event category to record
   * @param action event action to record
   */
  trackEvent(category: string, action: string) {
    if (!this.trackingId) return;
    gtag('event', action, {
      ...this.baseMetrics,
      'event_category': category,
    });
  }

  /**
   * Track an exception.
   * @param description error message to record
   */
  trackError(description: string) {
    if (!this.trackingId) return;
    gtag('event', 'exception', {
      ...this.baseMetrics,
      'description': description,
    });
  }

  /**
   * Track a duration.
   * @param category relevant event category
   * @param action relevant event action
   * @param millis duration to record
   */
  trackTiming(category: string, action: string, millis: number) {
    if (!this.trackingId) return;
    gtag('event', 'timing_complete', {
      ...this.baseMetrics,
      'event_category': category,
      'name': action,
      'value': millis,
    });
  }
}

/** HTTP parameters that hold additional Google Analytics metadata. */
export class AnalyticsParams extends HttpParams {
  constructor(readonly category: string, readonly action: string) {
    super();
  }
}

/** HTTP interceptor that sends request information to Google Analytics. */
@Injectable()
export class AnalyticsInterceptor implements HttpInterceptor {
  constructor(private readonly analytics: AnalyticsService) {}

  /** Track HTTP requests, their duration, and errors received. */
  intercept<T>(req: HttpRequest<T>, next: HttpHandler):
      Observable<HttpEvent<T>> {
    const params = req.params;
    if (!(params instanceof AnalyticsParams)) {
      return next.handle(req);  // skip tracking
    }

    // record request start
    const start = Date.now();
    this.analytics.trackEvent(params.category, params.action);

    return next.handle(req).pipe(
        tap({
          // record error response
          error: error => {
            this.analytics.trackError(
                `${params.category} ${params.action}: ${error.status}`);
          }
        }),
        finalize(() => {
          // record request duration
          this.analytics.trackTiming(
              params.category, params.action, Date.now() - start);
        }));
  }
}
