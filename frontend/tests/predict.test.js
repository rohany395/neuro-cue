import assert from "node:assert/strict";
import test from "node:test";

import { parseTimesteps, validateVideoRef } from "../api/predict.js";

const SPACE_URL = "https://rohany395-neuro-cue.hf.space";
const UPLOADED_PATH = "/tmp/gradio/12345/blob";
const UPLOADED_URL = `${SPACE_URL}/file=${UPLOADED_PATH}`;

test("validateVideoRef accepts only configured Gradio uploaded file URLs", () => {
  assert.deepEqual(
    validateVideoRef({
      path: UPLOADED_PATH,
      url: UPLOADED_URL,
      orig_name: "session.mp4",
    }),
    {
      path: UPLOADED_PATH,
      url: UPLOADED_URL,
      orig_name: "session.mp4",
    },
  );
});

test("validateVideoRef rejects attacker-controlled Hugging Face Space URLs", () => {
  assert.throws(
    () =>
      validateVideoRef({
        url: `https://attacker-controlled.hf.space/file=${UPLOADED_PATH}`,
        orig_name: "session.mp4",
      }),
    /configured Hugging Face Space/,
  );
});

test("validateVideoRef rejects path-only references", () => {
  assert.throws(
    () =>
      validateVideoRef({
        path: UPLOADED_PATH,
        orig_name: "session.mp4",
      }),
    /Gradio uploaded file URL/,
  );
});

test("validateVideoRef rejects traversal outside the Gradio upload root", () => {
  assert.throws(
    () =>
      validateVideoRef({
        url: `${SPACE_URL}/file=/tmp/gradio/12345/../../etc/passwd`,
        orig_name: "session.mp4",
      }),
    /uploaded Gradio file/,
  );
});

test("validateVideoRef rejects mismatched caller-provided paths", () => {
  assert.throws(
    () =>
      validateVideoRef({
        path: "/tmp/gradio/other/blob",
        url: UPLOADED_URL,
        orig_name: "session.mp4",
      }),
    /does not match/,
  );
});

test("parseTimesteps caps expensive visualization responses", () => {
  assert.equal(parseTimesteps(10), 10);
  assert.equal(parseTimesteps(1000), 30);
});
