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
  
  export default function EngagementChart({ temporalScores, currentTime }) {
    if (!temporalScores || temporalScores.length === 0) {
      return null;
    }
  
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <h2 className="text-sm font-semibold text-slate-900 mb-1">
          Activation Over Time
        </h2>
        <p className="text-xs text-slate-500 mb-4">
          Predicted mean activation per language region across timesteps 
          {typeof currentTime === "number" && (
            <span className="ml-2 font-mono text-slate-700">
              ● t = {currentTime.toFixed(1)}s
            </span>
          )}
        </p>
  
        <ResponsiveContainer width="100%" height={280}>
          <LineChart
            data={temporalScores}
            margin={{ top: 5, right: 20, left: 0, bottom: 25 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="time_seconds"
              label={{
                value: "Time (seconds)",
                position: "insideBottom",
                offset: -10,
                style: { fontSize: 12, fill: "#64748b" },
              }}
              tick={{ fontSize: 11, fill: "#64748b" }}
              tickFormatter={(v) => `${v.toFixed(1)}s`}
            />
            <YAxis
              label={{
                value: "Activation",
                angle: -90,
                position: "insideLeft",
                style: { fontSize: 12, fill: "#64748b" },
              }}
              tick={{ fontSize: 11, fill: "#64748b" }}
              tickFormatter={(v) => v.toFixed(2)}
            />
            <Tooltip
              contentStyle={{
                fontSize: 12,
                borderRadius: 8,
                border: "1px solid #e2e8f0",
              }}
              formatter={(value, name) => [
                value.toFixed(3),
                ROI_LABELS[name] || name,
              ]}
              labelFormatter={(v) => `t = ${Number(v).toFixed(1)}s`}
            />
            <Legend
              wrapperStyle={{ fontSize: 12, paddingTop: 10 }}
              formatter={(value) => ROI_LABELS[value] || value}
            />
            {Object.entries(ROI_COLORS).map(([key, color]) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={color}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
                isAnimationActive={false}
              />
            ))}
            {typeof currentTime === "number" && (
              <ReferenceLine
                x={currentTime}
                stroke="#0f172a"
                strokeWidth={2}
                strokeDasharray="0"
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }