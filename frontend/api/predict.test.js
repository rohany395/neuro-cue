import test from "node:test";
import assert from "node:assert/strict";

import handler from "./predict.js";


function createReq(method, headers = {}) {
  return {
    method,
    headers,
  };
}


function createRes() {
  return {
    headers: {},
    statusCode: 200,
    body: undefined,
    setHeader(name, value) {
      this.headers[name] = value;
      return this;
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


test("GET /api/predict reports disabled proxy mode", async () => {
  const res = createRes();

  await handler(createReq("GET"), res);

  assert.equal(res.statusCode, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.proxy, "disabled");
  assert.equal(res.body.predictionMode, "browser-direct-to-space");
});


test("POST /api/predict is disabled even if a key is supplied", async () => {
  const res = createRes();

  await handler(
    createReq("POST", { "x-neuro-cue-api-key": "previously-public-key" }),
    res,
  );

  assert.equal(res.statusCode, 410);
  assert.equal(res.body.success, false);
  assert.match(res.body.error, /proxy is disabled/i);
});
