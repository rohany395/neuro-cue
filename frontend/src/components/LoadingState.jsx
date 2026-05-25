export default function LoadingState({ filename, phase }) {
  const title =
    phase === "uploading"
      ? "Uploading video to Hugging Face..."
      : "Running prediction...";

  const subtitle =
    phase === "uploading"
      ? "Large files upload directly to the Space (not through Vercel)."
      : "Running TRIBE v2 inference and mapping language ROIs";

  return (
    <div className="bg-white border rounded-2xl p-12 text-center">
      <div className="inline-block w-12 h-12 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mb-4" />
      <p className="text-lg font-semibold text-slate-900 mb-1">{title}</p>
      {filename && <p className="text-sm text-slate-500 mb-3">{filename}</p>}
      <p className="text-xs text-slate-400">{subtitle}</p>
    </div>
  );
}