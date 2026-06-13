import { getSpaceClient, uploadVideoToSpace } from "./hfUpload.js";

const MAX_TEXT_CHARS = 5000;

function parsePredictResult(result) {
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
    return {
      status: "connected",
      mock_mode: false,
    };
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
  const client = await getSpaceClient();

  if (modality === "video" && videoFile) {
    onPhase?.("uploading");
    const videoRef = await uploadVideoToSpace(videoFile);

    onPhase?.("predicting");
    const result = await client.predict("/predict_json", {
      text: "",
      n_timesteps: nTimesteps,
      video: videoRef,
    });

    return parsePredictResult(result);
  }

  const trimmedText = text.trim();
  if (!trimmedText) {
    throw new Error("Text input is required.");
  }
  if (trimmedText.length > MAX_TEXT_CHARS) {
    throw new Error(`Text input must be ${MAX_TEXT_CHARS} characters or fewer.`);
  }

  onPhase?.("predicting");
  const result = await client.predict("/predict_json", {
    text: trimmedText,
    n_timesteps: nTimesteps,
    video: null,
  });

  return parsePredictResult(result);
}
