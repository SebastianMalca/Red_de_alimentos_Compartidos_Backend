import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 50,
  duration: '30s',
};

export default function () {
  const res = http.get('http://localhost:8000/donaciones');
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'transaction time < 500ms': (r) => r.timings.duration < 500,
  });

  // A small pause between requests to simulate real-world clients
  sleep(0.1);
}
