import { useRef, useEffect } from "react";

/**
 * Video player that exposes currentTime via the onTimeUpdate callback.
 * The parent uses this to drive the cursor on the temporal chart.
 */
export default function VideoPlayer({ src, onTimeUpdate }) {
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !onTimeUpdate) return;

    const handleTimeUpdate = () => {
      onTimeUpdate(video.currentTime);
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => video.removeEventListener("timeupdate", handleTimeUpdate);
  }, [onTimeUpdate]);

  return (
    <video
      ref={videoRef}
      src={src}
      controls
      className="w-full rounded-lg bg-black"
      style={{ maxHeight: "400px" }}
    />
  );
}