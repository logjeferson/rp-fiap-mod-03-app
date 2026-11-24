import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 50,
  duration: '3m',
};

export default function () {
  const url = 'https://apis.mysandbox.com.br/flags/flags';
  const params = {
    headers: {
      'Authorization': 'Bearer tm_key_3b426bacf4147575109094e8ba8b168519c029d884ed496ca9f0ce51c2d0a0e9'
    },
  };
  http.get(url, params);
  sleep(1);
}