import { useState, useMemo } from "react";
import EngagementChart from "./EngagementChart";
import VideoPlayer from "./VideoPlayer";

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

export default function Results({ result, lastInput, onReset }) {
  const [currentTime, setCurrentTime] = useState(0);

  // Build a blob URL for the uploaded video file (so we can replay it)
  const videoSrc = useMemo(() => {
    if (lastInput?.modality === "video" && lastInput?.videoFile) {
      return URL.createObjectURL(lastInput.videoFile);
    }
    return null;
  }, [lastInput]);

  if (!result) return null;

  const { brain_html, roi_scores, temporal_scores, metadata } = result;
  const analysisWindowSec = metadata.n_timesteps * metadata.tr_seconds;
  const showVideo = videoSrc !== null;

  return (
    <div className="space-y-6">
      <div className="text-xs text-slate-500 font-mono">
        ✓ {metadata.n_timesteps} timesteps × {metadata.n_vertices.toLocaleString()} vertices
        {" | "}
        TR = {metadata.tr_seconds}s
        {" | "}
        Stimulus: {metadata.stimulus_type}
      </div>

      {/* Top: Video (if any) | Brain heatmap */}
      <div className={`grid ${showVideo ? "lg:grid-cols-2" : "lg:grid-cols-3"} gap-6`}>
      {showVideo && (
        <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <h2 className="text-sm font-semibold text-slate-900 mb-3">
            Stimulus Video
            </h2>
            <VideoPlayer
            src={videoSrc}
            onTimeUpdate={setCurrentTime}
            maxSeconds={analysisWindowSec}
            />
            <p className="text-xs text-slate-500 mt-2">
            Brain prediction covers the first {analysisWindowSec}s of the stimulus.
            Playback stops at the analysis boundary.
            </p>
        </div>
        )}

        <div className={`${showVideo ? "" : "lg:col-span-2"} bg-white rounded-2xl border border-slate-200 p-4`}>
          <h2 className="text-sm font-semibold text-slate-900 mb-3">
            Predicted Cortical Activation
          </h2>
          <div
            className="w-full"
            dangerouslySetInnerHTML={{ __html: brain_html }}
          />
        </div>
      </div>

      {/* ROI cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {roi_scores.map((roi) => (
          <div
            key={roi.roi_key}
            className="bg-white border border-slate-200 rounded-xl p-4"
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

      {/* Temporal chart with cursor */}
      <EngagementChart temporalScores={temporal_scores} currentTime={showVideo ? currentTime : undefined} />

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