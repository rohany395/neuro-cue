import { Client } from "@gradio/client";

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
 * Submit a text stimulus and get structured prediction back.
 *
 * @param {Object} input
 * @param {string} input.text
 * @param {number} [input.nTimesteps=10]
 * @returns {Promise<{
 *   success: boolean,
 *   metadata: {n_timesteps: number, n_vertices: number, tr_seconds: number, stimulus_type: string},
 *   roi_scores: Array<{roi_key, roi_name, function, peak, mean, n_vertices, engagement_level}>,
 *   temporal_scores: Array<{timestep, time_seconds, broca, wernicke, sma, angular}>,
 *   brain_html: string,
 * }>}
 */
export async function predictStimulus({ text = "", nTimesteps = 10 }) {
  const client = await getClient();

  const result = await client.predict("/predict_json", {
    text,
    n_timesteps: nTimesteps,
  });

  // gr.api() wraps the dict in result.data[0]
  const data = result.data?.[0];
  if (!data) {
    throw new Error("No data returned from inference");
  }
  if (data.success === false) {
    throw new Error(data.error || "Prediction failed");
  }
  return data;
}