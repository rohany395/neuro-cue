import { useRef, useEffect, useState } from "react";

/**
 * Plays an uploaded video/audio file with custom controls.
 * Reports current time + duration up to parent via onTimeUpdate.
 *
 * For text stimuli, shows a text-mode placeholder with a virtual playhead
 * that the parent can advance.
 */
export default function StimulusPlayer({
  file,
  stimulusType,
  duration,
  onTimeUpdate,
  isPlaying,
  setIsPlaying,
  currentTime,
  onSeek,
}) {
  const mediaRef = useRef(null);
  const [mediaURL, setMediaURL] = useState(null);

  // Create an object URL for the uploaded file so we can play it
  useEffect(() => {
    if (!file || stimulusType === "text") return;
    const url = URL.createObjectURL(file);
    setMediaURL(url);
    // Cleanup on unmount
    return () => URL.revokeObjectURL(url);
  }, [file, stimulusType]);

  // Wire up the media element's events
  useEffect(() => {
    const media = mediaRef.current;
    if (!media) return;

    function handleTimeUpdate() {
      onTimeUpdate(media.currentTime);
    }
    function handleEnded() {
      setIsPlaying(false);
    }

    media.addEventListener("timeupdate", handleTimeUpdate);
    media.addEventListener("ended", handleEnded);
    return () => {
      media.removeEventListener("timeupdate", handleTimeUpdate);
      media.removeEventListener("ended", handleEnded);
    };
  }, [onTimeUpdate, setIsPlaying]);

  // Sync isPlaying state with the actual media element
  useEffect(() => {
    const media = mediaRef.current;
    if (!media) return;
    if (isPlaying) {
      // If we're at the end, restart from beginning
      if (media.ended || media.currentTime >= media.duration - 0.05) {
        media.currentTime = 0;
      }
      media.play().catch(() => setIsPlaying(false));
    } else {
      media.pause();
    }
  }, [isPlaying, setIsPlaying]);

  // Seek the media element when parent updates currentTime (from scrubber)
  useEffect(() => {
    const media = mediaRef.current;
    if (!media || stimulusType === "text") return;
    if (Math.abs(media.currentTime - currentTime) > 0.1) {
      media.currentTime = currentTime;
    }
  }, [currentTime, stimulusType]);

  // For text mode, advance currentTime via interval when playing
  useEffect(() => {
    if (stimulusType !== "text" || !isPlaying) return;
    const interval = setInterval(() => {
      onTimeUpdate((t) => {
        const next = (t ?? 0) + 0.1;
        if (next >= duration) {
          setIsPlaying(false);
          return duration;
        }
        return next;
      });
    }, 100);
    return () => clearInterval(interval);
  }, [stimulusType, isPlaying, duration, onTimeUpdate, setIsPlaying]);

  return (
    <div className="bg-slate-900 rounded-2xl overflow-hidden">
      {/* Media element */}
      <div className="relative aspect-video bg-black flex items-center justify-center">
        {stimulusType === "video" && mediaURL && (
          <video
            ref={mediaRef}
            src={mediaURL}
            className="w-full h-full object-contain"
            playsInline
          />
        )}
        {stimulusType === "audio" && mediaURL && (
          <div className="text-center text-white">
            <div className="text-7xl mb-4">🎵</div>
            <p className="text-sm text-slate-300">{file.name}</p>
            <audio ref={mediaRef} src={mediaURL} className="hidden" />
          </div>
        )}
        {stimulusType === "text" && (
          <div className="text-center text-white p-8">
            <div className="text-7xl mb-4">📝</div>
            <p className="text-sm text-slate-300">Text stimulus</p>
            <p className="text-xs text-slate-500 mt-1">{file.name}</p>
          </div>
        )}
      </div>

      {/* Custom controls */}
      <div className="p-4 flex items-center gap-4">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="w-10 h-10 flex items-center justify-center rounded-full bg-white text-slate-900 hover:bg-slate-100 transition-colors"
        >
          {isPlaying ? (
            <span className="text-lg">⏸</span>
          ) : (
            <span className="text-lg pl-0.5">▶</span>
          )}
        </button>

        <div className="flex-1">
          <input
            type="range"
            min={0}
            max={duration}
            step={0.05}
            value={currentTime}
            onChange={(e) => onSeek(parseFloat(e.target.value))}
            className="w-full accent-indigo-500"
          />
        </div>

        <div className="text-xs text-slate-300 font-mono tabular-nums">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>
    </div>
  );
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}