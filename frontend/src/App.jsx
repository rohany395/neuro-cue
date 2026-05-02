import { useState, useEffect } from "react";
import { checkHealth } from "./services/api";
import { usePrediction } from "./hooks/usePrediction";
import FileUpload from "./components/FileUpload";
import LoadingState from "./components/LoadingState";
import ResultsRaw from "./components/ResultsRaw";

function App() {
  const [backendStatus, setBackendStatus] = useState("checking...");
  const [mockMode, setMockMode] = useState(null);
  const { file, isLoading, result, error, runPrediction, reset } =
    usePrediction();

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setBackendStatus("✅ Connected");
        setMockMode(data.mock_mode);
      })
      .catch(() => {
        setBackendStatus("❌ Backend unreachable");
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Resonate</h1>
            <p className="text-xs text-slate-500">
              Predict brain engagement for speech therapy stimuli
            </p>
          </div>
          <div className="text-sm">
            <span className="text-slate-500">Backend: </span>
            <span className="font-medium">{backendStatus}</span>
            {mockMode === true && (
              <span className="ml-2 px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded">
                MOCK MODE
              </span>
            )}
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-4xl mx-auto px-6 py-12 space-y-6">
        {/* Empty state */}
        {!file && !isLoading && !result && (
          <>
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-slate-900 mb-2">
                Upload a stimulus
              </h2>
              <p className="text-slate-600">
                Get predicted engagement scores for Broca's, Wernicke's, SMA,
                and Angular Gyrus
              </p>
            </div>
            <FileUpload onFileSelected={runPrediction} disabled={isLoading} />
          </>
        )}

        {/* Loading state */}
        {isLoading && <LoadingState filename={file?.name} />}

        {/* Error state */}
        {error && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6">
            <p className="font-semibold text-red-900 mb-1">
              Prediction failed
            </p>
            <p className="text-sm text-red-700 mb-4">{error}</p>
            <button
              onClick={reset}
              className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium"
            >
              Try again
            </button>
          </div>
        )}

        {/* Results */}
        {result && !isLoading && (
          <ResultsRaw result={result} onReset={reset} />
        )}
      </main>

      <footer className="text-center text-xs text-slate-400 py-6">
        Built on Meta TRIBE v2 · CC BY-NC 4.0 · Educational use only
      </footer>
    </div>
  );
}

export default App;