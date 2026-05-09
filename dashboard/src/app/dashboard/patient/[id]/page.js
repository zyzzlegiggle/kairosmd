"use client";
import { useState, useEffect, use } from "react";
import Link from "next/link";
import { callMCPTool, clearMCPCache } from "@/lib/mcp";

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
      <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">{title}</h3>
      {children}
    </div>
  );
}

function ActionButton({ label, onClick, variant = "default", disabled = false }) {
  const styles = {
    default: "border border-gray-300 text-gray-700 hover:bg-gray-50",
    danger: "border border-red-300 text-red-700 hover:bg-red-50",
    success: "border border-green-300 text-green-700 hover:bg-green-50",
    primary: "bg-blue-600 text-white hover:bg-blue-700 border border-blue-600",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`text-xs px-3 py-1.5 rounded font-medium transition-colors ${styles[variant]} ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
    >
      {label}
    </button>
  );
}

export default function PatientDetailPage({ params }) {
  const { id } = use(params);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionNote, setActionNote] = useState("");
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [actionFeedback, setActionFeedback] = useState("");

  useEffect(() => {
    callMCPTool("get_patient_ward_detail", { patient_id: id })
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  async function handleAction(actionType, detail = "", conflictId = "") {
    try {
      await callMCPTool("record_ward_action", {
        patient_id: id,
        action_type: actionType,
        detail: detail,
        conflict_id: conflictId,
      });
      setActionFeedback(`Action recorded: ${actionType.replace(/_/g, " ")}`);
      clearMCPCache();
      // Refresh patient data
      const fresh = await callMCPTool("get_patient_ward_detail", { patient_id: id });
      setData(fresh);
      setTimeout(() => setActionFeedback(""), 3000);
    } catch (e) {
      setActionFeedback("Failed to record action");
    }
  }

  if (loading) return <p className="text-gray-500 p-4">Loading patient data...</p>;
  if (!data) return <p className="text-red-600 p-4">Patient not found.</p>;

  const briefing = data.llm_briefing || {};
  const news2 = data.news2 || {};
  const enc = data.encounter || {};

  return (
    <div className="max-w-4xl">
      <Link href="/dashboard" className="text-sm text-blue-600 hover:underline mb-4 inline-block">&larr; Back to Ward</Link>

      {/* Action Feedback */}
      {actionFeedback && (
        <div className="bg-green-50 border border-green-200 text-green-800 text-sm px-4 py-2 rounded mb-4">
          {actionFeedback}
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold">{data.name}</h2>
          <p className="text-sm text-gray-500">
            {data.gender} &middot; DOB: {data.birthDate} &middot; {enc.ward} &middot; {enc.bed}
          </p>
          <p className="text-sm text-gray-500">
            Admitted: {enc.admission_date?.slice(0, 10)} &middot; Day {enc.length_of_stay} &middot; {enc.admitting_diagnosis}
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <Badge color={news2.risk_level === "HIGH" ? "red" : news2.risk_level === "MEDIUM" ? "amber" : "green"}>
            NEWS2: {news2.total_score} — {news2.risk_level}
          </Badge>
          {data.escalation_status && (
            <Badge color="red">
              {data.escalation_status === "escalation_requested" ? "ESCALATION REQUESTED" : "URGENT REVIEW FLAGGED"}
            </Badge>
          )}
        </div>
      </div>

      {/* Quick Actions Bar */}
      <div className="border border-gray-200 rounded-lg p-3 mb-4 flex flex-wrap gap-2 items-center">
        <span className="text-xs text-gray-500 font-medium uppercase mr-2">Actions:</span>
        <ActionButton label="Flag Urgent Review" variant="danger" onClick={() => handleAction("urgent_review_flagged", "Flagged for immediate bedside review")} />
        <ActionButton label="Request Escalation" variant="danger" onClick={() => handleAction("escalation_requested", "Escalation to senior / ICU requested")} />
        <ActionButton label="Pharmacy Review" variant="default" onClick={() => handleAction("pharmacy_review_flagged", "Flagged for pharmacist review")} />
        <ActionButton
          label={data.discharge_override === "discharge_approved" ? "Discharge Approved ✓" : "Approve Discharge"}
          variant="success"
          onClick={() => handleAction("discharge_approved", "Cleared for discharge")}
          disabled={data.discharge_override === "discharge_approved"}
        />
        <ActionButton
          label={data.discharge_override === "discharge_blocked" ? "Discharge Blocked ✓" : "Block Discharge"}
          variant="danger"
          onClick={() => handleAction("discharge_blocked", "Discharge blocked — see clinical note")}
          disabled={data.discharge_override === "discharge_blocked"}
        />
        <button
          onClick={() => setShowNoteInput(!showNoteInput)}
          className="text-xs px-3 py-1.5 rounded font-medium border border-blue-300 text-blue-700 hover:bg-blue-50 cursor-pointer"
        >
          + Clinical Note
        </button>
      </div>

      {/* Clinical Note Input */}
      {showNoteInput && (
        <div className="border border-gray-200 rounded-lg p-3 mb-4">
          <textarea
            value={actionNote}
            onChange={(e) => setActionNote(e.target.value)}
            placeholder="Enter clinical response note..."
            className="w-full border border-gray-300 rounded p-2 text-sm mb-2 h-20 resize-none"
          />
          <div className="flex gap-2">
            <ActionButton
              label="Save Note"
              variant="primary"
              onClick={() => {
                if (actionNote.trim()) {
                  handleAction("clinical_note_added", actionNote.trim());
                  setActionNote("");
                  setShowNoteInput(false);
                }
              }}
            />
            <ActionButton label="Cancel" onClick={() => { setShowNoteInput(false); setActionNote(""); }} />
          </div>
        </div>
      )}

      {/* Overnight Summary */}
      <Section title="Overnight Summary">
        <p className="text-sm text-gray-700 leading-relaxed">{briefing.overnight_summary || "Not available"}</p>
      </Section>

      {/* Conflicts with individual acknowledge */}
      {data.conflicts?.length > 0 && (
        <Section title={`Conflicts (${data.conflict_count})`}>
          {data.conflicts.map((c, i) => (
            <div key={i} className={`rounded p-3 mb-2 text-sm border ${c.acknowledged ? "bg-gray-50 border-gray-200" : "bg-red-50 border-red-200"}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className={`font-medium ${c.acknowledged ? "text-gray-500" : "text-red-700"}`}>
                    [{c.severity}]
                  </span>{" "}
                  <span className={c.acknowledged ? "text-gray-500 line-through" : "text-red-900"}>
                    {c.message}
                  </span>
                </div>
                {c.acknowledged ? (
                  <span className="text-xs text-green-600 font-medium whitespace-nowrap">Reviewed ✓</span>
                ) : (
                  <ActionButton
                    label="Acknowledge"
                    variant="default"
                    onClick={() => handleAction("conflict_acknowledged", `Conflict reviewed: ${c.message?.slice(0, 80)}`, c.conflict_id)}
                  />
                )}
              </div>
            </div>
          ))}
        </Section>
      )}

      {/* Ward Round Talking Points */}
      <Section title="Talking Points">
        <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
          {(briefing.ward_round_talking_points || []).map((pt, i) => (
            <li key={i}>{pt}</li>
          ))}
        </ul>
      </Section>

      {/* Vital Trends */}
      {data.vital_trends?.length > 0 && (
        <Section title="Vital Trends (24h)">
          <table className="w-full text-sm">
            <thead className="text-xs text-gray-500 uppercase">
              <tr><th className="text-left py-1">Parameter</th><th>Previous</th><th>Latest</th><th>Trend</th></tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.vital_trends.map((t, i) => (
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
      )}

      {/* Discharge Readiness */}
      <Section title="Discharge Readiness">
        <div className="flex items-center gap-2 mb-3">
          <Badge color={data.discharge?.status === "Ready" ? "green" : data.discharge?.status === "Requires Review" ? "amber" : "red"}>
            {data.discharge?.summary || data.discharge?.status}
          </Badge>
          {data.discharge_override && (
            <Badge color={data.discharge_override === "discharge_approved" ? "green" : "red"}>
              Doctor override: {data.discharge_override.replace(/_/g, " ")}
            </Badge>
          )}
        </div>
        <div className="space-y-1">
          {(data.discharge?.checklist || []).map((c, i) => (
            <div key={i} className="flex items-center gap-2 text-sm">
              <span className={c.met ? "text-green-600" : "text-red-600"}>{c.met ? "✓" : "✗"}</span>
              <span className={c.met ? "text-gray-600" : "text-red-600"}>{c.item}: {c.detail}</span>
            </div>
          ))}
        </div>
      </Section>

      {/* Suggested Plan */}
      <Section title="Suggested Plan Adjustments">
        <p className="text-sm text-gray-700">{briefing.suggested_plan_adjustments || "Not available"}</p>
      </Section>

      {/* Clinical Activity Timeline */}
      <Section title="Clinical Activity Timeline">
        {data.actions?.length > 0 ? (
          <div className="relative border-l-2 border-gray-200 ml-3 space-y-6 pb-4">
            {[...data.actions].reverse().map((a, i) => {
              const isEscalation = a.action_type.includes("urgent") || a.action_type.includes("escalation");
              const isDischarge = a.action_type.includes("discharge");
              const isNote = a.action_type === "clinical_note_added";
              
              return (
                <div key={i} className="relative pl-6">
                  {/* Timeline dot */}
                  <div className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 border-white shadow-sm ${
                    isEscalation ? "bg-red-500" : isDischarge ? "bg-blue-500" : isNote ? "bg-amber-500" : "bg-gray-400"
                  }`} />
                  
                  <div className="bg-white border border-gray-100 rounded-md p-3 shadow-sm">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-bold text-gray-900 uppercase">
                        {a.action_type.replace(/_/g, " ")}
                      </span>
                      <span className="text-[10px] font-medium text-gray-400 tabular-nums">
                        {new Date(a.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                      </span>
                    </div>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {a.detail || "No additional detail provided."}
                    </p>
                    <div className="mt-2 pt-2 border-t border-gray-50 flex items-center gap-1.5">
                      <div className="w-4 h-4 rounded-full bg-blue-100 flex items-center justify-center text-[8px] font-bold text-blue-600">
                        {a.clinician?.charAt(0)}
                      </div>
                      <span className="text-[10px] font-medium text-gray-500">
                        {a.clinician} &middot; Consultant
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-sm text-gray-400 italic">No activity recorded for this session.</p>
        )}
      </Section>

      {/* Clinical Notes */}
      {data.clinical_notes?.length > 0 && (
        <Section title="Clinical Notes">
          {data.clinical_notes.map((n, i) => (
            <div key={i} className="mb-3 border-l-2 border-gray-300 pl-3">
              <p className="text-xs text-gray-400">{n.type} — {n.date?.slice(0, 16)}</p>
              <p className="text-sm text-gray-700 mt-1">{n.text?.slice(0, 500)}</p>
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}
