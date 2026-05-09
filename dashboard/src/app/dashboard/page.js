"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { callMCPTool } from "@/lib/mcp";

function Badge({ children, color }) {
  const colors = {
    red: "bg-red-100 text-red-700",
    amber: "bg-amber-100 text-amber-700",
    green: "bg-green-100 text-green-700",
    gray: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded ${colors[color] || colors.gray}`}>
      {children}
    </span>
  );
}

function news2Color(level) {
  if (level === "HIGH") return "red";
  if (level === "MEDIUM") return "amber";
  return "green";
}

function dischargeColor(status) {
  if (status === "Ready") return "green";
  if (status === "Requires Review") return "amber";
  return "red";
}

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    callMCPTool("get_ward_round_summary")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500">Loading ward data...</p>;
  if (error) return <p className="text-red-600">Error: {error}</p>;
  if (!data) return <p className="text-gray-500">No data available.</p>;

  const patients = data.patients || [];

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-1">General Medicine Ward</h2>
        <p className="text-sm text-gray-500">{data.date}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Stat label="Total Patients" value={data.total_patients} />
        <Stat label="High Risk" value={data.high_risk_count} color="text-red-600" />
        <Stat label="Active Conflicts" value={data.active_conflicts} color="text-amber-600" />
        <Stat label="Discharge Ready" value={data.discharge_candidates} color="text-green-600" />
      </div>

      {/* Patient Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left text-gray-500 text-xs uppercase">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Bed</th>
              <th className="px-4 py-2">Diagnosis</th>
              <th className="px-4 py-2">LOS</th>
              <th className="px-4 py-2">NEWS2</th>
              <th className="px-4 py-2">Conflicts</th>
              <th className="px-4 py-2">Discharge</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {patients.map((p) => (
              <tr key={p.patient_id} className="hover:bg-gray-50 cursor-pointer">
                <td className="px-4 py-3">
                  <Link href={`/dashboard/patient/${p.patient_id}`} className="text-blue-600 hover:underline font-medium">
                    {p.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-gray-600">{p.encounter?.bed || "-"}</td>
                <td className="px-4 py-3 text-gray-600 max-w-[200px] truncate">
                  {p.encounter?.admitting_diagnosis || "-"}
                </td>
                <td className="px-4 py-3 text-gray-600">{p.encounter?.length_of_stay || "-"}d</td>
                <td className="px-4 py-3">
                  <Badge color={news2Color(p.news2?.risk_level)}>
                    {p.news2?.total_score ?? "-"} {p.news2?.risk_level}
                  </Badge>
                </td>
                <td className="px-4 py-3">
                  {p.conflict_count > 0 ? (
                    <Badge color="red">{p.conflict_count} conflict{p.conflict_count > 1 ? "s" : ""}</Badge>
                  ) : (
                    <span className="text-gray-400 text-xs">None</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <Badge color={dischargeColor(p.discharge?.status)}>
                    {p.discharge?.status || "-"}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Stat({ label, value, color = "text-gray-900" }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <p className="text-xs text-gray-500 uppercase">{label}</p>
      <p className={`text-2xl font-semibold ${color}`}>{value ?? 0}</p>
    </div>
  );
}
