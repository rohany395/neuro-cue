const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

const TOKEN_CHECK_TIMEOUT_MS = 5000;

export const config = {
  maxDuration: 10,
};

function setProxyHeaders(res) {
  res.setHeader("X-Neuro-Cue-Proxy", "disabled");
}

async function checkSpaceHealth() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TOKEN_CHECK_TIMEOUT_MS);

  try {
    const response = await fetch(SPACE_URL, { signal: controller.signal });
    return { configured: true, reachable: response.ok, status: response.status };
  } catch (error) {
    return {
      configured: true,
      reachable: false,
      error: error.name === "AbortError" ? "timeout" : "request_failed",
    };
  } finally {
    clearTimeout(timeout);
  }
}

export default async function handler(req, res) {
  setProxyHeaders(res);

  if (req.method === "OPTIONS") {
    res.setHeader("Allow", "GET, OPTIONS");
    return res.status(204).end();
  }

  if (req.method === "GET") {
    const spaceStatus = await checkSpaceHealth();
    return res.status(200).json({
      success: true,
      proxy: "disabled",
      spaceUrl: SPACE_URL,
      space: spaceStatus,
      predictionPath: "browser-direct-to-space",
    });
  }

  res.setHeader("Allow", "GET, OPTIONS");
  return res.status(410).json({
    success: false,
    error:
      "The prediction proxy is disabled. Call the public Hugging Face Space directly.",
  });
}
