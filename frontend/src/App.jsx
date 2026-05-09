import { useState, useEffect } from "react";
import { checkHealth } from "./services/api";
import { usePrediction } from "./hooks/usePrediction";
import LoadingState from "./components/LoadingState";
import Results from "./components/Results";
import FileUpload from "./components/FileUpload";

const EXAMPLES = [
  "The cat sat on the mat. The dog ran fast.",
  "Quantum entanglement violates locality assumptions.",
  "Please pass the salt. I would like a glass of water.",
];

function App() {
  const [backendStatus, setBackendStatus] = useState("checking...");
  const [modality, setModality] = useState("text");
  const [text, setText] = useState(EXAMPLES[0]);
  const [videoFile, setVideoFile] = useState(null);

  const { lastInput, isLoading, result, error, runPrediction, reset } =
    usePrediction();

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setBackendStatus(
          data.status === "connected"
            ? "Connected to Hugging Face Space"
            : "Space unreachable"
        );
      })
      .catch(() => setBackendStatus("Space unreachable"));
  }, []);

  const canSubmit =
    (modality === "text" && text.trim()) ||
    (modality === "video" && videoFile);

  const handleSubmit = () => {
    if (!canSubmit) return;
    runPrediction({
      modality,
      text,
      videoFile,
      nTimesteps: 10,
    });
  };

  const handleReset = () => {
    reset();
    // keep text/videoFile state — user might want to retry
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Neuro Cue</h1>
            <p className="text-xs text-slate-500">
                Interactive brain-encoding visualizer · Meta TRIBE v2
            </p>
          </div>
          <div className="text-xs text-slate-500">{backendStatus}</div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10 space-y-6">
        {!result && !isLoading && (
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-1">
                Predict Brain Engagement
              </h2>
              <p className="text-sm text-slate-600">
                Submit a therapy stimulus. The model predicts cortical
                activation across language regions: Broca's, Wernicke's, SMA,
                and Angular Gyrus.
              </p>
            </div>

            {/* Modality selector */}
            <div className="flex gap-2 border-b border-slate-200">
              {[
                { key: "text", label: "Text" },
                { key: "video", label: "Video" },
              ].map((m) => (
                <button
                  key={m.key}
                  onClick={() => setModality(m.key)}
                  className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
                    modality === m.key
                      ? "border-slate-900 text-slate-900"
                      : "border-transparent text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>

            {modality === "text" && (
              <>
                <textarea
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={4}
                  placeholder="Enter therapy text..."
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
                      {ex.slice(0, 30)}...
                    </button>
                  ))}
                </div>
              </>
            )}

            {modality === "video" && (
              <FileUpload
                onFileSelected={setVideoFile}
                currentFile={videoFile}
                disabled={isLoading}
              />
            )}

            <button
              onClick={handleSubmit}
              disabled={!canSubmit || isLoading}
              className="w-full px-5 py-3 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg font-medium"
            >
              Generate Brain Prediction
            </button>

            <p className="text-xs text-slate-500">
              Request can take upto few minutes while hugging face space is cold-starts.
            </p>
          </div>
        )}

        {isLoading && <LoadingState filename="your stimulus" />}

        {error && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-6">
            <p className="font-semibold text-red-900 mb-1">
              Prediction failed
            </p>
            <p className="text-sm text-red-700 mb-4">{error}</p>
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium"
            >
              Try again
            </button>
          </div>
        )}

        {result && !isLoading && (
          <Results result={result} lastInput={lastInput} onReset={handleReset} />
        )}
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
        
        <a href="https://github.com/rohany395/neuro-cue"
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