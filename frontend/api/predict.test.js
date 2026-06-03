import assert from "node:assert/strict";
import test from "node:test";

import { validateVideoRef } from "./predict.js";

const SPACE_URL = "https://rohany395-neuro-cue.hf.space";

test("validateVideoRef accepts a configured Space upload reference", () => {
  const ref = validateVideoRef({
    path: "/tmp/gradio/session/blob",
    url: `${SPACE_URL}/file=/tmp/gradio/session/blob`,
    orig_name: "sample.mp4",
  });

  assert.deepEqual(ref, {
    path: "/tmp/gradio/session/blob",
    url: `${SPACE_URL}/file=/tmp/gradio/session/blob`,
    orig_name: "sample.mp4",
  });
});

test("validateVideoRef rejects paths outside the Gradio upload root", () => {
  assert.throws(
    () => validateVideoRef({ path: "/tmp/gradio/../../etc/passwd" }),
    /must point to a Hugging Face upload/,
  );
});

test("validateVideoRef rejects foreign Hugging Face Space URLs", () => {
  assert.throws(
    () =>
      validateVideoRef({
        url: "https://attacker-space.hf.space/file=/tmp/gradio/session/blob",
      }),
    /configured Hugging Face Space/,
  );
});

test("validateVideoRef rejects mismatched path and URL references", () => {
  assert.throws(
    () =>
      validateVideoRef({
        path: "/tmp/gradio/session/blob",
        url: `${SPACE_URL}/file=/tmp/gradio/other/blob`,
      }),
    /do not reference the same upload/,
  );
});
