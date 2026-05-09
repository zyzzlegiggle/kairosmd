"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { callMCPTool } from "@/lib/mcp";

export default function ConflictsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    callMCPTool("get_conflict_report")
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading conflicts...</p>;
  if (!data) return <p className="text-gray-500">No data.</p>;

  return (
    <div>
      <h2 className="text-xl font-semibold mb-1">Conflict Report</h2>
      <p className="text-sm text-gray-500 mb-6">
        {data.patients_with_conflicts} patient(s) with {data.total_conflicts} total conflict(s)
      </p>

      {(data.patients || []).map((p) => (
        <div key={p.patient_id} className="border border-gray-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <Link href={`/dashboard/patient/${p.patient_id}`} className="text-blue-600 hover:underline font-medium">
              {p.name}
            </Link>
            <span className="text-xs text-gray-500">{p.encounter?.bed}</span>
          </div>
          {(p.conflicts || []).map((c, i) => (
            <div key={i} className="bg-red-50 border border-red-200 rounded p-3 mb-2 text-sm">
              <span className="font-medium text-red-700">[{c.severity}]</span>{" "}
              <span className="text-red-900">{c.message}</span>
            </div>
          ))}
        </div>
      ))}

      {(data.patients || []).length === 0 && (
        <p className="text-gray-400">No conflicts detected across the ward.</p>
      )}
    </div>
  );
}
