import assert from "node:assert/strict";
import test from "node:test";

import handler from "./predict.js";

function createResponse() {
  return {
    headers: {},
    statusCode: null,
    body: null,
    ended: false,
    setHeader(name, value) {
      this.headers[name] = value;
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

test("GET reports direct Space predictions", async () => {
  const res = createResponse();

  await handler({ method: "GET", headers: {} }, res);

  assert.equal(res.statusCode, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.proxy, "disabled");
  assert.equal(res.body.predictions, "browser-direct-to-space");
});

test("POST prediction proxy is disabled", async () => {
  const res = createResponse();

  await handler({ method: "POST", headers: {} }, res);

  assert.equal(res.statusCode, 410);
  assert.equal(res.body.success, false);
  assert.match(res.body.error, /disabled/);
  assert.equal(res.headers.Allow, "GET, OPTIONS");
});
