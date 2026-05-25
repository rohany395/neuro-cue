import { uploadVideoToSpace } from "./hfUpload.js";

const PREDICT_PROXY_URL = import.meta.env.VITE_PREDICT_PROXY_URL || "/api/predict";
const PREDICT_API_KEY = import.meta.env.VITE_PREDICT_API_KEY || "";

function predictHeaders(contentType = null) {
  const headers = {};
  if (contentType) {
    headers["Content-Type"] = contentType;
  }
  if (PREDICT_API_KEY) {
    headers["x-neuro-cue-api-key"] = PREDICT_API_KEY;
  }
  return headers;
}

async function parsePredictResponse(res) {
  const data = await res.json().catch(() => null);
  if (!res.ok || !data) {
    if (res.status === 401 && !PREDICT_API_KEY) {
      throw new Error(
        "Missing VITE_PREDICT_API_KEY. Copy .env.local.example and set the same value as PREDICT_API_SECRET.",
      );
    }
    if (res.status === 413) {
      throw new Error(
        "Request too large for the API proxy. Video uploads should go directly to Hugging Face — refresh and try again.",
      );
    }
    throw new Error(data?.error || "Prediction failed");
  }
  if (data.success === false) {
    throw new Error(data.error || "Prediction failed");
  }
  return data;
}

export async function checkHealth() {
  try {
    const res = await fetch(PREDICT_PROXY_URL);
    const data = await res.json().catch(() => null);
    if (res.ok && data?.success) {
      return {
        status: data.hfToken?.valid ? "connected" : "error",
        mock_mode: false,
      };
    }
    return { status: "error" };
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
    const res = await fetch(PREDICT_PROXY_URL, {
      method: "POST",
      headers: predictHeaders("application/json"),
      body: JSON.stringify({
        modality: "video",
        n_timesteps: nTimesteps,
        video_ref: videoRef,
      }),
    });

    return parsePredictResponse(res);
  }

  onPhase?.("predicting");
  const res = await fetch(PREDICT_PROXY_URL, {
    method: "POST",
    headers: predictHeaders("application/json"),
    body: JSON.stringify({
      modality: "text",
      text,
      n_timesteps: nTimesteps,
    }),
  });

  return parsePredictResponse(res);
}
