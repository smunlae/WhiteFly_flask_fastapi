import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,
  duration: "30s",
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080/fastapi";

function randomName(prefix) {
  return `${prefix}_${Math.floor(Math.random() * 100000)}`;
}

export default function () {
  const homeRes = http.get(`${BASE_URL}/`);
  check(homeRes, {
    "fastapi home status is 200": (r) => r.status === 200,
  });

  const syncPage = http.get(`${BASE_URL}/form-sync`);
  const csrfMatchSync = syncPage.body.match(/name="csrf_token" value="([^"]+)"/);
  const csrfSync = csrfMatchSync ? csrfMatchSync[1] : "";

  sleep(2);

  const syncPayload = {
    first_name: randomName("Sync"),
    last_name: randomName("User"),
    website: "",
    fingerprint: "k6-fastapi-sync",
    csrf_token: csrfSync,
  };

  const syncRes = http.post(`${BASE_URL}/form-sync`, syncPayload, {
    redirects: 0,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  check(syncRes, {
    "fastapi sync returns redirect": (r) => r.status === 302 || r.status === 303,
  });

  const asyncPage = http.get(`${BASE_URL}/form-async`);
  const csrfMatchAsync = asyncPage.body.match(/name="csrf_token" value="([^"]+)"/);
  const csrfAsync = csrfMatchAsync ? csrfMatchAsync[1] : "";

  sleep(2);

  const asyncPayload = {
    first_name: randomName("Async"),
    last_name: randomName("User"),
    website: "",
    fingerprint: "k6-fastapi-async",
    csrf_token: csrfAsync,
  };

  const asyncRes = http.post(`${BASE_URL}/form-async`, asyncPayload, {
    redirects: 0,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  check(asyncRes, {
    "fastapi async returns redirect": (r) => r.status === 302 || r.status === 303,
  });

  sleep(1);
}
