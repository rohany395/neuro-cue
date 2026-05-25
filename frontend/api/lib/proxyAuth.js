import { createHash, timingSafeEqual } from "node:crypto";

const API_KEY_HEADER = "x-neuro-cue-api-key";

const DEFAULT_ALLOWED_ORIGINS = [
  "https://neuro-cue.vercel.app",
  "http://localhost:5173",
  "http://localhost:3000",
  "http://127.0.0.1:5173",
  "http://127.0.0.1:3000",
];

/** In-memory buckets; best-effort on serverless (per instance). */
const rateBuckets = new Map();

function parseAllowedOrigins() {
  const raw = process.env.ALLOWED_ORIGINS;
  if (!raw?.trim()) {
    return DEFAULT_ALLOWED_ORIGINS;
  }
  return raw
    .split(",")
    .map((o) => o.trim())
    .filter(Boolean);
}

function hashSecret(value) {
  return createHash("sha256").update(value || "").digest();
}

function safeEqualSecret(provided, expected) {
  const a = hashSecret(provided);
  const b = hashSecret(expected);
  return timingSafeEqual(a, b);
}

export function getPredictApiSecret() {
  return process.env.PREDICT_API_SECRET || process.env.NEURO_CUE_API_SECRET || "";
}

export function getRequestOrigin(req) {
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

export function isAllowedOrigin(origin, allowedOrigins) {
  if (!origin) {
    return true;
  }

  if (allowedOrigins.includes(origin)) {
    return true;
  }

  // Vercel preview deployments: https://neuro-cue-<hash>-<team>.vercel.app
  if (
    process.env.ALLOW_VERCEL_PREVIEWS !== "0" &&
    /^https:\/\/[a-z0-9-]+\.vercel\.app$/i.test(origin)
  ) {
    return true;
  }

  return false;
}

function getClientIp(req) {
  const forwarded = req.headers["x-forwarded-for"];
  if (typeof forwarded === "string" && forwarded.length > 0) {
    return forwarded.split(",")[0].trim();
  }
  if (typeof forwarded === "object" && forwarded?.[0]) {
    return String(forwarded[0]).trim();
  }
  return req.headers["x-real-ip"] || req.socket?.remoteAddress || "unknown";
}

function pruneRateBuckets(now) {
  if (rateBuckets.size < 5000) {
    return;
  }
  for (const [key, entry] of rateBuckets) {
    if (entry.minuteReset < now && entry.hourReset < now) {
      rateBuckets.delete(key);
    }
  }
}

export function checkRateLimit(req) {
  const perMinute = Number.parseInt(
    process.env.PREDICT_RATE_LIMIT_PER_MINUTE || "5",
    10,
  );
  const perHour = Number.parseInt(
    process.env.PREDICT_RATE_LIMIT_PER_HOUR || "20",
    10,
  );

  if (!Number.isFinite(perMinute) || !Number.isFinite(perHour)) {
    return { allowed: true };
  }

  const now = Date.now();
  pruneRateBuckets(now);

  const ip = getClientIp(req);
  const key = `ip:${ip}`;
  let entry = rateBuckets.get(key);

  if (!entry) {
    entry = {
      minuteCount: 0,
      minuteReset: now + 60_000,
      hourCount: 0,
      hourReset: now + 3_600_000,
    };
    rateBuckets.set(key, entry);
  }

  if (now >= entry.minuteReset) {
    entry.minuteCount = 0;
    entry.minuteReset = now + 60_000;
  }
  if (now >= entry.hourReset) {
    entry.hourCount = 0;
    entry.hourReset = now + 3_600_000;
  }

  entry.minuteCount += 1;
  entry.hourCount += 1;

  if (entry.minuteCount > perMinute) {
    return {
      allowed: false,
      retryAfterSec: Math.ceil((entry.minuteReset - now) / 1000),
      reason: "minute",
    };
  }
  if (entry.hourCount > perHour) {
    return {
      allowed: false,
      retryAfterSec: Math.ceil((entry.hourReset - now) / 1000),
      reason: "hour",
    };
  }

  return { allowed: true };
}

export function readApiKeyFromRequest(req) {
  const header = req.headers[API_KEY_HEADER];
  if (typeof header === "string" && header.length > 0) {
    return header;
  }

  const auth = req.headers.authorization;
  if (typeof auth === "string" && auth.startsWith("Bearer ")) {
    return auth.slice(7);
  }

  return "";
}

/**
 * Gate POST /api/predict before any HF/ZeroGPU work runs.
 * Returns null if allowed, or { status, body } to send immediately.
 */
export function authorizePredictRequest(req) {
  const secret = getPredictApiSecret();
  if (!secret) {
    return {
      status: 503,
      body: {
        success: false,
        error:
          "Prediction proxy is not configured. Set PREDICT_API_SECRET on the server.",
      },
    };
  }

  const providedKey = readApiKeyFromRequest(req);
  if (!safeEqualSecret(providedKey, secret)) {
    return {
      status: 401,
      body: {
        success: false,
        error: "Unauthorized. Missing or invalid API key.",
      },
    };
  }

  const allowedOrigins = parseAllowedOrigins();
  const origin = getRequestOrigin(req);
  if (!isAllowedOrigin(origin, allowedOrigins)) {
    return {
      status: 403,
      body: {
        success: false,
        error: "Forbidden. Request origin is not allowed.",
      },
    };
  }

  const rate = checkRateLimit(req);
  if (!rate.allowed) {
    return {
      status: 429,
      body: {
        success: false,
        error: `Too many requests. Try again in ${rate.retryAfterSec} seconds.`,
      },
      retryAfterSec: rate.retryAfterSec,
    };
  }

  return null;
}

export function applyCors(req, res) {
  const origin = getRequestOrigin(req);
  const allowedOrigins = parseAllowedOrigins();

  if (origin && isAllowedOrigin(origin, allowedOrigins)) {
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Vary", "Origin");
  }

  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  res.setHeader(
    "Access-Control-Allow-Headers",
    `Content-Type, ${API_KEY_HEADER}`,
  );
  res.setHeader("Access-Control-Max-Age", "86400");
}

export function handleOptions(req, res) {
  applyCors(req, res);
  return res.status(204).end();
}
