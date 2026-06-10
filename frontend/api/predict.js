import { Client } from "@gradio/client";
import { formidable } from "formidable";
import fs from "node:fs/promises";
import path from "node:path";
import {
  applyCors,
  authorizePredictRequest,
  getPredictApiSecret,
  handleOptions,
} from "./lib/proxyAuth.js";

const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL =
  process.env.HF_SPACE_URL || process.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;
const HF_TOKEN = process.env.HF_TOKEN || process.env.HUGGING_FACE_HUB_TOKEN;

const MAX_TEXT_CHARS = 5000;
const MAX_JSON_BYTES = 64 * 1024;
/** Vercel request body limit; reject multipart video uploads with a clear message. */
const VERCEL_MAX_BODY_BYTES = 4.5 * 1024 * 1024;
const MAX_TIMESTEPS = 30;
const TOKEN_CHECK_TIMEOUT_MS = 5000;
const GRADIO_FILE_PREFIX = "/file=";
const GRADIO_UPLOAD_ROOT = "/tmp/gradio";

let clientPromise = null;

export const config = {
  maxDuration: 300,
};

function getSpaceOrigin() {
  const parsed = new URL(SPACE_URL);
  return parsed.origin.toLowerCase();
}

function getClient() {
  if (!HF_TOKEN) {
    throw new Error("HF_TOKEN is not configured for the prediction proxy.");
  }

  if (!clientPromise) {
    clientPromise = Client.connect(SPACE_URL, { token: HF_TOKEN });
  }
  return clientPromise;
}

function setProxyHeaders(res) {
  res.setHeader("X-Neuro-Cue-Proxy", "1");
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

function singleValue(value) {
  return Array.isArray(value) ? value[0] : value;
}

function singleFile(value) {
  return Array.isArray(value) ? value[0] : value;
}

function normalizeUploadedPath(filePath) {
  if (typeof filePath !== "string" || !filePath || filePath.includes("\0")) {
    throw new Error("video_ref file path is invalid.");
  }

  const normalized = path.posix.normalize(filePath);
  if (!normalized.startsWith(`${GRADIO_UPLOAD_ROOT}/`)) {
    throw new Error("video_ref must point to an uploaded Gradio file.");
  }
  return normalized;
}

function extractUploadedPathFromUrl(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    throw new Error("video_ref url is invalid.");
  }

  if (parsed.origin.toLowerCase() !== getSpaceOrigin()) {
    throw new Error("video_ref url must point to the configured Hugging Face Space.");
  }

  if (!parsed.pathname.startsWith(GRADIO_FILE_PREFIX) || parsed.search || parsed.hash) {
    throw new Error("video_ref url must be a Gradio uploaded file URL.");
  }

  const uploadedPath = decodeURIComponent(parsed.pathname.slice(GRADIO_FILE_PREFIX.length));
  return {
    path: normalizeUploadedPath(uploadedPath),
    url: parsed.toString(),
  };
}

export function validateVideoRef(ref) {
  if (!ref || typeof ref !== "object") {
    throw new Error("video_ref is required for video predictions.");
  }

  const path = typeof ref.path === "string" ? ref.path : "";
  const url = typeof ref.url === "string" ? ref.url : "";

  if (!url) {
    throw new Error("video_ref must include a Gradio uploaded file URL.");
  }

  const uploaded = extractUploadedPathFromUrl(url);
  if (path && normalizeUploadedPath(path) !== uploaded.path) {
    throw new Error("video_ref path does not match the uploaded file URL.");
  }

  const origName =
    typeof ref.orig_name === "string"
      ? ref.orig_name
      : typeof ref.meta?.name === "string"
        ? ref.meta.name
        : undefined;

  return {
    path: uploaded.path,
    url: uploaded.url,
    orig_name: origName,
  };
}

async function cleanupUpload(videoFile) {
  if (videoFile?.filepath) {
    await fs.unlink(videoFile.filepath).catch(() => {});
  }
}

function parseMultipart(req) {
  const form = formidable({
    keepExtensions: true,
    maxFileSize: VERCEL_MAX_BODY_BYTES,
    maxFieldsSize: MAX_TEXT_CHARS * 4,
    multiples: false,
    uploadDir: "/tmp",
  });

  return new Promise((resolve, reject) => {
    form.parse(req, async (error, fields, files) => {
      if (error) {
        reject(error);
        return;
      }

      const videoFile = singleFile(files.video);
      if (videoFile?.filepath) {
        await cleanupUpload(videoFile);
        reject(
          new Error(
            "Do not upload video files through this API (Vercel 4.5MB limit). " +
              "Upload to the Hugging Face Space from the browser, then send video_ref as JSON.",
          ),
        );
        return;
      }

      resolve({
        modality: singleValue(fields.modality) || "text",
        text: singleValue(fields.text) || "",
        nTimesteps: singleValue(fields.n_timesteps) || "10",
        videoRef: null,
      });
    });
  });
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let body = "";

    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > MAX_JSON_BYTES) {
        reject(new Error("Request body is too large."));
        req.destroy();
      }
    });

    req.on("end", () => {
      try {
        const json = body ? JSON.parse(body) : {};
        resolve({
          modality: json.modality || "text",
          text: json.text || "",
          nTimesteps: json.n_timesteps ?? json.nTimesteps ?? 10,
          videoRef: json.video_ref ?? json.videoRef ?? null,
        });
      } catch {
        reject(new Error("Request body must be valid JSON."));
      }
    });

    req.on("error", reject);
  });
}

async function parseRequest(req) {
  const contentType = req.headers["content-type"] || "";

  if (contentType.includes("multipart/form-data")) {
    return parseMultipart(req);
  }

  if (contentType.includes("application/json")) {
    return readJson(req);
  }

  throw new Error("Request must be application/json or multipart/form-data (text only).");
}

export function parseTimesteps(value) {
  const nTimesteps = Number.parseInt(value, 10);

  if (!Number.isInteger(nTimesteps) || nTimesteps < 1) {
    throw new Error("n_timesteps must be a positive integer.");
  }

  return Math.min(nTimesteps, MAX_TIMESTEPS);
}

function validateText(text) {
  const trimmed = text.trim();

  if (!trimmed) {
    throw new Error("Text input is required.");
  }

  if (trimmed.length > MAX_TEXT_CHARS) {
    throw new Error(`Text input must be ${MAX_TEXT_CHARS} characters or fewer.`);
  }

  return trimmed;
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
      predictAuthConfigured: Boolean(getPredictApiSecret()),
      videoUpload: "browser-direct-to-space",
    });
  }

  if (req.method !== "POST") {
    res.setHeader("Allow", "GET, POST, OPTIONS");
    return res.status(405).json({ success: false, error: "Method not allowed." });
  }

  const authFailure = authorizePredictRequest(req);
  if (authFailure) {
    if (authFailure.retryAfterSec) {
      res.setHeader("Retry-After", String(authFailure.retryAfterSec));
    }
    return res.status(authFailure.status).json(authFailure.body);
  }

  try {
    const parsed = await parseRequest(req);
    const modality = parsed.modality === "video" ? "video" : "text";
    const nTimesteps = parseTimesteps(parsed.nTimesteps);

    let payload;
    if (modality === "video") {
      const videoRef = validateVideoRef(parsed.videoRef);
      payload = {
        text: "",
        n_timesteps: nTimesteps,
        video: videoRef,
      };
    } else {
      payload = {
        text: validateText(parsed.text),
        n_timesteps: nTimesteps,
        video: null,
      };
    }

    const client = await getClient();
    const result = await client.predict("/predict_json", payload);
    const data = result.data?.[0];

    if (!data) {
      return res.status(502).json({
        success: false,
        error: "No prediction data returned from Hugging Face.",
      });
    }

    return res.status(200).json(data);
  } catch (error) {
    console.error("[predict proxy] Prediction failed:", error);
    const message = error.message || "Prediction failed.";
    const status = message.includes("4.5MB") ? 413 : 500;
    return res.status(status).json({
      success: false,
      error: message,
    });
  }
}
