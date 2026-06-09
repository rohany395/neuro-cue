const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

function setProxyHeaders(res) {
  res.setHeader("X-Neuro-Cue-Proxy", "1");
}

export default async function handler(req, res) {
  setProxyHeaders(res);

  if (req.method === "OPTIONS") {
    res.setHeader("Allow", "GET, OPTIONS");
    return res.status(204).end();
  }

  if (req.method === "GET") {
    return res.status(200).json({
      success: true,
      proxy: "neuro-cue-vercel",
      spaceUrl: SPACE_URL,
      predictions: "browser-direct-to-space",
      videoUpload: "browser-direct-to-space",
    });
  }

  if (req.method === "POST") {
    return res.status(410).json({
      success: false,
      error:
        "The prediction proxy is disabled. Call the public Hugging Face Space /predict_json API directly.",
    });
  }

  res.setHeader("Allow", "GET, OPTIONS");
  return res.status(405).json({ success: false, error: "Method not allowed." });
}
