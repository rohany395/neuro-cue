import EngagementChart from "./EngagementChart";

const ENGAGEMENT_COLORS = {
  high: "text-emerald-600",
  moderate: "text-amber-600",
  low: "text-slate-500",
};

const ENGAGEMENT_LABELS = {
  high: "High",
  moderate: "Moderate",
  low: "Low",
};

export default function Results({ result, onReset }) {
  if (!result) return null;

  const { brain_html, roi_scores, temporal_scores, metadata } = result;

  return (
    <div className="space-y-6">
      {/* Status bar */}
      <div className="text-xs text-slate-500 font-mono">
        ✓ {metadata.n_timesteps} timesteps × {metadata.n_vertices.toLocaleString()} vertices
        {" | "}
        TR = {metadata.tr_seconds}s
        {" | "}
        Stimulus: {metadata.stimulus_type}
      </div>

      {/* Top row: brain + ROI cards */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Brain heatmap */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-900 mb-3">
            Cortical Activation Map
          </h2>
          <div
            className="w-full"
            dangerouslySetInnerHTML={{ __html: brain_html }}
          />
        </div>

        {/* ROI cards */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4">
          <h2 className="text-sm font-semibold text-slate-900 mb-1">
            Clinical Insights
          </h2>
          <p className="text-xs text-slate-500 mb-4">
            Language ROI scores (left hemisphere)
          </p>
          <div className="space-y-3">
            {roi_scores.map((roi) => (
              <div
                key={roi.roi_key}
                className="border border-slate-200 rounded-lg p-3"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-slate-900">
                    {roi.roi_name}
                  </span>
                  <span
                    className={`text-xs font-medium ${
                      ENGAGEMENT_COLORS[roi.engagement_level]
                    }`}
                  >
                    ● {ENGAGEMENT_LABELS[roi.engagement_level]}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mb-2 leading-relaxed">
                  {roi.function}
                </p>
                <div className="flex gap-3 text-xs font-mono text-slate-600">
                  <span>peak: <b>{roi.peak >= 0 ? "+" : ""}{roi.peak.toFixed(3)}</b></span>
                  <span>mean: <b>{roi.mean >= 0 ? "+" : ""}{roi.mean.toFixed(3)}</b></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Temporal chart - full width */}
      <EngagementChart temporalScores={temporal_scores} />

      {/* Reset button */}
      <div className="flex justify-center pt-2">
        <button
          onClick={onReset}
          className="px-5 py-2 text-sm bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium"
        >
          Try Another Stimulus
        </button>
      </div>
    </div>
  );
}