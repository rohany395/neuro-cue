import { getSpaceClient, uploadVideoToSpace } from "./hfUpload.js";

const MAX_TEXT_CHARS = 5000;

function normalizeTimesteps(value) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed < 1) {
    return 10;
  }
  return parsed;
}

function validateTextInput(text) {
  const trimmed = text.trim();
  if (!trimmed) {
    throw new Error("Text input is required.");
  }
  if (trimmed.length > MAX_TEXT_CHARS) {
    throw new Error(`Text input must be ${MAX_TEXT_CHARS} characters or fewer.`);
  }
  return trimmed;
}

async function predictViaSpace(payload) {
  const client = await getSpaceClient();
  const result = await client.predict("/predict_json", payload);
  const data = result.data?.[0];
  if (!data) {
    throw new Error("No prediction data returned from Hugging Face.");
  }
  if (data.success === false) {
    throw new Error(data.error || "Prediction failed");
  }
  return data;
}

export async function checkHealth() {
  try {
    await getSpaceClient();
    return { status: "connected", mock_mode: false };
  } catch {
    return { status: "error" };
  }
}

/**
 * Submit a stimulus (text OR video) and get structured prediction back.
 *
 * Video: uploads to HF Space first, then POSTs a small JSON payload to the proxy.
 *
 * @param {Object} input
 * @param {"text"|"video"} input.modality
 * @param {string} [input.text]
 * @param {File} [input.videoFile]
 * @param {number} [input.nTimesteps=10]
 * @param {(phase: "uploading"|"predicting"|null) => void} [input.onPhase]
 */
export async function predictStimulus({
  modality = "text",
  text = "",
  videoFile = null,
  nTimesteps = 10,
  onPhase = null,
}) {
  if (modality === "video" && videoFile) {
    onPhase?.("uploading");
    const videoRef = await uploadVideoToSpace(videoFile);

    onPhase?.("predicting");
    return predictViaSpace({
      text: "",
      n_timesteps: normalizeTimesteps(nTimesteps),
      video: videoRef,
    });
  }

  onPhase?.("predicting");
  return predictViaSpace({
    text: validateTextInput(text),
    n_timesteps: normalizeTimesteps(nTimesteps),
    video: null,
  });
}
