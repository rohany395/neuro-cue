import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ReferenceLine,
    ResponsiveContainer,
  } from "recharts";
  
  // Match the ROI colors from BrainVisualization
  const ROI_COLORS = {
    broca: "#ef4444",
    wernicke: "#3b82f6",
    sma: "#10b981",
    angular: "#a855f7",
  };
  
  const ROI_LABELS = {
    broca: "Broca's",
    wernicke: "Wernicke's",
    sma: "SMA",
    angular: "Angular",
  };
  
  /**
   * Map a timestep index to its corresponding time in seconds.
   * (Backend assumes TR=1.5s; total duration / n_timesteps gives effective TR.)
   */
  function buildChartData(temporalCurves, duration, nTimesteps) {
    const dt = duration / nTimesteps;
    return temporalCurves.map((point, idx) => ({
      time: idx * dt,
      broca: point.broca,
      wernicke: point.wernicke,
      sma: point.sma,
      angular: point.angular,
    }));
  }
  
  /**
   * Custom tooltip — shows time + all four ROI values.
   */
  function CustomTooltip({ active, payload, label }) {
    if (!active || !payload || !payload.length) return null;
  
    return (
      <div className="bg-white border rounded-lg shadow-lg p-3 text-xs">
        <p className="font-semibold text-slate-700 mb-2">
          t = {label.toFixed(1)}s
        </p>
        {payload.map((entry) => (
          <div
            key={entry.dataKey}
            className="flex items-center gap-2 py-0.5"
          >
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-slate-600">
              {ROI_LABELS[entry.dataKey]}:
            </span>
            <span className="font-mono font-semibold">
              {entry.value.toFixed(3)}
            </span>
          </div>
        ))}
      </div>
    );
  }
  
  export default function EngagementChart({
    temporalCurves,
    duration,
    nTimesteps,
    currentTime,
    onSeek,
  }) {
    const data = buildChartData(temporalCurves, duration, nTimesteps);
  
    // Allow click-to-seek on the chart
    function handleClick(state) {
      if (state && state.activeLabel !== undefined && onSeek) {
        onSeek(state.activeLabel);
      }
    }
  
    return (
      <div className="bg-white border rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="font-semibold text-slate-900">
              Engagement Over Time
            </h4>
            <p className="text-xs text-slate-500">
              Predicted activation per ROI · click chart to scrub
            </p>
          </div>
        </div>
  
        <div className="w-full h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={data}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
              onClick={handleClick}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="time"
                type="number"
                domain={[0, duration]}
                tickFormatter={(t) => `${t.toFixed(0)}s`}
                tick={{ fontSize: 11, fill: "#64748b" }}
                stroke="#cbd5e1"
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#64748b" }}
                stroke="#cbd5e1"
                tickFormatter={(v) => v.toFixed(1)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                wrapperStyle={{ fontSize: 12 }}
                formatter={(value) => ROI_LABELS[value] || value}
              />
  
              {/* Playhead — synced to video time */}
              <ReferenceLine
                x={currentTime}
                stroke="#1e293b"
                strokeWidth={2}
                strokeDasharray="4 2"
                label={{
                  value: "▼",
                  position: "top",
                  fill: "#1e293b",
                  fontSize: 12,
                }}
              />
  
              <Line
                type="monotone"
                dataKey="broca"
                stroke={ROI_COLORS.broca}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="wernicke"
                stroke={ROI_COLORS.wernicke}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="sma"
                stroke={ROI_COLORS.sma}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="angular"
                stroke={ROI_COLORS.angular}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    );
  }