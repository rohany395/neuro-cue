const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

function setProxyHeaders(res) {
  res.setHeader("X-Neuro-Cue-Proxy", "disabled");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Max-Age", "86400");
}

function getRequestOrigin(req) {
  const origin = req.headers.origin;
  if (origin) {
    return origin;
  }

  const referer = req.headers.referer;
  if (!referer) {
    return null;
  }

  try {
    return new URL(referer).origin;
  } catch {
    return null;
  }
}

function applyCors(req, res) {
  const origin = getRequestOrigin(req);
  if (origin) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }
}

export default async function handler(req, res) {
  setProxyHeaders(res);
  applyCors(req, res);

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }

  if (req.method === "GET") {
    return res.status(200).json({
      success: true,
      proxy: "disabled",
      spaceUrl: SPACE_URL,
      videoUpload: "browser-direct-to-space",
      predictions: "browser-direct-to-space",
    });
  }

  res.setHeader("Allow", "GET, OPTIONS");
  return res.status(410).json({
    success: false,
    error:
      "Server-side prediction proxy is disabled. Call the Hugging Face Space directly.",
  });
}
