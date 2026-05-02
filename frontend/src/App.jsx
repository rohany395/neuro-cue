import { useState, useEffect } from "react";
import { checkHealth } from "./services/api";

function App() {
  const [backendStatus, setBackendStatus] = useState("checking...");
  const [mockMode, setMockMode] = useState(null);

  useEffect(() => {
    checkHealth()
      .then((data) => {
        setBackendStatus("✅ Connected");
        setMockMode(data.mock_mode);
      })
      .catch((err) => {
        console.error(err);
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

      {/* Main content */}
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="bg-white rounded-2xl shadow-sm border p-12 text-center">
          <div className="text-5xl mb-4">🧠</div>
          <h2 className="text-3xl font-bold text-slate-900 mb-3">
            Welcome to Neuro cue
          </h2>
          <p className="text-slate-600 max-w-xl mx-auto mb-8">
            An educational research tool for predicting how speech therapy
            stimuli engage clinically relevant language regions of the brain.
          </p>
        </div>
      </main>

      <footer className="text-center text-xs text-slate-400 py-6">
        Built on Meta TRIBE v2 · CC BY-NC 4.0 · Educational use only
      </footer>
    </div>
  );
}

export default App;