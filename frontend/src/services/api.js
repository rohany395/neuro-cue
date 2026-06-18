import { Client } from "@gradio/client";
import { uploadVideoToSpace } from "./hfUpload.js";

const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL = import.meta.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;
const MAX_TIMESTEPS = 30;

let clientPromise = null;

async function getSpaceClient() {
  if (!clientPromise) {
    clientPromise = Client.connect(SPACE_URL);
  }
  return clientPromise;
}

function normalizeTimesteps(value) {
  const nTimesteps = Number.parseInt(value, 10);
  if (!Number.isInteger(nTimesteps) || nTimesteps < 1) {
    throw new Error("n_timesteps must be a positive integer.");
  }
  return Math.min(nTimesteps, MAX_TIMESTEPS);
}

async function predictJson(payload) {
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
    const client = await getSpaceClient();
    return {
      status: client.config?.root ? "connected" : "error",
      mock_mode: false,
    };
  } catch {
    return { status: "error" };
  }
}

/**
 * Submit a stimulus (text OR video) and get structured prediction back.
 *
 * Video: uploads to HF Space first, then asks the Space API to predict on that upload.
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
  const normalizedTimesteps = normalizeTimesteps(nTimesteps);

  if (modality === "video" && videoFile) {
    onPhase?.("uploading");
    const videoRef = await uploadVideoToSpace(videoFile);

    onPhase?.("predicting");
    return predictJson({
      text: "",
      n_timesteps: normalizedTimesteps,
      video: videoRef,
    });
  }

  onPhase?.("predicting");
  return predictJson({
    text,
    n_timesteps: normalizedTimesteps,
    video: null,
  });
}
