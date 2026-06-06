import assert from "node:assert/strict";
import test from "node:test";

import {
  normalizePredictJson,
  parseTimesteps,
  validateVideoRef,
} from "./predict.js";

test("normalizes Vercel-parsed JSON request bodies", () => {
  assert.deepEqual(
    normalizePredictJson({
      modality: "video",
      n_timesteps: 15,
      video_ref: {
        path: "/tmp/gradio/session/blob",
        url: "https://rohany395-neuro-cue.hf.space/gradio_api/file=/tmp/gradio/session/blob",
        orig_name: "clip.mp4",
      },
    }),
    {
      modality: "video",
      text: "",
      nTimesteps: 15,
      videoRef: {
        path: "/tmp/gradio/session/blob",
        url: "https://rohany395-neuro-cue.hf.space/gradio_api/file=/tmp/gradio/session/blob",
        orig_name: "clip.mp4",
      },
    },
  );
});

test("clamps timestep requests at the proxy boundary", () => {
  assert.equal(parseTimesteps(100), 30);
  assert.equal(parseTimesteps("5"), 5);
  assert.throws(() => parseTimesteps(0), /positive integer/);
  assert.throws(() => parseTimesteps(-1), /positive integer/);
});

test("accepts only local Gradio upload paths for video_ref", () => {
  assert.deepEqual(
    validateVideoRef({
      path: "/tmp/gradio/session/blob",
      url: "https://rohany395-neuro-cue.hf.space/gradio_api/file=/tmp/gradio/session/blob",
      orig_name: "clip.webm",
    }),
    {
      path: "/tmp/gradio/session/blob",
      url: "https://rohany395-neuro-cue.hf.space/gradio_api/file=/tmp/gradio/session/blob",
      orig_name: "clip.webm",
    },
  );

  assert.throws(
    () => validateVideoRef({ path: "/etc/passwd", orig_name: "clip.mp4" }),
    /local Gradio upload path/,
  );
  assert.throws(
    () => validateVideoRef({ path: "/tmp/gradio/session/../other/blob" }),
    /local Gradio upload path/,
  );
  assert.throws(
    () => validateVideoRef({
      path: "/tmp/gradio/session/blob",
      url: "https://attacker.hf.space/gradio_api/file=/tmp/gradio/session/blob",
    }),
    /configured Hugging Face Space/,
  );
  assert.throws(
    () => validateVideoRef({ url: "https://rohany395-neuro-cue.hf.space/file=blob" }),
    /local Gradio upload path/,
  );
});
