"use client";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const VITAL_LABELS = {
  "9279-1": { name: "Respiratory Rate", unit: "bpm", color: "#2563eb" },
  "59408-5": { name: "SpO2", unit: "%", color: "#16a34a" },
  "8480-6": { name: "Systolic BP", unit: "mmHg", color: "#7c3aed" },
  "8867-4": { name: "Heart Rate", unit: "bpm", color: "#dc2626" },
  "8310-5": { name: "Temperature", unit: "\u00B0C", color: "#d97706" },
  "67775-7": { name: "AVPU", unit: "", color: "#64748b" },
  "2708-6": { name: "SpO2", unit: "%", color: "#16a34a" },
};

function TrendArrow({ direction, concerning }) {
  if (direction === "increasing") {
    return <span className={`font-bold ${concerning ? "text-clinical-critical" : "text-text-secondary"}`}>{"\u2191"}</span>;
  }
  if (direction === "decreasing") {
    return <span className={`font-bold ${concerning ? "text-clinical-critical" : "text-clinical-info"}`}>{"\u2193"}</span>;
  }
  return <span className="text-text-tertiary">{"\u2192"}</span>;
}

export default function VitalChart({ trends }) {
  if (!trends || trends.length === 0) return <p className="text-sm text-text-tertiary">No observation data.</p>;

  return (
    <div className="grid grid-cols-2 gap-4">
      {trends.map((t, i) => {
        const meta = VITAL_LABELS[t.loinc] || { name: t.parameter || t.loinc, unit: "", color: "#64748b" };
        const displayName = meta.name;
        let points = [];
        if (t.history && t.history.length > 0) {
          points = t.history.map((h, idx) => ({
            name: new Date(h.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            value: h.value
          }));
        } else {
          points = [
            { name: "Prev", value: t.oldest },
            { name: "Now", value: t.newest },
          ];
        }
        
        const diff = t.newest - t.oldest;
        const sign = diff > 0 ? "+" : "";

        return (
          <div key={i} className={`rounded-lg border p-4 ${t.concerning ? "border-clinical-critical-border bg-clinical-critical-bg" : "border-border bg-surface-secondary"}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-text-primary">{displayName}</span>
              <div className="flex items-center gap-1.5">
                <TrendArrow direction={t.direction} concerning={t.concerning} />
                <span className={`text-[11px] font-semibold ${t.concerning ? "text-clinical-critical" : "text-text-secondary"}`}>
                  {sign}{diff.toFixed(1)} {meta.unit}
                </span>
              </div>
            </div>
            <div className="flex items-end gap-4">
              <div className="flex-1 h-14">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={points}>
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke={t.concerning ? "#dc2626" : meta.color}
                      strokeWidth={2.5}
                      dot={{ r: 3, fill: t.concerning ? "#dc2626" : meta.color }}
                    />
                    <YAxis domain={["auto", "auto"]} hide />
                    <XAxis dataKey="name" hide />
                    <Tooltip
                      contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #e2e8f0" }}
                      formatter={(val) => [`${val} ${meta.unit}`, displayName]}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="text-right">
                <p className={`text-lg font-bold ${t.concerning ? "text-clinical-critical" : "text-text-primary"}`}>
                  {t.newest}
                </p>
                <p className="text-[10px] text-text-tertiary">{meta.unit}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
