"use client";
import { useState, useEffect, use } from "react";
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

function Section({ title, children }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4 mb-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase">{title}</h3>
      {children}
    </div>
  );
}

export default function PatientDetailPage({ params }) {
  const { id } = use(params);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    callMCPTool("get_patient_ward_detail", { patient_id: id })
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-gray-500">Loading patient data...</p>;
  if (!data) return <p className="text-red-600">Patient not found.</p>;

  const briefing = data.llm_briefing || {};

  return (
    <div>
      <Link href="/dashboard" className="text-sm text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Ward</Link>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold">{data.name}</h2>
          <p className="text-sm text-gray-500">
            {data.gender} &middot; DOB: {data.birthDate} &middot; {data.encounter?.bed || ""}
          </p>
          <p className="text-sm text-gray-500">
            Admitted: {data.encounter?.admission_date?.slice(0, 10)} &middot; LOS: {data.encounter?.length_of_stay}d
          </p>
        </div>
        <div className="flex gap-2">
          <Badge color={data.news2?.risk_level === "HIGH" ? "red" : data.news2?.risk_level === "MEDIUM" ? "amber" : "green"}>
            NEWS2: {data.news2?.total_score} {data.news2?.risk_level}
          </Badge>
        </div>
      </div>

      {/* AI Overnight Summary */}
      <Section title="Overnight Summary (AI)">
        <p className="text-sm text-gray-700 leading-relaxed">{briefing.overnight_summary || "Not available"}</p>
      </Section>

      {/* Conflicts */}
      {data.conflicts?.length > 0 && (
        <Section title={`Conflicts (${data.conflict_count})`}>
          {data.conflicts.map((c, i) => (
            <div key={i} className="bg-red-50 border border-red-200 rounded p-3 mb-2 text-sm">
              <span className="font-medium text-red-700">[{c.severity}]</span>{" "}
              <span className="text-red-900">{c.message}</span>
            </div>
          ))}
          {briefing.conflict_highlights && (
            <p className="text-sm text-gray-600 mt-2 italic">{briefing.conflict_highlights}</p>
          )}
        </Section>
      )}

      {/* Ward Round Talking Points */}
      <Section title="Ward Round Talking Points">
        <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
          {(briefing.ward_round_talking_points || []).map((pt, i) => (
            <li key={i}>{pt}</li>
          ))}
        </ul>
      </Section>

      {/* Vital Trends */}
      <Section title="Vital Trends (24h)">
        <table className="w-full text-sm">
          <thead className="text-xs text-gray-500 uppercase">
            <tr><th className="text-left py-1">Parameter</th><th>Oldest</th><th>Latest</th><th>Trend</th></tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {(data.vital_trends || []).map((t, i) => (
              <tr key={i} className={t.concerning ? "text-red-700 font-medium" : ""}>
                <td className="py-1">{t.parameter}</td>
                <td className="text-center">{t.oldest}</td>
                <td className="text-center">{t.newest}</td>
                <td className="text-center">{t.direction} {t.concerning ? "⚠" : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      {/* Lab Trends */}
      {data.lab_trends?.length > 0 && (
        <Section title="Lab Trends">
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-500 uppercase">
              <tr><th className="text-left py-1">Lab</th><th>Previous</th><th>Latest</th><th>Trend</th></tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.lab_trends.map((t, i) => (
                <tr key={i}>
                  <td className="py-1">{t.parameter}</td>
                  <td className="text-center">{t.oldest}</td>
                  <td className="text-center">{t.newest}</td>
                  <td className="text-center">{t.direction}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {/* Discharge Readiness */}
      <Section title="Discharge Readiness">
        <Badge color={data.discharge?.status === "Ready" ? "green" : data.discharge?.status === "Requires Review" ? "amber" : "red"}>
          {data.discharge?.summary || data.discharge?.status}
        </Badge>
        <div className="mt-3 space-y-1">
          {(data.discharge?.checklist || []).map((c, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span>{c.met ? "✓" : "✗"}</span>
              <span className={c.met ? "text-gray-600" : "text-red-600"}>{c.item}: {c.detail}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Suggested Plan Adjustments */}
      <Section title="Suggested Plan Adjustments (AI)">
        <p className="text-sm text-gray-700">{briefing.suggested_plan_adjustments || "Not available"}</p>
      </Section>

      {/* Clinical Notes */}
      <Section title="Clinical Notes">
        {(data.clinical_notes || []).map((n, i) => (
          <div key={i} className="mb-3 border-l-2 border-gray-300 pl-3">
            <p className="text-xs text-gray-400">{n.type} — {n.date?.slice(0, 16)}</p>
            <p className="text-sm text-gray-700 mt-1">{n.text?.slice(0, 500)}</p>
          </div>
        ))}
      </Section>
    </div>
  );
}
