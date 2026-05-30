import assert from "node:assert/strict";
import test from "node:test";

const { default: handler } = await import("./predict.js");

function createResponse() {
  return {
    statusCode: null,
    body: null,
    headers: {},
    setHeader(name, value) {
      this.headers[name] = value;
    },
    status(code) {
      this.statusCode = code;
      return this;
    },
    json(payload) {
      this.body = payload;
      return this;
    },
    end() {
      this.ended = true;
      return this;
    },
  };
}

test("POST /api/predict is disabled", async () => {
  const req = { method: "POST", headers: {} };
  const res = createResponse();

  await handler(req, res);

  assert.equal(res.statusCode, 410);
  assert.equal(res.headers["X-Neuro-Cue-Proxy"], "disabled");
  assert.match(res.body.error, /Prediction proxy is disabled/);
});

test("GET /api/predict reports public Space direct mode", async () => {
  const req = { method: "GET", headers: {} };
  const res = createResponse();

  await handler(req, res);

  assert.equal(res.statusCode, 200);
  assert.equal(res.body.success, true);
  assert.equal(res.body.proxy, "disabled");
});
