import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60s — TRIBE v2 inference can be slow
});

/**
 * Health check — confirms backend is reachable.
 */
export async function checkHealth() {
  const response = await apiClient.get("/health");
  return response.data;
}

/**
 * Upload a stimulus and get brain prediction back.
 * @param {File} file - The video/audio/text file to analyze
 */
export async function predictStimulus(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post("/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export default apiClient;