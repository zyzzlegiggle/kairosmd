"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { callMCPTool } from "@/lib/mcp";

function Badge({ children, color }) {
  const colors = {
    green: "bg-green-100 text-green-700",
    amber: "bg-amber-100 text-amber-700",
    red: "bg-red-100 text-red-700",
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded ${colors[color] || "bg-gray-100 text-gray-600"}`}>
      {children}
    </span>
  );
}

export default function DischargePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    callMCPTool("get_discharge_candidates")
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading discharge candidates...</p>;
  if (!data) return <p className="text-gray-500">No data.</p>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-1">Discharge Candidates</h2>
      <p className="text-sm text-gray-500 mb-6">{data.candidate_count} candidate(s)</p>

      {(data.candidates || []).map((p) => (
        <div key={p.patient_id} className="border border-gray-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-2">
            <Link href={`/dashboard/patient/${p.patient_id}`} className="text-blue-600 hover:underline font-medium">
              {p.name}
            </Link>
            <div className="flex gap-2 items-center">
              <span className="text-xs text-gray-500">LOS: {p.encounter?.length_of_stay}d</span>
              <Badge color={p.discharge?.status === "Ready" ? "green" : "amber"}>
                {p.discharge?.status}
              </Badge>
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-2">{p.encounter?.admitting_diagnosis}</p>
          <div className="space-y-1">
            {(p.discharge?.checklist || []).map((c, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                <span className={c.met ? "text-green-600" : "text-red-600"}>{c.met ? "✓" : "✗"}</span>
                <span className="text-gray-600">{c.item}</span>
              </div>
            ))}
          </div>
        </div>
      ))}

      {(data.candidates || []).length === 0 && (
        <p className="text-gray-400">No discharge candidates at this time.</p>
      )}
    </div>
  );
}
