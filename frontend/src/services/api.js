const PREDICT_PROXY_URL = import.meta.env.VITE_PREDICT_PROXY_URL || "/api/predict";
const PREDICT_API_KEY = import.meta.env.VITE_PREDICT_API_KEY || "";

function predictHeaders() {
  const headers = {};
  if (PREDICT_API_KEY) {
    headers["x-neuro-cue-api-key"] = PREDICT_API_KEY;
  }
  return headers;
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
 * @param {Object} input
 * @param {"text"|"video"} input.modality
 * @param {string} [input.text]
 * @param {File} [input.videoFile]
 * @param {number} [input.nTimesteps=10]
 */
export async function predictStimulus({
  modality = "text",
  text = "",
  videoFile = null,
  nTimesteps = 10,
}) {
  const formData = new FormData();
  formData.append("modality", modality);
  formData.append("n_timesteps", String(nTimesteps));

  if (modality === "video" && videoFile) {
    formData.append("video", videoFile);
  } else {
    formData.append("text", text);
  }

  const res = await fetch(PREDICT_PROXY_URL, {
    method: "POST",
    headers: predictHeaders(),
    body: formData,
  });

  const data = await res.json().catch(() => null);
  if (!res.ok || !data) {
    if (res.status === 401 && !PREDICT_API_KEY) {
      throw new Error(
        "Missing VITE_PREDICT_API_KEY. Copy .env.local.example and set the same value as PREDICT_API_SECRET.",
      );
    }
    throw new Error(data?.error || "Prediction failed");
  }
  if (data.success === false) {
    throw new Error(data.error || "Prediction failed");
  }
  return data;
}