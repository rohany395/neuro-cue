import { useState, useRef } from "react";

const ACCEPTED_EXTENSIONS = ".mp4,.mov,.mp3,.wav,.txt";

export default function FileUpload({ onFileSelected, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  function handleFile(file) {
    if (!file) return;
    onFileSelected(file);
  }

  function handleDragOver(e) {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    handleFile(e.dataTransfer.files?.[0]);
  }

  function handleClick() {
    if (!disabled) inputRef.current?.click();
  }

  function handleInputChange(e) {
    handleFile(e.target.files?.[0]);
    e.target.value = ""; // allow re-uploading the same file
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
        transition-colors
        ${disabled
          ? "border-slate-200 bg-slate-50 cursor-not-allowed opacity-60"
          : isDragging
          ? "border-indigo-500 bg-indigo-50"
          : "border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50"
        }
      `}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        onChange={handleInputChange}
        className="hidden"
      />

      <div className="text-5xl mb-3">📁</div>
      <p className="text-lg font-semibold text-slate-900 mb-1">
        Drop a stimulus file here
      </p>
      <p className="text-sm text-slate-500 mb-4">
        or click to browse
      </p>
      <p className="text-xs text-slate-400">
        Supports: MP4, MOV, MP3, WAV, TXT
      </p>
    </div>
  );
}