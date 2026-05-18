const SPACE_URL =
  import.meta.env.VITE_SPACE_URL || "https://rohany395-neuro-cue.hf.space/";
const PREDICT_PROXY_URL = import.meta.env.VITE_PREDICT_PROXY_URL || "/api/predict";

export async function checkHealth() {
  try {
    const res = await fetch(SPACE_URL);
    if (res.ok) return { status: "connected", mock_mode: false };
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
    body: formData,
  });

  const data = await res.json().catch(() => null);
  if (!res.ok || !data) {
    throw new Error(data?.error || "Prediction failed");
  }
  if (data.success === false) {
    throw new Error(data.error || "Prediction failed");
  }
  return data;
}