import { http, group, check, sleep } from 'k6';
import { Rate, Counter, Trend } from 'k6/metrics';

export const options = {
  scenarios: {
    // Standard Load - verify stability
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 50 },
        { duration: '2m', target: 50 },
        { duration: '30s', target: 0 },
      ],
    },
    
    // Reality Stress - Push to 500 VUs
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 100 },
        { duration: '2m', target: 500 }, // INDUSTRIAL SCALE
        { duration: '2m', target: 500 },
        { duration: '1m', target: 0 },
      ],
    },
    
    // Chaos Phase - Randomly inject faults
    chaos: {
      executor: 'per-vu-iterations',
      vus: 5,
      iterations: 10,
      startTime: '30s',
    },
  },
  
  thresholds: {
    http_req_duration: ['p(95)<1000', 'p(99)<2500'], // Relaxed for stress
    http_req_failed: ['rate<0.05'], // Allow 5% failure under chaos
  },
};

const errorRate = new Rate('errors');
const apiCalls = new Counter('api_calls');

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || '';

export default function () {
  const scenario = __SCENARIO;

  if (scenario === 'chaos') {
    group('Chaos Injection', () => {
      const types = ['latency', 'crash', 'exhaustion'];
      const type = types[Math.floor(Math.random() * types.length)];
      
      let res;
      if (type === 'latency') {
        res = http.post(`${BASE_URL}/api/v1/chaos/latency?service=video_engine&delay_ms=2000`);
      } else if (type === 'crash') {
        res = http.post(`${BASE_URL}/api/v1/chaos/crash`);
      } else {
        res = http.post(`${BASE_URL}/api/v1/chaos/exhaustion?platform=youtube`);
      }
      
      check(res, { 'chaos injection successful': (r) => r.status === 200 });
      sleep(randomIntBetween(5, 15));
    });
    return;
  }

  // Active Load Scenarios
  group('Discovery Lifecycle', () => {
    const res = http.get(`${BASE_URL}/api/v1/discovery/trends?niche=ViralEconomics`, {
      headers: { 'Authorization': `Bearer ${API_KEY}` },
    });
    check(res, { 'discovery status 200': (r) => r.status === 200 });
    apiCalls.add(1);
    errorRate.add(res.status !== 200);
  });

  group('Video Generation Spike', () => {
    // Simulate complex requests that trigger Resource Governor
    const payload = JSON.stringify({
      niche: 'AI_AGENT_STRESS',
      strategy: 'CHAOS_PROOF_EVOLUTION',
      priority: 'high'
    });
    
    const res = http.post(`${BASE_URL}/api/v1/video/generate/evolve`, payload, {
      headers: { 
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json' 
      },
    });
    
    check(res, { 'generation accepted': (r) => [200, 202, 429].includes(r.status) });
    sleep(1);
  });
}

function randomIntBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}