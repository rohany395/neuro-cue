import { Client } from "@gradio/client";

// Public Gradio Space URL
const SPACE_URL =
  import.meta.env.VITE_SPACE_URL || "https://rohany395-neuro-cue.hf.space/";

// Optional HF token for personal quota (set in .env.local)
const HF_TOKEN = import.meta.env.VITE_HF_TOKEN;

let _clientPromise = null;

/**
 * Lazy-init the Gradio client. Reuses the same connection.
 */
function getClient() {
  if (!_clientPromise) {
    const opts = HF_TOKEN ? { token: HF_TOKEN } : {};
    _clientPromise = Client.connect(SPACE_URL, opts);
  }
  return _clientPromise;
}

/**
 * Health check - pings the Space root.
 */
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
 * Submit a stimulus and get brain prediction back.
 */
export async function predictStimulus({
  modality = "Text",
  text = "",
  audioFile = null,
  videoFile = null,
  nTimesteps = 10,
  vmin = 0.5,
}) {
  const client = await getClient();

  const result = await client.predict("/predict", {
    input_type: modality,
    video_file: videoFile,
    audio_file: audioFile,
    text_input: text,
    n_timesteps: nTimesteps,
    vmin_val: vmin,
  });

  const [brainHtml, clinicalHtml, statusMd] = result.data;
  return { brainHtml, clinicalHtml, status: statusMd };
}