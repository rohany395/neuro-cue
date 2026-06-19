import { Client, prepare_files } from "@gradio/client";

export const MAX_VIDEO_BYTES = 50 * 1024 * 1024;

const DEFAULT_SPACE_URL = "https://rohany395-neuro-cue.hf.space/";
const SPACE_URL = import.meta.env.VITE_SPACE_URL || DEFAULT_SPACE_URL;

let clientPromise = null;

export async function getSpaceClient() {
  if (!clientPromise) {
    clientPromise = Client.connect(SPACE_URL);
  }
  return clientPromise;
}

/**
 * Upload a video directly to the Hugging Face Space (bypasses Vercel's 4.5MB body limit).
 * @returns {Promise<{ path: string, url?: string, orig_name: string }>}
 */
export async function uploadVideoToSpace(file) {
  if (!file) {
    throw new Error("No video file selected.");
  }

  if (file.size > MAX_VIDEO_BYTES) {
    const maxMb = MAX_VIDEO_BYTES / (1024 * 1024);
    throw new Error(`Video must be ${maxMb} MB or smaller.`);
  }

  const client = await getSpaceClient();
  const root = client.config?.root;
  if (!root) {
    throw new Error("Could not connect to Hugging Face Space.");
  }

  const prepared = await prepare_files([file]);
  const uploaded = await client.upload(prepared, root, undefined, MAX_VIDEO_BYTES);
  const fileData = uploaded?.[0];

  if (!fileData?.path && !fileData?.url) {
    throw new Error("Upload to Hugging Face Space did not return a file reference.");
  }

  return {
    path: fileData.path,
    url: fileData.url,
    orig_name: fileData.orig_name || file.name,
  };
}
