const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

function setHeaders(res) {
  res.setHeader("X-Neuro-Cue-Proxy", "disabled");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
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
      spaceUrl: SPACE_URL,
      inference: "browser-direct-to-space",
      videoUpload: "browser-direct-to-space",
    });
  }

  if (req.method === "POST") {
    return res.status(410).json({
      success: false,
      error:
        "Server-side prediction proxy is disabled. Call the public Hugging Face Space API directly.",
    });
  }

  res.setHeader("Allow", "GET, POST, OPTIONS");
  return res.status(405).json({ success: false, error: "Method not allowed." });
}
