import { getSpaceClient, predictOnSpace, uploadVideoToSpace } from "./hfUpload.js";

const MAX_TEXT_CHARS = 5000;
const MAX_TIMESTEPS = 30;

function parseTimesteps(value) {
  const nTimesteps = Number.parseInt(value, 10);
  if (!Number.isInteger(nTimesteps) || nTimesteps < 1) {
    throw new Error("Timesteps must be a positive integer.");
  }
  return Math.min(nTimesteps, MAX_TIMESTEPS);
}

function validateText(text) {
  const trimmed = text.trim();
  if (!trimmed) {
    throw new Error("Text input is required.");
  }
  if (trimmed.length > MAX_TEXT_CHARS) {
    throw new Error(`Text input must be ${MAX_TEXT_CHARS} characters or fewer.`);
  }
  return trimmed;
}

function parsePredictResponse(result) {
  const data = result?.data?.[0];
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
 * Video: uploads to HF Space first, then sends the file reference to predict_json.
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
  const n_timesteps = parseTimesteps(nTimesteps);

  if (modality === "video" && videoFile) {
    onPhase?.("uploading");
    const videoRef = await uploadVideoToSpace(videoFile);

    onPhase?.("predicting");
    const result = await predictOnSpace({
      text: "",
      n_timesteps,
      video: videoRef,
    });

    return parsePredictResponse(result);
  }

  onPhase?.("predicting");
  const result = await predictOnSpace({
    text: validateText(text),
    n_timesteps,
    video: null,
  });

  return parsePredictResponse(result);
}
