import assert from "node:assert/strict";
import test from "node:test";

process.env.HF_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";

const { validateVideoRef } = await import("./predict.js");

test("validateVideoRef accepts matching Gradio upload path and file URL", () => {
  const videoRef = validateVideoRef({
    path: "/tmp/gradio/upload-abc/blob",
    url: "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/upload-abc/blob",
    orig_name: "stimulus.mp4",
  });

  assert.deepEqual(videoRef, {
    path: "/tmp/gradio/upload-abc/blob",
    url: "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/upload-abc/blob",
    orig_name: "stimulus.mp4",
  });
});

test("validateVideoRef derives a safe path from a Gradio file URL", () => {
  const videoRef = validateVideoRef({
    url: "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/upload-abc/blob",
  });

  assert.equal(videoRef.path, "/tmp/gradio/upload-abc/blob");
});

test("validateVideoRef rejects non-upload local paths", () => {
  assert.throws(
    () => validateVideoRef({ path: "/etc/passwd" }),
    /must reference a Hugging Face upload/,
  );
});

test("validateVideoRef rejects traversal within upload paths", () => {
  assert.throws(
    () => validateVideoRef({ path: "/tmp/gradio/upload-abc/../secret" }),
    /must reference a Hugging Face upload/,
  );
});

test("validateVideoRef rejects file URLs from other hosts", () => {
  assert.throws(
    () =>
      validateVideoRef({
        url: "https://attacker.hf.space/file=/tmp/gradio/upload-abc/blob",
      }),
    /configured Hugging Face Space/,
  );
});

test("validateVideoRef rejects mismatched path and URL references", () => {
  assert.throws(
    () =>
      validateVideoRef({
        path: "/tmp/gradio/upload-abc/blob",
        url: "https://rohany395-neuro-cue.hf.space/file=/tmp/gradio/upload-def/blob",
      }),
    /do not reference the same upload/,
  );
});
