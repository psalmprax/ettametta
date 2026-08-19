/**
 * Frontend Analytics & Event Tracking for ettametta Dashboard
 * Integrates with PostHog endpoint via HTTP forwarding or browser SDK.
 */

interface AnalyticsEvent {
  event: string;
  distinct_id?: string;
  properties?: Record<string, unknown>;
}

export class DashboardAnalytics {
  private static instance: DashboardAnalytics;
  private apiEndpoint = '/api/v1/posthog/events';
  private distinctId: string;

  private constructor() {
    this.distinctId = this.getOrCreateDistinctId();
  }

  public static getInstance(): DashboardAnalytics {
    if (!DashboardAnalytics.instance) {
      DashboardAnalytics.instance = new DashboardAnalytics();
    }
    return DashboardAnalytics.instance;
  }

  private getOrCreateDistinctId(): string {
    if (typeof window === 'undefined') return 'server_side';
    let id = localStorage.getItem('ettametta_distinct_id');
    if (!id) {
      id = 'usr_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
      localStorage.setItem('ettametta_distinct_id', id);
    }
    return id;
  }

  public async capture(eventName: string, properties: Record<string, unknown> = {}): Promise<void> {
    if (typeof window === 'undefined') return;

    try {
      const payload: AnalyticsEvent = {
        event: eventName,
        distinct_id: this.distinctId,
        properties: {
          ...properties,
          path: window.location.pathname,
          referrer: document.referrer,
          timestamp: new Date().toISOString(),
        },
      };

      await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch {
      // Fail silently in frontend so telemetry never disrupts UX
    }
  }

  public trackVideoCreationStarted(niche: string, template: string) {
    this.capture('video_creation_started', { niche, template });
  }

  public trackVideoRenderCompleted(jobId: string, durationSec: number) {
    this.capture('video_render_completed', { jobId, durationSec });
  }

  public trackAEOOptimized(score: number, entityCount: number) {
    this.capture('aeo_optimized', { score, entityCount });
  }
}

export const analytics = DashboardAnalytics.getInstance();
