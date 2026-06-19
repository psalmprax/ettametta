import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from '../k6.config.js';

export const options = {
  stages: [
    { duration: '1m', target: 5 },
    { duration: '3m', target: 15 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.02'],
  },
};

export default function () {
  const payload = JSON.stringify({
    title: `Load Test Video ${Date.now()}`,
    style: 'viral',
    script: 'This is a load test video generation request.',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const createRes = http.post(`${BASE_URL}/api/v1/video/jobs`, payload, params);

  check(createRes, {
    'create job status is 201': (r) => r.status === 201 || r.status === 200,
    'create job response time < 1s': (r) => r.timings.duration < 1000,
    'create job returns id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.id !== undefined || body.job_id !== undefined;
      } catch {
        return false;
      }
    },
  });

  let jobId = null;
  try {
    const body = JSON.parse(createRes.body);
    jobId = body.id || body.job_id;
  } catch {}

  sleep(1);

  if (jobId) {
    const statusRes = http.get(`${BASE_URL}/api/v1/video/jobs/${jobId}`);

    check(statusRes, {
      'job status is 200': (r) => r.status === 200,
      'job status response time < 500ms': (r) => r.timings.duration < 500,
      'job has valid status': (r) => {
        try {
          const body = JSON.parse(r.body);
          const validStatuses = ['pending', 'processing', 'completed', 'failed'];
          return validStatuses.includes(body.status);
        } catch {
          return false;
        }
      },
    });
  }

  sleep(2);
}
