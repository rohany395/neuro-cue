import { getSpaceClient, uploadVideoToSpace } from "./hfUpload.js";

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
    return { status: "connected", mock_mode: false };
  } catch {
    return { status: "error" };
  }
}

async function predictOnSpace(payload) {
  const client = await getSpaceClient();
  const result = await client.predict("/predict_json", payload);
  return parsePredictResult(result);
}

/**
 * Submit a stimulus (text OR video) and get structured prediction back.
 *
 * Video: uploads to HF Space first, then calls the Space prediction endpoint.
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
    return predictOnSpace({
      text: "",
      n_timesteps: nTimesteps,
      video: videoRef,
    });
  }

  onPhase?.("predicting");
  return predictOnSpace({
    text,
    n_timesteps: nTimesteps,
    video: null,
  });
}
