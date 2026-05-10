"use client";
import { useState, useEffect, use } from "react";
import Link from "next/link";
import { callMCPTool, invalidatePatientCache } from "@/lib/mcp";
import dynamic from "next/dynamic";

const VitalChart = dynamic(() => import("@/components/VitalChart"), { ssr: false });

/* ---------- Shared UI Components ---------- */

function Card({ title, children, className = "", headerRight = null }) {
  return (
    <div className={`bg-white rounded-xl border border-border ${className}`}>
      {title && (
        <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
          <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider">{title}</h3>
          {headerRight}
        </div>
      )}
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

function Badge({ children, variant = "default" }) {
  const styles = {
    critical: "bg-clinical-critical text-white",
    warning: "bg-clinical-warning-bg text-clinical-warning border border-clinical-warning-border",
    success: "bg-clinical-normal-bg text-clinical-normal border border-clinical-normal-border",
    info: "bg-clinical-info-bg text-clinical-info border border-clinical-info-border",
    default: "bg-surface-secondary text-text-secondary border border-border",
  };
  return (
    <span className={`inline-block text-[11px] font-semibold px-2.5 py-1 rounded-md ${styles[variant]}`}>
      {children}
    </span>
  );
}

function ActionButton({ label, onClick, variant = "default", disabled = false }) {
  const styles = {
    default: "border-border text-text-secondary hover:bg-surface-hover",
    danger: "border-clinical-critical-border text-clinical-critical hover:bg-clinical-critical-bg",
    success: "border-clinical-normal-border text-clinical-normal hover:bg-clinical-normal-bg",
    primary: "bg-clinical-info text-white hover:bg-blue-700 border-clinical-info",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`text-xs font-semibold px-3.5 py-2 rounded-lg border transition-colors cursor-pointer ${styles[variant]} ${disabled ? "opacity-40 cursor-not-allowed" : ""}`}
    >
      {label}
    </button>
  );
}

function Toast({ message, onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3000);
    return () => clearTimeout(t);
  }, [onClose]);
  return (
    <div className="fixed bottom-6 right-6 z-50 toast-enter bg-text-primary text-white text-sm font-medium px-5 py-3 rounded-xl shadow-lg flex items-center gap-3">
      <span>{message}</span>
      <button onClick={onClose} className="text-white/60 hover:text-white text-xs cursor-pointer">Dismiss</button>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-5">
      <div className="skeleton h-28 rounded-xl" />
      <div className="grid grid-cols-3 gap-5">
        <div className="skeleton h-64 rounded-xl col-span-2" />
        <div className="skeleton h-64 rounded-xl" />
      </div>
    </div>
  );
}

function DrugWarningItem({ warning }) {
  const [expanded, setExpanded] = useState(false);
  const w = warning;
  
  return (
    <div className="text-sm border border-clinical-warning-border bg-clinical-warning-bg rounded-lg px-3 py-2.5 transition-all">
      <p className="font-semibold text-clinical-warning">{w.drug}</p>
      {w.boxed_warning && <p className="text-[11px] text-clinical-critical font-bold mt-1 uppercase tracking-tight">Boxed Warning</p>}
      {w.interaction_warnings && (
        <div className="mt-1">
          <p className={`text-xs text-text-secondary leading-relaxed ${expanded ? "" : "line-clamp-2"}`}>
            {w.interaction_warnings}
          </p>
          {w.interaction_warnings.length > 100 && (
            <button 
              onClick={() => setExpanded(!expanded)}
              className="text-[10px] font-bold text-clinical-info mt-1 hover:underline cursor-pointer uppercase tracking-wider"
            >
              {expanded ? "Show Less" : "Read Full Warning"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}

/* ---------- Page ---------- */

export default function PatientDetailPage({ params }) {
  const { id } = use(params);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState("");
  const [noteInput, setNoteInput] = useState("");
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchData = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    else setRefreshing(true);
    
    try {
      const result = await callMCPTool("get_patient_ward_detail", { patient_id: id });
      setData(result);
    } catch (e) {
      setToast("Failed to refresh clinical data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => { fetchData(true); }, [id]);

  const handleAction = async (actionType, detail = "", conflictId = "") => {
    setActionLoading(true);
    try {
      await callMCPTool("record_ward_action", {
        patient_id: id,
        action_type: actionType,
        detail,
        conflict_id: conflictId,
        clinician: "Dr. Mike",
      });
      invalidatePatientCache(id);
      setToast(`Action recorded: ${actionType.replace(/_/g, " ")}`);
      fetchData(false);
    } catch (e) {
      setToast(`Error: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <LoadingSkeleton />;
  if (!data) return <p className="text-text-tertiary text-sm">Patient not found.</p>;

  const briefing = data.llm_briefing || {};
  const news2 = data.news2 || {};
  const encounter = data.encounter || {};
  const discharge = data.discharge || {};

  const news2Variant = news2.risk_level === "HIGH" ? "critical" : news2.risk_level === "MEDIUM" ? "warning" : "success";

  return (
    <div>
      {/* Back link */}
      <Link href="/dashboard" className="text-xs text-text-tertiary hover:text-text-secondary transition-colors mb-4 inline-block">
        Ward Board
      </Link>

      {/* Header */}
      <div className="bg-white rounded-xl border border-border p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h2 className="text-xl font-bold text-text-primary">{data.name}</h2>
              <Badge variant={news2Variant}>NEWS2: {news2.total_score ?? "--"} ({news2.risk_level || "--"})</Badge>
            </div>
            <div className="flex items-center gap-4 text-xs text-text-tertiary mt-2">
              <span><strong className="text-text-secondary">Bed</strong> {encounter.bed || "--"}</span>
              <span className="text-border">|</span>
              <span><strong className="text-text-secondary">Diagnosis</strong> {encounter.admitting_diagnosis || "--"}</span>
              <span className="text-border">|</span>
              <span><strong className="text-text-secondary">Day</strong> {encounter.length_of_stay || "--"}</span>
              <span className="text-border">|</span>
              <span><strong className="text-text-secondary">DOB</strong> {data.birthDate || "--"}</span>
              <span className="text-border">|</span>
              <span><strong className="text-text-secondary">Sex</strong> {data.gender || "--"}</span>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-3">
            {refreshing && (
              <div className="flex items-center gap-2 text-[10px] font-bold text-clinical-info uppercase tracking-widest animate-pulse mr-2">
                <span className="w-2 h-2 rounded-full bg-clinical-info"></span>
                Refreshing...
              </div>
            )}
            <div className="flex gap-2">
              <ActionButton label="Add Note" variant="primary" onClick={() => setShowNoteForm(!showNoteForm)} />
              <ActionButton label="Escalate" variant="danger" onClick={() => handleAction("escalation_requested", "Consultant-initiated escalation")} disabled={actionLoading} />
              <ActionButton label="Flag for Pharmacy" variant="warning" onClick={() => handleAction("pharmacy_review_flagged", "Medication review required")} disabled={actionLoading} />
            </div>
          </div>
        </div>

        {/* Note form */}
        {showNoteForm && (
          <div className="mt-4 pt-4 border-t border-border">
            <textarea
              value={noteInput}
              onChange={(e) => setNoteInput(e.target.value)}
              placeholder="Enter clinical note..."
              className="w-full border border-border rounded-lg p-3 text-sm h-20 resize-none focus:outline-none focus:ring-2 focus:ring-clinical-info/30 focus:border-clinical-info"
            />
            <div className="flex gap-2 mt-2">
              <ActionButton
                label="Save Note"
                variant="primary"
                onClick={() => {
                  if (noteInput.trim()) {
                    handleAction("clinical_note_added", noteInput.trim());
                    setNoteInput("");
                    setShowNoteForm(false);
                  }
                }}
                disabled={actionLoading}
              />
              <ActionButton label="Cancel" onClick={() => { setShowNoteForm(false); setNoteInput(""); }} />
            </div>
          </div>
        )}
      </div>

      {/* Two column layout */}
      <div className="grid grid-cols-3 gap-6 mb-6">
        {/* Left - 2 cols */}
        <div className="col-span-2 space-y-6">
          {/* Observations (Vital Trends) */}
          {data.vital_trends?.length > 0 && (
            <Card title="Observations (24h Trend)">
              <VitalChart trends={data.vital_trends} />
            </Card>
          )}

          {/* Laboratory Results */}
          {data.lab_trends?.length > 0 && (
            <Card title="Laboratory Results">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border-light">
                    <th className="text-left py-2 text-[11px] font-semibold text-text-tertiary uppercase">Parameter</th>
                    <th className="text-center py-2 text-[11px] font-semibold text-text-tertiary uppercase">Previous</th>
                    <th className="text-center py-2 text-[11px] font-semibold text-text-tertiary uppercase">Latest</th>
                    <th className="text-center py-2 text-[11px] font-semibold text-text-tertiary uppercase">Trend</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-light">
                  {data.lab_trends.map((t, i) => (
                    <tr key={i}>
                      <td className="py-2.5 font-medium text-text-primary">{t.parameter || t.loinc}</td>
                      <td className="py-2.5 text-center text-text-secondary">{t.oldest}</td>
                      <td className="py-2.5 text-center font-semibold text-text-primary">{t.newest}</td>
                      <td className="py-2.5 text-center">
                        <TrendIndicator direction={t.direction} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          )}

          {/* Brief Summary */}
          <Card title="Brief Summary">
            <p className="text-sm text-text-secondary leading-relaxed">
              {briefing.overnight_summary || "Summary not available. Review chart directly."}
            </p>
          </Card>

          {/* Ward Round Key Points */}
          <Card title="Ward Round Key Points">
            <ul className="space-y-2">
              {(briefing.ward_round_talking_points || []).map((pt, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                  <span className="text-text-tertiary mt-0.5 font-bold">-</span>
                  <span>{pt}</span>
                </li>
              ))}
              {(!briefing.ward_round_talking_points || briefing.ward_round_talking_points.length === 0) && (
                <li className="text-sm text-text-tertiary">No key points available.</li>
              )}
            </ul>
          </Card>

          {/* Active Alerts */}
          {data.conflict_count > 0 && (
            <Card
              title={`Active Alerts (${data.conflict_count})`}
              headerRight={<Badge variant="critical">{data.conflict_count} unresolved</Badge>}
            >
              <div className="space-y-3">
                {data.conflicts.map((c, i) => {
                  const isAck = c.acknowledged;
                  return (
                    <div
                      key={i}
                      className={`rounded-lg p-4 border text-sm ${isAck ? "bg-surface-secondary border-border" : "bg-clinical-critical-bg border-clinical-critical-border"}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <span className={`text-[11px] font-bold uppercase tracking-wider ${isAck ? "text-text-tertiary" : "text-clinical-critical"}`}>
                            {c.severity}
                          </span>
                          <p className={`mt-1 ${isAck ? "text-text-tertiary line-through" : "text-text-primary font-medium"}`}>
                            {c.message}
                          </p>
                        </div>
                        {isAck ? (
                          <Badge variant="success">Reviewed</Badge>
                        ) : (
                          <ActionButton
                            label="Acknowledge"
                            variant="danger"
                            onClick={() => handleAction("conflict_acknowledged", `Reviewed: ${c.message?.slice(0, 80)}`, c.conflict_id)}
                            disabled={actionLoading}
                          />
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          )}
        </div>


        {/* Right sidebar - 1 col */}
        <div className="space-y-6">
          {/* Discharge Readiness */}
          <Card title="Discharge Readiness">
            <div className="mb-3">
              <Badge variant={discharge.status === "Ready" ? "success" : discharge.status === "Requires Review" ? "warning" : "default"}>
                {discharge.summary || discharge.status || "--"}
              </Badge>
              {data.discharge_override && (
                <Badge variant={data.discharge_override === "discharge_approved" ? "success" : "critical"}>
                  Override: {data.discharge_override.replace(/_/g, " ")}
                </Badge>
              )}
            </div>
            <div className="space-y-2">
              {(discharge.checklist || []).map((c, i) => (
                <div key={i} className="flex items-center gap-2.5 text-sm">
                  <span className={`text-xs font-bold ${c.met ? "text-clinical-normal" : "text-clinical-critical"}`}>
                    {c.met ? "\u2713" : "\u2717"}
                  </span>
                  <span className={c.met ? "text-text-secondary" : "text-clinical-critical font-medium"}>
                    {c.item}
                  </span>
                </div>
              ))}
            </div>
            <div className="flex gap-2 mt-4 pt-3 border-t border-border">
              <ActionButton
                label="Approve Discharge"
                variant="success"
                onClick={() => handleAction("discharge_approved", "Clinically safe for discharge")}
                disabled={actionLoading}
              />
              <ActionButton
                label="Block"
                variant="danger"
                onClick={() => handleAction("discharge_blocked", "Discharge not safe at this time")}
                disabled={actionLoading}
              />
            </div>
          </Card>

          {/* Active Conditions */}
          {data.active_conditions?.length > 0 && (
            <Card title="Active Conditions">
              <div className="space-y-1.5">
                {data.active_conditions.map((c, i) => (
                  <div key={i} className="text-sm text-text-secondary bg-surface-secondary rounded-lg px-3 py-2">
                    {c}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Safety Flags */}
          {data.safety_flags?.length > 0 && (
            <Card title="Safety Flags">
              <div className="space-y-1.5">
                {data.safety_flags.map((f, i) => (
                  <div key={i} className="text-sm font-medium text-clinical-critical bg-clinical-critical-bg rounded-lg px-3 py-2 border border-clinical-critical-border">
                    {f}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* FDA Drug Safety */}
          {data.fda_safety?.drug_warnings?.length > 0 && (
            <Card title="FDA Drug Warnings">
              <div className="space-y-2">
                {data.fda_safety.drug_warnings.map((w, i) => (
                  <DrugWarningItem key={i} warning={w} />
                ))}
              </div>
            </Card>
          )}

          {/* Proposed Plan */}
          <Card title="Proposed Plan Adjustments">
            <p className="text-sm text-text-secondary leading-relaxed">
              {briefing.suggested_plan_adjustments || "No plan adjustments suggested."}
            </p>
          </Card>
        </div>
      </div>

      {/* Full width bottom sections */}
      <div className="grid grid-cols-2 gap-6">
        {/* Clinical Notes */}
        <Card title="Clinical Notes">
          {data.clinical_notes?.length > 0 ? (
            <div className="space-y-4">
              {data.clinical_notes.map((n, i) => (
                <div key={i} className="border-l-3 border-clinical-info pl-4">
                  <div className="flex items-center justify-between">
                    <p className="text-[11px] font-bold text-text-primary uppercase">
                      {n.type}
                    </p>
                    <p className="text-[10px] font-medium text-text-tertiary">
                      {n.date?.slice(0, 16)?.replace("T", " ")}
                    </p>
                  </div>
                  <p className="text-[10px] font-semibold text-clinical-info mt-0.5">
                    {n.author}
                  </p>
                  <p className="text-sm text-text-secondary mt-1.5 leading-relaxed">{n.text?.slice(0, 500)}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-text-tertiary">No clinical notes available.</p>
          )}
        </Card>

        {/* Activity Log */}
        <Card title="Activity Log">
          {data.actions?.length > 0 ? (
            <div className="space-y-3">
              {[...data.actions].reverse().map((a, i) => {
                const typeColor =
                  a.action_type.includes("urgent") || a.action_type.includes("escalation")
                    ? "border-clinical-critical"
                    : a.action_type.includes("discharge")
                    ? "border-clinical-info"
                    : "border-clinical-warning";
                return (
                  <div key={i} className={`border-l-3 ${typeColor} pl-4`}>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold text-text-primary uppercase">
                        {a.action_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-[10px] text-text-tertiary tabular-nums">
                        {new Date(a.timestamp).toLocaleString([], { dateStyle: "short", timeStyle: "short" })}
                      </span>
                    </div>
                    <p className="text-sm text-text-secondary mt-0.5">{a.detail || "No detail provided."}</p>
                    <p className="text-[10px] text-text-tertiary mt-1">{a.clinician}</p>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-text-tertiary">No activity recorded for this session.</p>
          )}
        </Card>
      </div>

      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </div>
  );
}

function TrendIndicator({ direction }) {
  if (direction === "increasing") return <span className="text-clinical-critical font-bold">{"\u2191"}</span>;
  if (direction === "decreasing") return <span className="text-clinical-info font-bold">{"\u2193"}</span>;
  return <span className="text-text-tertiary">{"\u2192"}</span>;
}
