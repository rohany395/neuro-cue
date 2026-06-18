const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

export const config = {
  maxDuration: 10,
};

function setHeaders(res) {
  res.setHeader("X-Neuro-Cue-Proxy", "disabled");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Max-Age", "86400");
}

export default async function handler(req, res) {
  setHeaders(res);

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }

  if (req.method === "GET") {
    return res.status(200).json({
      success: true,
      proxy: "disabled",
      predictionTransport: "browser-direct-to-space",
      spaceUrl: SPACE_URL,
    });
  }

  if (req.method === "POST") {
    return res.status(410).json({
      success: false,
      error:
        "Prediction proxy is disabled. Use the public Hugging Face Space API directly.",
    });
  }

  res.setHeader("Allow", "GET, OPTIONS");
  return res.status(405).json({ success: false, error: "Method not allowed." });
}
