/**
 * Load Test Script for ettametta API
 * Run with: k6 run scripts/load_test.js
 * 
 * Install k6: https://k6.io/docs/getting-started/installation/
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export const options = {
    stages: [
        { duration: '30s', target: 10 },   // Ramp up to 10 users
        { duration: '1m', target: 10 },     // Stay at 10 users
        { duration: '30s', target: 50 },   // Ramp up to 50 users
        { duration: '2m', target: 50 },    // Stay at 50 users
        { duration: '30s', target: 100 },  // Ramp up to 100 users
        { duration: '2m', target: 100 },   // Stay at 100 users
        { duration: '1m', target: 0 },     // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'],  // 95% of requests should be < 500ms
        errors: ['rate<0.1'],              // Error rate should be < 10%
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_TOKEN = __ENV.API_TOKEN || ''; // Use et_token or INTERNAL_API_TOKEN

const headers = {
    'Content-Type': 'application/json',
    ...(API_TOKEN ? { 'Authorization': `Bearer ${API_TOKEN}` } : {}),
};

export default function () {
    // Test 1: Health check
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
        'health status is 200': (r) => r.status === 200,
    });

    // Test 2: Discovery search
    const discoveryRes = http.get(
        `${BASE_URL}/api/discovery/search?topic=AI`,
        { headers }
    );
    check(discoveryRes, {
        'discovery returns 200': (r) => r.status === 200,
        'discovery has results': (r) => r.status === 200 && r.json('candidates') !== undefined,
    });
    errorRate(discoveryRes.status !== 200);

    // Test 3: Analytics
    const analyticsRes = http.get(
        `${BASE_URL}/api/analytics/overview`,
        { headers }
    );
    check(analyticsRes, {
        'analytics returns 200': (r) => r.status === 200 || r.status === 401,
    });

    // Test 4: Settings
    const settingsRes = http.get(
        `${BASE_URL}/api/settings/config`,
        { headers }
    );
    check(settingsRes, {
        'settings returns 200': (r) => r.status === 200 || r.status === 401,
    });

    sleep(1);
}

// Test setup
export function setup() {
    console.log(`Testing against: ${BASE_URL}`);

    // Try to login and get a token
    const loginRes = http.post(
        `${BASE_URL}/api/auth/login`,
        JSON.stringify({
            username: 'testuser',
            password: 'testpass',
        }),
        { headers }
    );

    if (loginRes.status === 200) {
        const token = loginRes.json('access_token');
        console.log('Got auth token');
        return { token };
    }

    console.log('No auth token available');
    return { token: null };
}
