const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

export const config = {
  maxDuration: 300,
};

function setCorsHeaders(req, res) {
  const origin = req.headers.origin;

  if (origin) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }

  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Max-Age", "86400");
}

export default async function handler(req, res) {
  res.setHeader("X-Neuro-Cue-Proxy", "disabled");
  setCorsHeaders(req, res);

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }

  if (req.method === "GET") {
    return res.status(200).json({
      success: true,
      proxy: "disabled",
      spaceUrl: SPACE_URL,
      message:
        "Prediction proxy is disabled. The web app calls the public Hugging Face Space directly.",
    });
  }

  if (req.method === "POST") {
    return res.status(410).json({
      success: false,
      error:
        "Prediction proxy is disabled. Call the public Hugging Face Space /predict_json API directly.",
    });
  }

  res.setHeader("Allow", "GET, OPTIONS");
  return res.status(405).json({ success: false, error: "Method not allowed." });
}
