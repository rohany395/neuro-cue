import { useState, useRef } from "react";

const ACCEPTED_EXTENSIONS = ".mp4,.mov,.webm";

export default function FileUpload({ onFileSelected, currentFile, disabled }) {
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
    e.target.value = "";
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        border-2 border-dashed rounded-lg p-6 text-center cursor-pointer
        transition-colors
        ${disabled
          ? "border-slate-200 bg-slate-50 cursor-not-allowed opacity-60"
          : isDragging
          ? "border-slate-900 bg-slate-100"
          : "border-slate-300 bg-white hover:border-slate-500 hover:bg-slate-50"
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

      {currentFile ? (
        <>
          <p className="text-sm font-semibold text-slate-900 mb-1">
            {currentFile.name}
          </p>
          <p className="text-xs text-slate-500">
            {(currentFile.size / (1024 * 1024)).toFixed(1)} MB - click to replace
          </p>
        </>
      ) : (
        <>
          <p className="text-sm font-semibold text-slate-900 mb-1">
            Drop a video file here
          </p>
          <p className="text-xs text-slate-500 mb-1">or click to browse</p>
          <p className="text-xs text-slate-400">MP4, MOV, WebM</p>
        </>
      )}
    </div>
  );
}