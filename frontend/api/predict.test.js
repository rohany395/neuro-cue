import assert from "node:assert/strict";
import test from "node:test";

import { validateVideoRef } from "./predict.js";

test("accepts a Gradio upload path for the configured Space", () => {
  assert.deepEqual(
    validateVideoRef({
      path: "/tmp/gradio/session/blob",
      url: "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/session/blob",
      orig_name: "sample.mp4",
    }),
    {
      path: "/tmp/gradio/session/blob",
      url: "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/session/blob",
      orig_name: "sample.mp4",
    },
  );
});

test("rejects arbitrary local paths", () => {
  assert.throws(
    () => validateVideoRef({ path: "/etc/passwd", orig_name: "passwd.mp4" }),
    /Gradio upload/,
  );
});

test("rejects URL values smuggled through path", () => {
  assert.throws(
    () => validateVideoRef({ path: "https://attacker.example/huge.mp4" }),
    /local Gradio upload path/,
  );
});

test("rejects other Hugging Face Space hosts", () => {
  assert.throws(
    () =>
      validateVideoRef({
        path: "/tmp/gradio/session/blob",
        url: "https://attacker.hf.space/file=/tmp/gradio/session/blob",
      }),
    /configured Hugging Face Space/,
  );
});

test("rejects mismatched file URLs", () => {
  assert.throws(
    () =>
      validateVideoRef({
        path: "/tmp/gradio/session/blob",
        url: "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/other/blob",
      }),
    /does not match/,
  );
});
