import { http, group, check } from 'k6';
import { Rate, Counter, Trend } from 'k6/metrics';

export const options = {
  scenarios: {
    // Smoke test - verify basic functionality
    smoke: {
      executor: 'per-vu-iterations',
      vus: 1,
      iterations: 5,
      maxDuration: '1m',
    },
    
    // Load test - normal usage
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 10 },   // Ramp up
        { duration: '1m', target: 10 },    // Steady
        { duration: '30s', target: 50 },    // Peak
        { duration: '1m', target: 50 },    // Hold
        { duration: '30s', target: 0 },     // Ramp down
      ],
      maxDuration: '5m',
    },
    
    // Stress test - push beyond capacity
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 100 },
        { duration: '2m', target: 100 },
        { duration: '1m', target: 200 },
        { duration: '2m', target: 200 },
        { duration: '1m', target: 0 },
      ],
      maxDuration: '8m',
    },
    
    // Spike test - sudden increase
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 10 },
        { duration: '30s', target: 100 },  // Spike
        { duration: '1m', target: 100 },
        { duration: '10s', target: 0 },
      ],
      maxDuration: '3m',
    },
  },
  
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
    http_reqs: ['rate>100'],
  },
};

// Custom metrics
const errorRate = new Rate('errors');
const requestDuration = new Trend('request_duration');
const apiCalls = new Counter('api_calls');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || '';

// Test scenarios
export default function () {
  group('Health Check', () => {
    const res = http.get(`${BASE_URL}/health`);
    check(res, { 'health check status': (r) => r.status === 200 });
  });

  group('Authentication', () => {
    // Login
    const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
      email: 'test@example.com',
      password: 'testpassword',
    }), { headers: { 'Content-Type': 'application/json' } });
    
    check(loginRes, {
      'login status 200': (r) => r.status === 200,
      'login returns token': (r) => r.json('access_token') !== undefined,
    });
    
    errorRate.add(loginRes.status !== 200);
    requestDuration.add(loginRes.timings.duration);
  });

  group('Discovery API', () => {
    const res = http.get(`${BASE_URL}/api/v1/discovery/trends?niche=Technology`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
    });
    
    check(res, {
      'discovery returns 200': (r) => r.status === 200,
      'discovery has data': (r) => r.json('data') !== undefined,
    });
    
    errorRate.add(res.status !== 200);
    requestDuration.add(res.timings.duration);
    apiCalls.add(1);
  });

  group('Analytics API', () => {
    const res = http.get(`${BASE_URL}/api/v1/analytics/stats/summary`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
    });
    
    check(res, {
      'analytics returns 200': (r) => r.status === 200,
    });
    
    errorRate.add(res.status !== 200);
  });

  group('Publishing API', () => {
    const res = http.get(`${BASE_URL}/api/v1/publish/history`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
    });
    
    check(res, {
      'publish history returns 200': (r) => r.status === 200,
    });
  });

  group('Monetization API', () => {
    const res = http.get(`${BASE_URL}/api/v1/monetization/report`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
    });
    
    check(res, {
      'monetization returns 200': (r) => r.status === 200,
    });
  });
}

// Setup and teardown
export function setup() {
  // Login and get token
  const res = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
    email: 'test@example.com',
    password: 'testpassword',
  }), { headers: { 'Content-Type': 'application/json' } });
  
  const token = res.json('access_token');
  return { token };
}

export function teardown(data) {
  console.log(`Test completed. API calls: ${apiCalls.values}`);
}