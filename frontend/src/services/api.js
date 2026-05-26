import { getSpaceClient, SPACE_URL, uploadVideoToSpace } from "./hfUpload.js";

function parsePredictData(data) {
  if (!data) {
    throw new Error("No data returned from inference");
  }
  if (data.success === false) {
    throw new Error(data.error || "Prediction failed");
  }
  return data;
}

export async function checkHealth() {
  try {
    const res = await fetch(SPACE_URL);
    return { status: res.ok ? "connected" : "error", mock_mode: false };
  } catch {
    return { status: "error" };
  }
}

/**
 * Submit a stimulus (text OR video) and get structured prediction back.
 *
 * Video: uploads to HF Space first, then sends the file reference to the Space API.
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
  let payload;

  if (modality === "video" && videoFile) {
    onPhase?.("uploading");
    const videoRef = await uploadVideoToSpace(videoFile);

    onPhase?.("predicting");
    payload = {
      text: "",
      n_timesteps: nTimesteps,
      video: videoRef,
    };
  } else {
    onPhase?.("predicting");
    payload = {
      text,
      n_timesteps: nTimesteps,
      video: null,
    };
  }

  const result = await client.predict("/predict_json", payload);
  const data = result.data?.[0];

  return parsePredictData(data);
}
