import { useState, useEffect } from "react";
import { checkHealth } from "./services/api";
import { usePrediction } from "./hooks/usePrediction";
import LoadingState from "./components/LoadingState";
import Results from "./components/Results";

const EXAMPLES = [
  "The cat sat on the mat. The dog ran fast.",
  "Quantum entanglement violates locality assumptions.",
  "Please pass the salt. I would like a glass of water.",
];

function App() {
  const [backendStatus, setBackendStatus] = useState("checking…");
  const [text, setText] = useState(EXAMPLES[0]);
  const { isLoading, result, error, runPrediction, reset } = usePrediction();

  useEffect(() => {
    checkHealth()
      .then((data) => {
        if (data.status === "connected") {
          setBackendStatus("✅ Connected to Hugging Face Space");
        } else {
          setBackendStatus("⚠️ Space unreachable");
        }
      })
      .catch(() => setBackendStatus("⚠️ Space unreachable"));
  }, []);

  const handleSubmit = () => {
    if (!text.trim()) return;
    runPrediction({ text, nTimesteps: 10 });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Resonate</h1>
            <p className="text-xs text-slate-500">
              Neural Stimulus Optimizer for Speech-Language Pathology
            </p>
          </div>
          <div className="text-xs text-slate-500">{backendStatus}</div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-6">
        {/* Input panel — always visible */}
        {!result && !isLoading && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-1">
                Predict Brain Engagement
              </h2>
              <p className="text-sm text-slate-600">
                Enter a therapy stimulus (text). The model predicts cortical
                activation across language regions: Broca's, Wernicke's, SMA,
                and Angular Gyrus.
              </p>
            </div>

            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={4}
              placeholder="Enter therapy text…"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-slate-900"
            />

            <div className="flex flex-wrap gap-2 text-xs">
              <span className="text-slate-500 mr-1">Examples:</span>
              {EXAMPLES.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setText(ex)}
                  className="px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700"
                >
                  {ex.slice(0, 30)}…
                </button>
              ))}
            </div>

            <button
              onClick={handleSubmit}
              disabled={!text.trim() || isLoading}
              className="w-full px-5 py-3 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg font-medium"
            >
              Generate Brain Prediction
            </button>

            <p className="text-xs text-slate-500">
              First request can take 30–90 seconds (Hugging Face GPU
              cold-start). Subsequent requests are fast.
            </p>
          </div>
        )}

        {/* Loading */}
        {isLoading && <LoadingState filename="your stimulus" />}

        {/* Error */}
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
        {result && !isLoading && <Results result={result} onReset={reset} />}
      </main>

      <footer className="text-center text-xs text-slate-400 py-6">
        Built on Meta TRIBE v2 - CC BY-NC 4.0 - Educational research prototype.
        Not a medical device.
        <br />
        
          <a href="https://huggingface.co/spaces/rohany395/neuro-cue"
          target="_blank"
          rel="noreferrer"
          className="underline hover:text-slate-600"
        >
          View live Space
        </a>
        {" - "}
        <a
          href="https://github.com/rohany395/neuro-cue"
          target="_blank"
          rel="noreferrer"
          className="underline hover:text-slate-600"
        >
          Source on GitHub
        </a>
      </footer>
    </div>
  );
}

export default App;