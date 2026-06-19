export const options = {
  stages: [
    { duration: '2m', target: 10 },  // ramp-up to 10 users
    { duration: '2m', target: 50 },  // ramp-up to 50 users
    { duration: '5m', target: 50 },  // hold at 50 users
    { duration: '2m', target: 0 },   // ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],    // less than 1% failure rate
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export { BASE_URL };
