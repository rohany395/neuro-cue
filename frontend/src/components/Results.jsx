/**
 * Renders the brain visualization + clinical insights returned by the Gradio Space.
 * Outputs are HTML strings from the deployed inference backend.
 */
export default function Results({ result, onReset }) {
    if (!result) return null;
  
    const { brainHtml, clinicalHtml, status } = result;
  
    return (
      <div className="space-y-6">
        {/* Status bar */}
        {status && (
          <div className="text-xs text-slate-500 font-mono">{status}</div>
        )}
  
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Brain heatmap (2/3 width) */}
          <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-4">
            <h2 className="text-sm font-semibold text-slate-900 mb-3">
              Cortical Activation Map
            </h2>
            <div
              className="w-full"
              // The Gradio function returns a self-contained iframe — render it directly
              dangerouslySetInnerHTML={{ __html: brainHtml }}
            />
          </div>
  
          {/* Clinical insights (1/3 width) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <h2 className="text-sm font-semibold text-slate-900 mb-1">
              Clinical Insights
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Language ROI scores (left hemisphere)
            </p>
            <div
              className="text-sm"
              dangerouslySetInnerHTML={{ __html: clinicalHtml }}
            />
          </div>
        </div>
  
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