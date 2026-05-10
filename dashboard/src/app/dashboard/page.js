"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { callMCPTool } from "@/lib/mcp";

function StatCard({ label, value, variant = "default" }) {
  const colors = {
    default: "border-border",
    critical: "border-clinical-critical bg-clinical-critical-bg",
    warning: "border-clinical-warning bg-clinical-warning-bg",
    success: "border-clinical-normal bg-clinical-normal-bg",
  };
  const textColors = {
    default: "text-text-primary",
    critical: "text-clinical-critical",
    warning: "text-clinical-warning",
    success: "text-clinical-normal",
  };
  return (
    <div className={`bg-white rounded-xl border ${colors[variant]} p-5`}>
      <p className="text-[11px] font-semibold text-text-tertiary uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-3xl font-bold ${textColors[variant]}`}>{value ?? 0}</p>
    </div>
  );
}

function NEWS2Badge({ score, level }) {
  const colors = {
    HIGH: "bg-clinical-critical text-white",
    MEDIUM: "bg-clinical-warning text-white",
    LOW: "bg-clinical-normal-bg text-clinical-normal border border-clinical-normal-border",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full ${colors[level] || colors.LOW}`}>
      {score}
    </span>
  );
}

function PriorityDot({ level }) {
  const colors = {
    HIGH: "bg-clinical-critical",
    MEDIUM: "bg-clinical-warning",
    LOW: "bg-clinical-normal",
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${colors[level] || colors.LOW}`} />;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-5">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="skeleton h-24 rounded-xl" />
        ))}
      </div>
      <div className="skeleton h-96 rounded-xl" />
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: "priority_score", direction: "asc" });

  useEffect(() => {
    callMCPTool("get_ward_round_summary")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;
  if (error) return (
    <div className="bg-clinical-critical-bg border border-clinical-critical-border rounded-xl p-6">
      <p className="text-sm font-semibold text-clinical-critical">Connection Error</p>
      <p className="text-sm text-text-secondary mt-1">{error}</p>
    </div>
  );
  if (!data) return <p className="text-text-tertiary text-sm">No ward data available.</p>;

  const patients = [...(data.patients || [])];

  // Scoring for sorting
  const priorityMap = { HIGH: 0, MEDIUM: 1, LOW: 2 };
  const getVal = (p, key) => {
    if (key === "priority_score") return priorityMap[p.priority] ?? 3;
    if (key === "name") return p.name;
    if (key === "bed") return parseInt(p.encounter?.bed) || 999;
    if (key === "news2") return p.news2?.total_score ?? -1;
    if (key === "alerts") return p.conflict_count ?? 0;
    if (key === "admitted") return p.encounter?.admission_date || "";
    if (key === "los") return p.encounter?.length_of_stay ?? 0;
    return "";
  };

  patients.sort((a, b) => {
    const aVal = getVal(a, sortConfig.key);
    const bVal = getVal(b, sortConfig.key);
    if (aVal < bVal) return sortConfig.direction === "asc" ? -1 : 1;
    if (aVal > bVal) return sortConfig.direction === "asc" ? 1 : -1;
    return 0;
  });

  const requestSort = (key) => {
    let direction = "asc";
    if (sortConfig.key === key && sortConfig.direction === "asc") {
      direction = "desc";
    }
    setSortConfig({ key, direction });
  };

  const SortIcon = ({ col }) => {
    if (sortConfig.key !== col) return <span className="ml-1 opacity-20"></span>;
    return <span className="ml-1 text-clinical-info">{sortConfig.direction === "asc" ? "\u2191" : "\u2193"}</span>;
  };

  // Extract all conflicts for Ward Alerts
  const allConflicts = [];
  patients.forEach(p => {
    (p.conflicts || []).forEach(c => {
      if (!c.acknowledged) {
        allConflicts.push({ ...c, patientName: p.name, patientId: p.patient_id });
      }
    });
  });
  const highPriorityAlerts = allConflicts.filter(c => c.severity === "HIGH");

  return (
    <div>
      {/* Stats */}
      <div className="grid grid-cols-4 gap-5 mb-8">
        <StatCard label="Total Census" value={data.total_patients} />
        <StatCard label="High Acuity" value={data.high_risk_count} variant={data.high_risk_count > 0 ? "critical" : "default"} />
        <StatCard label="Active Alerts" value={data.active_conflicts} variant={data.active_conflicts > 0 ? "warning" : "default"} />
        <StatCard label="Discharge Ready" value={data.discharge_candidates} variant={data.discharge_candidates > 0 ? "success" : "default"} />
      </div>

      {/* Ward Alerts Section */}
      {highPriorityAlerts.length > 0 && (
        <div className="mb-8 bg-white rounded-xl border border-clinical-critical-border overflow-hidden">
          <div className="px-6 py-3 bg-clinical-critical-bg border-b border-clinical-critical-border flex items-center justify-between">
            <h3 className="text-xs font-bold text-clinical-critical uppercase tracking-wider">Critical Ward Alerts</h3>
            <span className="text-[10px] font-bold px-2 py-0.5 bg-clinical-critical text-white rounded-full">
              {highPriorityAlerts.length} URGENT
            </span>
          </div>
          <div className="divide-y divide-clinical-critical-border/30">
            {highPriorityAlerts.slice(0, 3).map((alert, i) => (
              <div key={i} className="px-6 py-3 flex items-center justify-between text-sm">
                <div className="flex items-center gap-3">
                  <span className="font-bold text-clinical-critical">HIGH</span>
                  <span className="text-text-secondary">
                    <strong className="text-text-primary">{alert.patientName}:</strong> {alert.message}
                  </span>
                </div>
                <Link href={`/dashboard/patient/${alert.patientId}`} className="text-xs font-bold text-clinical-info hover:underline">
                  Review Patient
                </Link>
              </div>
            ))}
            {highPriorityAlerts.length > 3 && (
              <div className="px-6 py-2 text-center bg-surface-secondary">
                <p className="text-[10px] text-text-tertiary uppercase font-bold">+{highPriorityAlerts.length - 3} more critical alerts</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Patient Census Table */}
      <div className="bg-white rounded-xl border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h3 className="text-sm font-bold text-text-primary uppercase tracking-wide">Patient Census</h3>
          <p className="text-[10px] text-text-tertiary">Click headers to sort</p>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border-light bg-surface-secondary">
              <th
                className="text-left px-6 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider w-12 cursor-pointer hover:text-text-primary"
                onClick={() => requestSort("priority_score")}
              >
                <SortIcon col="priority_score" />
              </th>
              <th
                className="text-left px-3 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => requestSort("bed")}
              >
                Bed <SortIcon col="bed" />
              </th>
              <th
                className="text-left px-3 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => requestSort("name")}
              >
                Patient <SortIcon col="name" />
              </th>
              <th className="text-left px-3 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider">Diagnosis</th>
              <th
                className="text-center px-3 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => requestSort("admitted")}
              >
                Admitted <SortIcon col="admitted" />
              </th>
              <th
                className="text-center px-3 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => requestSort("los")}
              >
                Day <SortIcon col="los" />
              </th>
              <th
                className="text-center px-3 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => requestSort("news2")}
              >
                NEWS2 <SortIcon col="news2" />
              </th>
              <th
                className="text-center px-3 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider cursor-pointer hover:text-text-primary"
                onClick={() => requestSort("alerts")}
              >
                Alerts <SortIcon col="alerts" />
              </th>
              <th className="text-left px-3 py-3 text-[11px] font-semibold text-text-tertiary uppercase tracking-wider">Discharge</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-light">
            {patients.map((p) => (
              <tr key={p.patient_id} className="hover:bg-surface-hover transition-colors group">
                <td className="px-6 py-3.5">
                  <PriorityDot level={p.priority} />
                </td>
                <td className="px-3 py-3.5 text-text-secondary font-medium tabular-nums">{p.encounter?.bed || "-"}</td>
                <td className="px-3 py-3.5">
                  <Link
                    href={`/dashboard/patient/${p.patient_id}`}
                    className="text-text-primary font-semibold hover:text-clinical-info transition-colors"
                  >
                    {p.name}
                  </Link>
                </td>
                <td className="px-3 py-3.5 text-text-secondary max-w-[180px] truncate">
                  {p.encounter?.admitting_diagnosis || "-"}
                </td>
                <td className="px-3 py-3.5 text-center text-text-secondary tabular-nums">
                  {p.encounter?.admission_date?.split("T")[0] || "-"}
                </td>
                <td className="px-3 py-3.5 text-center text-text-secondary tabular-nums">
                  {p.encounter?.length_of_stay || "-"}
                </td>
                <td className="px-3 py-3.5 text-center">
                  <NEWS2Badge score={p.news2?.total_score ?? "-"} level={p.news2?.risk_level} />
                </td>
                <td className="px-3 py-3.5 text-center">
                  {p.conflict_count > 0 ? (
                    <span className="inline-flex items-center gap-1 text-xs font-bold text-clinical-critical bg-clinical-critical-bg px-2 py-0.5 rounded-full">
                      {p.conflict_count}
                    </span>
                  ) : (
                    <span className="text-text-tertiary text-xs">--</span>
                  )}
                </td>
                <td className="px-3 py-3.5">
                  <DischargeBadge status={p.discharge?.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {patients.length === 0 && (
          <div className="px-6 py-12 text-center text-text-tertiary text-sm">
            No active inpatients. Run the seeder to populate ward data.
          </div>
        )}
      </div>
    </div>
  );
}

function DischargeBadge({ status }) {
  if (!status) return <span className="text-xs text-text-tertiary">--</span>;
  const styles = {
    Ready: "text-clinical-normal bg-clinical-normal-bg border-clinical-normal-border",
    "Requires Review": "text-clinical-warning bg-clinical-warning-bg border-clinical-warning-border",
    "Not Ready": "text-text-secondary bg-surface-secondary border-border",
  };
  return (
    <span className={`inline-block text-[11px] font-semibold px-2 py-0.5 rounded border ${styles[status] || styles["Not Ready"]}`}>
      {status}
    </span>
  );
}
