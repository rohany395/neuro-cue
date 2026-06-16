import test from "node:test";
import assert from "node:assert/strict";

import handler from "../api/predict.js";

function mockResponse() {
  return {
    statusCode: null,
    body: null,
    ended: false,
    headers: {},
    setHeader(name, value) {
      this.headers[name.toLowerCase()] = value;
    },
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(body) {
      this.body = body;
      return this;
    },
    end() {
      this.ended = true;
      return this;
    },
  };
}

test("POST /api/predict does not proxy token-backed predictions", async () => {
  const req = {
    method: "POST",
    headers: {
      origin: "https://neuro-cue.vercel.app",
      "x-neuro-cue-api-key": "previously-bundled-key",
    },
  };
  const res = mockResponse();

  await handler(req, res);

  assert.equal(res.statusCode, 410);
  assert.equal(res.body.success, false);
  assert.match(res.body.error, /proxy is disabled/i);
  assert.equal(res.headers.allow, "GET, OPTIONS");
});

test("GET /api/predict reports direct Space prediction mode", async () => {
  const req = {
    method: "GET",
    headers: {
      origin: "https://neuro-cue.vercel.app",
    },
  };
  const res = mockResponse();

  await handler(req, res);

  assert.equal(res.statusCode, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.proxy, "disabled");
  assert.equal(res.body.predictionApi, "hugging-face-space");
  assert.equal(res.body.hfToken, undefined);
});
