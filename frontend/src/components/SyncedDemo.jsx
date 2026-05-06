import { useState } from "react";
import StimulusPlayer from "./StimulusPlayer";
import BrainVisualization from "./BrainVisualization";
import EngagementChart from "./EngagementChart";

export default function SyncedDemo({ file, result }) {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const duration = result.duration_seconds;

  function handleTimeUpdate(value) {
    if (typeof value === "function") {
      setCurrentTime((prev) => value(prev));
    } else {
      setCurrentTime(value);
    }
  }

  function handleSeek(time) {
    setCurrentTime(time);
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <StimulusPlayer
          file={file}
          stimulusType={result.stimulus_type}
          duration={duration}
          currentTime={currentTime}
          onTimeUpdate={handleTimeUpdate}
          onSeek={handleSeek}
          isPlaying={isPlaying}
          setIsPlaying={setIsPlaying}
        />
        <BrainVisualization
          sessionId={result.session_id}
          currentTime={currentTime}
          duration={duration}
          nTimesteps={result.n_timesteps}
        />
      </div>

      <EngagementChart
        temporalCurves={result.temporal_curves}
        duration={duration}
        nTimesteps={result.n_timesteps}
        currentTime={currentTime}
        onSeek={handleSeek}
      />
    </div>
  );
}