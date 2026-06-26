const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

export const config = {
  maxDuration: 10,
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
  setCorsHeaders(req, res);

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }

  if (req.method === "GET") {
    return res.status(200).json({
      success: true,
      proxy: "disabled",
      spaceUrl: SPACE_URL,
      predictionTransport: "browser-direct-to-space",
    });
  }

  res.setHeader("Allow", "GET, OPTIONS");
  return res.status(410).json({
    success: false,
    error:
      "The prediction proxy is disabled. Use the public Hugging Face Space API directly.",
  });
}
