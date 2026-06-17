import assert from "node:assert/strict";
import { test } from "node:test";

import handler from "./predict.js";


function createResponse() {
  return {
    body: null,
    headers: {},
    statusCode: 200,
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


test("POST /api/predict is disabled before proxying to Hugging Face", async () => {
  const res = createResponse();

  await handler({ method: "POST", headers: {} }, res);

  assert.equal(res.statusCode, 410);
  assert.equal(res.body.success, false);
  assert.match(res.body.error, /Prediction proxy is disabled/);
});


test("OPTIONS advertises only non-prediction methods", async () => {
  const res = createResponse();

  await handler({ method: "OPTIONS", headers: {} }, res);

  assert.equal(res.statusCode, 204);
  assert.equal(res.headers.allow, "GET, OPTIONS");
});
