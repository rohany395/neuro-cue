export default function ResultsRaw({ result, onReset }) {
    return (
      <div className="bg-white border rounded-2xl p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-xl font-bold text-slate-900">
              Prediction Results
            </h3>
            <p className="text-sm text-slate-500">
              {result.stimulus_type} · {result.duration_seconds.toFixed(1)}s ·{" "}
              {result.n_timesteps} timesteps
              {result.is_mock && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded">
                  MOCK DATA
                </span>
              )}
            </p>
          </div>
          <button
            onClick={onReset}
            className="px-4 py-2 text-sm bg-slate-100 hover:bg-slate-200 rounded-lg font-medium"
          >
            Upload Another
          </button>
        </div>
  
        {/* ROI Scorecards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {result.roi_scores.map((roi) => (
            <div
              key={roi.name}
              className="border rounded-xl p-4 bg-slate-50"
            >
              <p className="text-xs uppercase tracking-wider text-slate-500 mb-1">
                {roi.full_name}
              </p>
              <p className="text-2xl font-bold text-slate-900">
                {roi.score.toFixed(3)}
              </p>
              <p
                className={`text-xs font-medium mt-1 ${
                  roi.interpretation === "high"
                    ? "text-emerald-600"
                    : roi.interpretation === "moderate"
                    ? "text-amber-600"
                    : "text-slate-500"
                }`}
              >
                {roi.interpretation}
              </p>
            </div>
          ))}
        </div>
  
        {/* Recommendation */}
        <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 mb-6">
          <p className="text-xs uppercase tracking-wider text-indigo-700 font-semibold mb-1">
            Clinical Interpretation
          </p>
          <p className="text-sm text-slate-800">{result.recommendation}</p>
        </div>
  
        {/* Raw JSON for debugging */}
        <details className="text-xs">
          <summary className="cursor-pointer text-slate-500 hover:text-slate-700">
            View raw response (debug)
          </summary>
          <pre className="mt-2 p-4 bg-slate-900 text-slate-100 rounded-lg overflow-x-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </details>
      </div>
    );
  }