import { useState } from "react";
import { predictStimulus } from "../services/api";

export function usePrediction() {
  const [isLoading, setIsLoading] = useState(false);
  const [phase, setPhase] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [lastInput, setLastInput] = useState(null);

  async function runPrediction(input) {
    setLastInput(input);
    setIsLoading(true);
    setPhase(null);
    setError(null);
    setResult(null);

    try {
      const data = await predictStimulus({ ...input, onPhase: setPhase });
      setResult(data);
    } catch (err) {
      console.error("Prediction failed:", err);
      const message =
        err?.message ||
        "Prediction failed. The Space may be cold-starting — try again in 30 seconds.";
      setError(message);
    } finally {
      setIsLoading(false);
      setPhase(null);
    }
  }

  function reset() {
    setIsLoading(false);
    setPhase(null);
    setResult(null);
    setError(null);
    setLastInput(null);
  }

  return { lastInput, isLoading, phase, result, error, runPrediction, reset };
}