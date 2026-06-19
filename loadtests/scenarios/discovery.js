import http from 'k6/http';
import { check, sleep } from 'k6';
import { BASE_URL } from '../k6.config.js';

export const options = {
  stages: [
    { duration: '1m', target: 10 },
    { duration: '3m', target: 20 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.02'],
  },
};

export default function () {
  const candidatesRes = http.get(`${BASE_URL}/api/v1/discovery/candidates`);

  check(candidatesRes, {
    'candidates status is 200': (r) => r.status === 200,
    'candidates response time < 500ms': (r) => r.timings.duration < 500,
    'candidates returns array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body) || Array.isArray(body.data);
      } catch {
        return false;
      }
    },
  });

  sleep(0.5);

  let candidateId = null;
  try {
    const body = JSON.parse(candidatesRes.body);
    const items = Array.isArray(body) ? body : body.data;
    if (items && items.length > 0) {
      candidateId = items[0].id;
    }
  } catch {}

  if (candidateId) {
    const analysisRes = http.get(`${BASE_URL}/api/v1/discovery/analysis/${candidateId}`);

    check(analysisRes, {
      'analysis status is 200': (r) => r.status === 200,
      'analysis response time < 1s': (r) => r.timings.duration < 1000,
      'analysis returns data': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body !== null;
        } catch {
          return false;
        }
      },
    });

    sleep(0.5);
  } else {
    sleep(1);
  }
}
