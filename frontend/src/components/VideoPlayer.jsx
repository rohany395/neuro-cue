import { useRef, useEffect } from "react";

export default function VideoPlayer({ src, onTimeUpdate, maxSeconds }) {
  const videoRef = useRef(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      if (maxSeconds != null && video.currentTime >= maxSeconds) {
        video.pause();
        video.currentTime = maxSeconds;
      }
      onTimeUpdate?.(Math.min(video.currentTime, maxSeconds ?? Infinity));
    };

    video.addEventListener("timeupdate", handleTimeUpdate);
    return () => video.removeEventListener("timeupdate", handleTimeUpdate);
  }, [onTimeUpdate, maxSeconds]);

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