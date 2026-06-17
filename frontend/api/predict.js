const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

const SPACE_CHECK_TIMEOUT_MS = 5000;

function setProxyHeaders(res) {
  res.setHeader("X-Neuro-Cue-Proxy", "1");
}

async function checkSpace() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), SPACE_CHECK_TIMEOUT_MS);

  try {
    const response = await fetch(SPACE_URL, {
      method: "HEAD",
      signal: controller.signal,
    });

    return {
      reachable: response.ok,
      status: response.status,
    };
  } catch (error) {
    return {
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
    const spaceStatus = await checkSpace();
    return res.status(200).json({
      success: true,
      proxy: "neuro-cue-vercel",
      spaceUrl: SPACE_URL,
      space: spaceStatus,
      predictionProxy: "disabled",
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
