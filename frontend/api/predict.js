const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;
const HF_TOKEN = process.env.HF_TOKEN || process.env.HUGGING_FACE_HUB_TOKEN;

const TOKEN_CHECK_TIMEOUT_MS = 5000;

export const config = {
  maxDuration: 300,
};

function setProxyHeaders(res) {
  res.setHeader("X-Neuro-Cue-Proxy", "1");
}

function applyCors(req, res) {
  const origin = req.headers.origin;
  if (origin) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }

  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Access-Control-Max-Age", "86400");
}

function handleOptions(req, res) {
  applyCors(req, res);
  return res.status(204).end();
}

async function checkHfToken() {
  if (!HF_TOKEN) {
    return { configured: false, valid: false };
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TOKEN_CHECK_TIMEOUT_MS);

  try {
    const response = await fetch("https://huggingface.co/api/whoami-v2", {
      headers: { Authorization: `Bearer ${HF_TOKEN}` },
      signal: controller.signal,
    });

    return {
      configured: true,
      valid: response.ok,
      status: response.status,
    };
  } catch (error) {
    return {
      configured: true,
      valid: false,
      error: error.name === "AbortError" ? "timeout" : "request_failed",
    };
  } finally {
    clearTimeout(timeout);
  }
}

export default async function handler(req, res) {
  setProxyHeaders(res);
  applyCors(req, res);

  if (req.method === "OPTIONS") {
    return handleOptions(req, res);
  }

  if (req.method === "GET") {
    const tokenStatus = await checkHfToken();
    return res.status(200).json({
      success: true,
      proxy: "neuro-cue-vercel",
      spaceUrl: SPACE_URL,
      hfToken: tokenStatus,
      videoUpload: "browser-direct-to-space",
      postPredictions: "disabled",
    });
  }

  res.setHeader("Allow", "GET, OPTIONS");
  if (req.method !== "POST") {
    return res.status(405).json({ success: false, error: "Method not allowed." });
  }

  return res.status(410).json({
    success: false,
    error:
      "Server-side prediction proxy is disabled. Use the public Hugging Face Space API directly.",
  });
}
