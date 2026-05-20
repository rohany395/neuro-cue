import { Client, handle_file } from "@gradio/client";
import { formidable } from "formidable";
import fs from "node:fs/promises";
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
const MAX_VIDEO_BYTES = 50 * 1024 * 1024;
const MAX_TIMESTEPS = 100;
const TOKEN_CHECK_TIMEOUT_MS = 5000;

let clientPromise = null;

export const config = {
  maxDuration: 300,
};

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

function parseMultipart(req) {
  const form = formidable({
    keepExtensions: true,
    maxFileSize: MAX_VIDEO_BYTES,
    maxFieldsSize: MAX_TEXT_CHARS * 4,
    multiples: false,
    uploadDir: "/tmp",
  });

  return new Promise((resolve, reject) => {
    form.parse(req, (error, fields, files) => {
      if (error) {
        reject(error);
        return;
      }

      resolve({
        modality: singleValue(fields.modality) || "text",
        text: singleValue(fields.text) || "",
        nTimesteps: singleValue(fields.n_timesteps) || "10",
        videoFile: singleFile(files.video),
      });
    });
  });
}

function readJson(req) {
  return new Promise((resolve, reject) => {
    let body = "";

    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > MAX_TEXT_CHARS * 4) {
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
          videoFile: null,
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

  throw new Error("Request must be multipart/form-data or application/json.");
}

function parseTimesteps(value) {
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

async function cleanupUpload(videoFile) {
  if (videoFile?.filepath) {
    await fs.unlink(videoFile.filepath).catch(() => {});
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
      predictAuthConfigured: Boolean(getPredictApiSecret()),
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

  let videoFile = null;

  try {
    const parsed = await parseRequest(req);
    const modality = parsed.modality === "video" ? "video" : "text";
    const nTimesteps = parseTimesteps(parsed.nTimesteps);
    videoFile = parsed.videoFile;

    let payload;
    if (modality === "video") {
      if (!videoFile?.filepath) {
        return res.status(400).json({
          success: false,
          error: "Video file is required.",
        });
      }

      payload = {
        text: "",
        n_timesteps: nTimesteps,
        video: handle_file(videoFile.filepath),
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
    return res.status(500).json({
      success: false,
      error: error.message || "Prediction failed.",
    });
  } finally {
    await cleanupUpload(videoFile);
  }
}
