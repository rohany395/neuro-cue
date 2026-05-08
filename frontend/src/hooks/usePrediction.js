import { useState } from "react";
import { predictStimulus } from "../services/api";

export function usePrediction() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [lastInput, setLastInput] = useState(null);

  async function runPrediction(input) {
    setLastInput(input);
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await predictStimulus(input);
      setResult(data);
    } catch (err) {
      console.error("Prediction failed:", err);
      const message =
        err?.message ||
        "Prediction failed. The Space may be cold-starting — try again in 30 seconds.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  function reset() {
    setIsLoading(false);
    setResult(null);
    setError(null);
    setLastInput(null);
  }

  return { lastInput, isLoading, result, error, runPrediction, reset };
}