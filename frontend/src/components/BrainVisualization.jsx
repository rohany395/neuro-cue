import { useState, useEffect, useMemo } from "react";

const API_BASE_URL = "http://localhost:8000";

export default function BrainVisualization({
  sessionId,
  currentTime,
  duration,
  nTimesteps,
}) {
  const [loadedFrames, setLoadedFrames] = useState({});
  const [isLoadingInitial, setIsLoadingInitial] = useState(true);

  // Compute current frame index from time
  const currentFrameIdx = useMemo(() => {
    return Math.min(
      nTimesteps - 1,
      Math.max(0, Math.floor((currentTime / duration) * nTimesteps))
    );
  }, [currentTime, duration, nTimesteps]);

  // Pre-load all frames in the background once we have a session
  useEffect(() => {
    if (!sessionId) return;
    setIsLoadingInitial(true);

    async function loadAllFrames() {
      const frames = {};
      for (let i = 0; i < nTimesteps; i++) {
        try {
          const res = await fetch(
            `${API_BASE_URL}/brain-frame/${sessionId}/${i}`
          );
          if (res.ok) {
            frames[i] = await res.text();
          }
          // Show first frame as soon as it loads
          if (i === 0) {
            setLoadedFrames({ 0: frames[0] });
            setIsLoadingInitial(false);
          }
          // Update incrementally as more frames load
          if (i > 0 && i % 5 === 0) {
            setLoadedFrames({ ...frames });
          }
        } catch (err) {
          console.error(`Failed to load frame ${i}:`, err);
        }
      }
      setLoadedFrames(frames);
    }

    loadAllFrames();
  }, [sessionId, nTimesteps]);

  const currentFrameHtml = loadedFrames[currentFrameIdx];
  const totalLoaded = Object.keys(loadedFrames).length;
  const loadProgress = Math.round((totalLoaded / nTimesteps) * 100);

  return (
    <div className="relative w-full h-[500px] bg-slate-900 rounded-2xl overflow-hidden">
      {isLoadingInitial && (
        <div className="absolute inset-0 flex items-center justify-center text-white">
          <div className="text-center">
            <div className="inline-block w-12 h-12 border-4 border-slate-600 border-t-white rounded-full animate-spin mb-4" />
            <p className="text-sm">Rendering brain heatmaps...</p>
            <p className="text-xs text-slate-400 mt-1">
              {totalLoaded} / {nTimesteps} frames
            </p>
          </div>
        </div>
      )}

      {currentFrameHtml && (
        <iframe
          srcDoc={currentFrameHtml}
          title="Brain Heatmap"
          className="w-full h-full border-0"
          sandbox="allow-scripts allow-same-origin"
        />
      )}

      {/* Status overlay */}
      <div className="absolute top-3 right-3 px-2 py-1 text-xs bg-slate-800/80 text-white rounded font-mono pointer-events-none">
        t = {currentTime.toFixed(1)}s · frame {currentFrameIdx + 1}/
        {nTimesteps}
      </div>

      {/* Loading progress overlay (after initial frame is ready) */}
      {!isLoadingInitial && loadProgress < 100 && (
        <div className="absolute bottom-3 left-3 px-3 py-1.5 text-xs bg-slate-800/80 text-white rounded">
          Loading frames: {loadProgress}%
        </div>
      )}
    </div>
  );
}