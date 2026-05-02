import { useState } from "react";
import { predictStimulus } from "../services/api";

/**
 * Manages the prediction lifecycle:
 *   - file selected
 *   - loading state during inference
 *   - results
 *   - errors
 */
export function usePrediction() {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  async function runPrediction(uploadedFile) {
    setFile(uploadedFile);
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await predictStimulus(uploadedFile);
      setResult(data);
    } catch (err) {
      console.error("Prediction failed:", err);
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Something went wrong. Check that the backend is running.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  function reset() {
    setFile(null);
    setIsLoading(false);
    setResult(null);
    setError(null);
  }

  return { file, isLoading, result, error, runPrediction, reset };
}
