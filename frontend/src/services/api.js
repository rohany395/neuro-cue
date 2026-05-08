import { Client, handle_file } from "@gradio/client";

const SPACE_URL =
  import.meta.env.VITE_SPACE_URL || "https://rohany395-neuro-cue.hf.space/";

const HF_TOKEN = import.meta.env.VITE_HF_TOKEN;

let _clientPromise = null;

function getClient() {
  if (!_clientPromise) {
    const opts = HF_TOKEN ? { token: HF_TOKEN } : {};
    _clientPromise = Client.connect(SPACE_URL, opts);
  }
  return _clientPromise;
}

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
  const client = await getClient();

  let payload;
  if (modality === "video" && videoFile) {
    payload = {
      text: "",
      n_timesteps: nTimesteps,
      video: handle_file(videoFile),
    };
  } else {
    payload = {
      text,
      n_timesteps: nTimesteps,
      video: null,
    };
  }

  const result = await client.predict("/predict_json", payload);

  const data = result.data?.[0];
  if (!data) {
    throw new Error("No data returned from inference");
  }
  if (data.success === false) {
    throw new Error(data.error || "Prediction failed");
  }
  return data;
}