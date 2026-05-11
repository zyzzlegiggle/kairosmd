"use client";
import { useState, useEffect, use } from "react";
import Link from "next/link";
import { callMCPTool, invalidatePatientCache } from "../../../../shared/mcp.js";
import dynamic from "next/dynamic";

const VitalChart = dynamic(() => import("@/components/VitalChart"), { ssr: false });

/* ── Tiny helpers ─────────────────────────────────────────────── */

function Card({ title, children, className = "", accent = "", headerRight = null, footer = null }) {
  return (
    <div className={`bg-white rounded-xl border border-border ${className}`}>
      {title && (
        <div className={`px-5 py-3 border-b border-border flex items-center justify-between ${accent}`}>
          <h3 className="text-[11px] font-bold text-text-primary uppercase tracking-wider">{title}</h3>
          {headerRight}
        </div>
      )}
      <div className="px-5 py-4">{children}</div>
      {footer && <div className="px-5 pb-3">{footer}</div>}
    </div>
  );
}

function Badge({ children, variant = "default" }) {
  const s = {
    critical: "bg-clinical-critical/10 text-clinical-critical border border-clinical-critical/20",
    warning: "bg-clinical-warning-bg text-clinical-warning border border-clinical-warning-border",
    success: "bg-clinical-normal-bg text-clinical-normal border border-clinical-normal-border",
    info: "bg-clinical-info-bg text-clinical-info border border-clinical-info-border",
    default: "bg-surface-secondary text-text-secondary border border-border",
  };
  return <span className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-md ${s[variant]}`}>{children}</span>;
}

function Toast({ message, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 3000); return () => clearTimeout(t); }, [onClose]);
  return (
    <div className="fixed bottom-6 right-6 z-50 toast-enter bg-text-primary text-white text-sm font-medium px-5 py-3 rounded-xl shadow-lg flex items-center gap-3">
      <span>{message}</span>
      <button onClick={onClose} className="text-white/60 hover:text-white text-xs cursor-pointer">×</button>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="skeleton h-24 rounded-xl" />
      <div className="grid grid-cols-3 gap-4">
        <div className="skeleton h-56 rounded-xl col-span-2" />
        <div className="skeleton h-56 rounded-xl" />
      </div>
    </div>
  );
}

function TrendIndicator({ direction }) {
  if (direction === "increasing") return <span className="text-clinical-critical font-bold">{"\u2191"}</span>;
  if (direction === "decreasing") return <span className="text-clinical-info font-bold">{"\u2193"}</span>;
  return <span className="text-text-tertiary">{"\u2192"}</span>;
}

/* ── Page ─────────────────────────────────────────────────────── */

export default function PatientDetailPage({ params }) {
  const { id } = use(params);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState("Synchronizing FHIR Clinical Record...");
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState("");
  const [noteInput, setNoteInput] = useState("");
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [wardList, setWardList] = useState([]);

  // Load ward list for bed-to-bed nav
  useEffect(() => {
    callMCPTool("get_ward_round_summary")
      .then((res) => {
        const sorted = (res.patients || []).sort((a, b) => {
          return (parseInt(a.encounter?.bed) || 999) - (parseInt(b.encounter?.bed) || 999);
        });
        setWardList(sorted);
      })
      .catch(() => { });
  }, []);

  const currentIdx = wardList.findIndex(p => p.patient_id === id);
  const prevPatient = currentIdx > 0 ? wardList[currentIdx - 1] : null;
  const nextPatient = currentIdx < wardList.length - 1 ? wardList[currentIdx + 1] : null;

  // Keyboard nav: J = next, K = prev
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === "TEXTAREA" || e.target.tagName === "INPUT") return;
      if (e.key === "j" && nextPatient) window.location.href = `/dashboard/patient/${nextPatient.patient_id}`;
      if (e.key === "k" && prevPatient) window.location.href = `/dashboard/patient/${prevPatient.patient_id}`;
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [prevPatient, nextPatient]);

  const fetchData = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    else setRefreshing(true);
    setSyncMessage("Synchronizing FHIR Clinical Record...");
    setSyncing(true);
    try {
      const result = await callMCPTool("get_patient_ward_detail", { patient_id: id });
      setData(result);
    } catch (e) {
      setToast("Failed to load patient data");
    } finally {
      setLoading(false);
      setRefreshing(false);
      setSyncing(false);
    }
  };

  useEffect(() => { fetchData(true); }, [id]);

  const act = async (type, detail = "", conflictId = "") => {
    setSyncMessage("Propagating Entry to FHIR Server...");
    setSyncing(true);
    setActionLoading(true);
    const clinician = (typeof window !== 'undefined' ? localStorage.getItem("clinician_name") : "Dr. Mike") || "Dr. Mike";
    try {
      await callMCPTool("record_ward_action", {
        patient_id: id, action_type: type, detail,
        conflict_id: conflictId, clinician: clinician,
      });
      invalidatePatientCache(id);
      setToast(`Recorded: ${type.replace(/_/g, " ")}`);
      fetchData(false);
    } catch (e) {
      setToast(`Error: ${e.message}`);
    } finally {
      setActionLoading(false);
      setSyncing(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background relative overflow-hidden">
        {/* Technical Syncing Pill */}
        <div className="fixed top-12 left-1/2 -translate-x-1/2 z-[100] animate-bounce">
          <div className="bg-clinical-info text-white px-6 py-3 rounded-full shadow-[0_20px_50px_rgba(37,99,235,0.4)] flex items-center gap-4 border border-white/20 backdrop-blur-md bg-blue-600/90">
            <div className="flex gap-1">
              <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
              <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse delay-75" />
              <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse delay-150" />
            </div>
            <span className="text-xs font-black uppercase tracking-[0.2em]">Synchronizing FHIR Clinical Engine</span>
          </div>
        </div>
        
        <div className="flex flex-col items-center gap-6 opacity-20">
          <div className="w-24 h-24 border-8 border-clinical-info border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    );
  }
  if (!data) return <p className="text-text-tertiary text-sm p-8">Patient not found.</p>;

  const briefing = data.llm_briefing || {};
  const news2 = data.news2 || {};
  const enc = data.encounter || {};
  const discharge = data.discharge || {};

  // ── DEDUPLICATION LOGIC ──
  // 1. Conflicts
  const rawAlerts = data.conflicts || [];
  const alerts = [...new Map(rawAlerts.map(a => [a.message, a])).values()];

  // 2. Safety Flags
  const rawFlags = data.safety_flags || [];
  const flags = [...new Set(rawFlags)];

  // 3. Clinical Notes
  const rawNotes = data.clinical_notes || [];
  const clinicalNotes = [...new Map(rawNotes.map(n => [`${n.date}-${n.text.slice(0, 50)}`, n])).values()];

  // 4. Medications
  const rawMeds = data.active_medications || [];
  const activeMeds = [...new Map(rawMeds.map(m => [m.name, m])).values()];

  // 5. Allergies
  const uniqueAllergies = [...new Map((data.allergies || []).map(a => [a.name, a])).values()];

  const hasAlerts = alerts.length > 0 || flags.length > 0;

  const riskColor = news2.risk_level === "HIGH" ? "critical" : news2.risk_level === "MEDIUM" ? "warning" : "success";

  return (
    <div className="space-y-5 relative">
      {/* Background Syncing Pill */}
      <div className={`fixed top-6 left-[calc(50%+120px)] -translate-x-1/2 z-[100] transition-all duration-500 ease-in-out ${syncing ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-4 pointer-events-none"}`}>
        <div className="bg-clinical-info text-white px-6 py-2 rounded-full shadow-[0_20px_50px_rgba(37,99,235,0.4)] flex items-center gap-3 border border-white/20 backdrop-blur-md bg-blue-600/90">
          <div className="flex gap-1">
            <div className="w-1.5 h-1.5 bg-white rounded-full animate-bounce" />
            <div className="w-1.5 h-1.5 bg-white rounded-full animate-bounce delay-100" />
            <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse delay-200" />
          </div>
          <span className="text-[10px] font-black uppercase tracking-widest text-white/90">{syncMessage}</span>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════
          HEADER — Patient identity + quick actions
         ══════════════════════════════════════════════════════════ */}
      <div className="bg-white rounded-xl border border-border p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h2 className="text-2xl font-black text-text-primary tracking-tight">{data.name}</h2>
            <div className="flex items-center gap-3 mt-4">
              {/* NEWS2 Score Card */}
              <div className={`p-3 rounded-2xl border-2 flex flex-col items-center min-w-[90px] shadow-sm ${news2.risk_level === 'HIGH' ? 'bg-clinical-critical-bg border-clinical-critical text-clinical-critical' : news2.risk_level === 'MEDIUM' ? 'bg-clinical-warning-bg border-clinical-warning text-clinical-warning' : 'bg-clinical-normal-bg border-clinical-normal text-clinical-normal'}`}>
                <span className="text-[9px] font-black uppercase tracking-widest mb-1 opacity-60">NEWS2</span>
                <span className="text-2xl font-black leading-none">{news2.total_score ?? "--"}</span>
              </div>

              {/* Active Conflicts Card */}
              <div className={`p-3 rounded-2xl border-2 flex flex-col items-center min-w-[90px] shadow-sm ${alerts.filter(a => !a.acknowledged).length > 0 ? 'bg-clinical-critical-bg border-clinical-critical text-clinical-critical' : 'bg-surface-secondary border-border text-text-tertiary'}`}>
                <span className="text-[9px] font-black uppercase tracking-widest mb-1 opacity-60">Conflicts</span>
                <span className="text-2xl font-black leading-none">{alerts.filter(a => !a.acknowledged).length}</span>
              </div>

              {/* Allergies Summary Card */}
              <div className={`p-3 rounded-2xl border-2 flex flex-col min-w-[140px] shadow-sm ${uniqueAllergies.some(a => a.criticality === 'high') ? 'bg-clinical-critical-bg border-clinical-critical text-clinical-critical' : 'bg-surface-secondary border-border text-text-secondary'}`}>
                <span className="text-[9px] font-black uppercase tracking-widest mb-1 opacity-60 text-center">Allergies</span>
                <div className="flex flex-wrap justify-center gap-1.5 mt-0.5">
                  {uniqueAllergies.length > 0 ? uniqueAllergies.map((a, i) => (
                    <span key={i} className={`text-[10px] font-bold uppercase ${a.criticality === 'high' ? 'text-clinical-critical' : 'text-text-primary'}`}>
                      {a.name}{i < uniqueAllergies.length - 1 ? "," : ""}
                    </span>
                  )) : <span className="text-[10px] font-bold uppercase italic opacity-40">None recorded</span>}
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {refreshing && (
              <span className="text-[10px] font-bold text-clinical-info uppercase animate-pulse mr-1">Syncing…</span>
            )}
            <button onClick={() => setShowNoteForm(!showNoteForm)} className="text-xs font-bold px-4 py-2 rounded-xl bg-clinical-info text-white hover:bg-blue-700 shadow-sm transition-all cursor-pointer">
              + Note
            </button>
            <button onClick={() => act("escalation_requested", "Consultant-initiated escalation")} disabled={actionLoading} className="text-xs font-bold px-4 py-2 rounded-xl border-2 border-clinical-critical text-clinical-critical hover:bg-clinical-critical hover:text-white transition-all cursor-pointer disabled:opacity-40">
              Escalate
            </button>
          </div>
        </div>

        {/* Big Info Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-surface-secondary rounded-xl p-4 border border-border">
            <p className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest mb-1">Bed Number</p>
            <p className="text-xl font-black text-text-primary">{enc.bed?.startsWith('Bed') ? enc.bed : `Bed ${enc.bed || '--'}`}</p>
          </div>
          <div className="bg-surface-secondary rounded-xl p-4 border border-border">
            <p className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest mb-1">Diagnosis</p>
            <p className="text-xl font-black text-text-primary truncate">{enc.admitting_diagnosis || "--"}</p>
          </div>
          <div className="bg-surface-secondary rounded-xl p-4 border border-border">
            <p className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest mb-1">Responsible Consultant</p>
            <p className="text-xl font-black text-text-primary truncate">{data.consultant || "--"}</p>
          </div>
          <div className="bg-surface-secondary rounded-xl p-4 border border-border">
            <p className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest mb-1">Day {enc.length_of_stay || "--"}</p>
            <p className="text-sm font-black text-text-secondary mt-1">{data.gender}, DOB {data.birthDate}</p>
          </div>
        </div>

        {showNoteForm && (
          <div className="mt-4 pt-4 border-t border-border">
            <textarea
              value={noteInput}
              onChange={(e) => setNoteInput(e.target.value)}
              placeholder="Type clinical note…"
              className="w-full border border-border rounded-lg p-3 text-sm h-20 resize-none focus:outline-none focus:ring-2 focus:ring-clinical-info/30 focus:border-clinical-info"
            />
            <div className="flex gap-2 mt-2">
              <button
                onClick={() => { if (noteInput.trim()) { act("clinical_note_added", noteInput.trim()); setNoteInput(""); setShowNoteForm(false); } }}
                disabled={actionLoading}
                className="text-xs font-semibold px-4 py-2 rounded-lg bg-clinical-info text-white hover:bg-blue-700 transition-colors cursor-pointer disabled:opacity-40"
              >
                Save
              </button>
              <button onClick={() => { setShowNoteForm(false); setNoteInput(""); }} className="text-xs text-text-tertiary hover:text-text-secondary cursor-pointer">
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ══════════════════════════════════════════════════════════
          ROW 1 — Evidence: Vitals + Labs (side by side)
         ══════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-3 gap-5">
        {/* Vitals Chart — 2/3 width */}
        <div className="col-span-2">
          {data.vital_trends?.length > 0 ? (
            <Card title="Vital Signs (24h)">
              <VitalChart trends={data.vital_trends} />
            </Card>
          ) : (
            <Card title="Vital Signs"><p className="text-sm text-text-tertiary">No vitals recorded.</p></Card>
          )}
        </div>

        {/* Discharge Status — 1/3 width (Swapped from sidebar) */}
        <Card title="Discharge Eligibility">
          <div className="mb-3 flex items-center justify-between">
            <Badge variant={discharge.status === "Ready" ? "success" : discharge.status === "Requires Review" ? "warning" : "default"}>
              {discharge.status || "--"}
            </Badge>
            {data.discharge_override && (
              <span className="text-[9px] font-black text-clinical-info uppercase tracking-widest px-2 py-0.5 rounded bg-clinical-info-bg border border-clinical-info-border">
                {data.discharge_override.replace(/_/g, " ")}
              </span>
            )}
          </div>

          <div className="space-y-4">
            {/* Not Ready / Unmet */}
            {discharge.checklist?.some(c => !c.met) && (
              <div className="space-y-1">
                <p className="text-[9px] font-bold text-clinical-critical uppercase tracking-wider mb-1">Needs Resolution</p>
                {discharge.checklist.filter(c => !c.met).map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="font-bold text-clinical-critical">✗</span>
                    <span className="text-text-primary font-medium">{c.item}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Ready / Met */}
            {discharge.checklist?.some(c => c.met) && (
              <div className="space-y-1">
                <p className="text-[9px] font-bold text-clinical-normal uppercase tracking-wider mb-1">Criteria Met</p>
                {discharge.checklist.filter(c => c.met).map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs opacity-60">
                    <span className="font-bold text-clinical-normal">✓</span>
                    <span className="text-text-tertiary">{c.item}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex gap-2 mt-4 pt-3 border-t border-border">
            <button
              onClick={() => act("discharge_approved", "Clinically safe for discharge")}
              disabled={actionLoading}
              className="flex-1 text-[10px] font-bold py-1.5 rounded-lg bg-clinical-normal/10 text-clinical-normal border border-clinical-normal/20 hover:bg-clinical-normal hover:text-white transition-colors cursor-pointer disabled:opacity-40"
            >
              Approve
            </button>
            <button
              onClick={() => act("discharge_blocked", "Discharge not safe")}
              disabled={actionLoading}
              className="flex-1 text-[10px] font-bold py-1.5 rounded-lg border border-clinical-critical/20 text-clinical-critical hover:bg-clinical-critical hover:text-white transition-colors cursor-pointer disabled:opacity-40"
            >
              Block
            </button>
          </div>
        </Card>
      </div>

      {/* ══════════════════════════════════════════════════════════
          ROW 2 — AI Briefing + Sidebar (Alerts, Discharge, Meds)
         ══════════════════════════════════════════════════════════ */}
      <div className="grid grid-cols-3 gap-5">
        {/* LEFT — AI Clinical Briefing (2/3) */}
        <div className="col-span-2 space-y-5">
          {/* Summary */}
          <Card title="Clinical Briefing">
            <div className="space-y-5">
              {/* Overnight Summary */}
              <div>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {briefing.overnight_summary || "No summary available."}
                </p>
              </div>

              {/* Discussion Points */}
              {briefing.ward_round_talking_points?.length > 0 && (
                <div>
                  <h4 className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest mb-2">Discussion Points</h4>
                  <ul className="space-y-1.5">
                    {briefing.ward_round_talking_points.map((pt, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                        <span className="text-clinical-info mt-0.5 font-bold shrink-0">•</span>
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Plan */}
              {briefing.suggested_plan_adjustments && (
                <div className="bg-clinical-info-bg border border-clinical-info-border rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <h4 className="text-[10px] font-bold text-clinical-info uppercase tracking-widest">Suggested Plan</h4>
                    <button
                      onClick={() => act("clinical_note_added", `Applied Suggested Plan: ${briefing.suggested_plan_adjustments}`)}
                      disabled={actionLoading}
                      className="text-[9px] font-black bg-clinical-info text-white px-2 py-0.5 rounded-md uppercase hover:bg-blue-700 transition-colors cursor-pointer disabled:opacity-40 flex items-center gap-1"
                    >
                      <span>+</span> Add to Notes
                    </button>
                  </div>
                  <p className="text-sm text-text-primary leading-relaxed">{briefing.suggested_plan_adjustments}</p>
                </div>
              )}

              {/* Diagnostic Reports (Unlocked) */}
              {data.diagnostic_reports?.length > 0 && (
                <div className="pt-4 border-t border-border-light">
                  <h4 className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest mb-2">Diagnostic Reports</h4>
                  <div className="space-y-3">
                    {data.diagnostic_reports.map((dr, i) => (
                      <div key={i} className="bg-surface-secondary rounded-lg p-2.5 border border-border-light">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-black text-text-primary uppercase">{dr.test}</span>
                          <span className="text-[9px] text-text-tertiary tabular-nums font-medium">{dr.date?.slice(0, 10)}</span>
                        </div>
                        <p className="text-xs text-text-secondary font-medium leading-relaxed italic">"{dr.conclusion}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>


        </div>

        {/* RIGHT — Discharge + Drug Safety (1/3) */}
        <div className="space-y-5">
          {/* Lab Results — Swapped from top row */}
          <Card title="Lab Results">
            {data.lab_trends?.length > 0 ? (
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border-light">
                    <th className="text-left py-1.5 font-semibold text-text-tertiary uppercase">Test</th>
                    <th className="text-right py-1.5 font-semibold text-text-tertiary uppercase">Prev</th>
                    <th className="text-right py-1.5 font-semibold text-text-tertiary uppercase">Now</th>
                    <th className="text-center py-1.5 w-8"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-light">
                  {data.lab_trends.map((t, i) => (
                    <tr key={i}>
                      <td className="py-2 font-medium text-text-primary">{t.parameter || t.loinc}</td>
                      <td className="py-2 text-right text-text-tertiary tabular-nums">
                        {typeof t.oldest === "number" ? t.oldest.toFixed(2) : t.oldest}
                      </td>
                      <td className="py-2 text-right font-bold text-text-primary tabular-nums">
                        {typeof t.newest === "number" ? t.newest.toFixed(2) : t.newest}
                      </td>
                      <td className="py-2 text-center"><TrendIndicator direction={t.direction} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="text-sm text-text-tertiary">No lab data.</p>
            )}
          </Card>

          {/* Active Medications */}
          <Card title="Active Medications">
            {activeMeds.length > 0 ? (
              <div className="space-y-2">
                {activeMeds.map((m, i) => (
                  <div key={i} className="flex items-start justify-between text-xs py-1 border-b border-border-light last:border-0">
                    <span className="font-bold text-text-primary">{m.name}</span>
                    <span className="text-text-tertiary text-right max-w-[120px] truncate">{m.dosage}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-tertiary">No active medications.</p>
            )}
          </Card>

          {/* Drug Safety */}
          {data.fda_safety?.drug_warnings?.length > 0 && (
            <Card
              title="Drug Safety"
              footer={
                <div className="mt-2 text-[9px] text-text-tertiary italic text-right">
                  Powered by OpenFDA
                </div>
              }
            >
              <div className="space-y-2">
                {data.fda_safety.drug_warnings.map((w, i) => (
                  <DrugWarning key={i} w={w} />
                ))}
              </div>
            </Card>
          )}

        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════
          FIXED WIDGETS — Floating UI
         ══════════════════════════════════════════════════════════ */}
      <SafetyAlertsWidget alerts={alerts} flags={flags} onAck={(c) => act("conflict_acknowledged", `Reviewed: ${c.message?.slice(0, 80)}`, c.conflict_id)} actionLoading={actionLoading} />
      <ClinicalNotesWidget notes={clinicalNotes} />

      {/* ══════════════════════════════════════════════════════════
          STICKY NAVIGATOR — Bottom Center (White Theme)
         ══════════════════════════════════════════════════════════ */}
      <div className="fixed bottom-4 left-[58%] -translate-x-1/2 z-40 w-[580px] pointer-events-none">
        <div className="bg-white border border-border rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.2)] p-3 flex items-center justify-between pointer-events-auto backdrop-blur-xl bg-white/95">
          {/* Prev Button */}
          <Link
            href={prevPatient ? `/dashboard/patient/${prevPatient.patient_id}` : "#"}
            className={`w-11 h-11 flex items-center justify-center rounded-xl transition-all shadow-sm ${prevPatient ? 'bg-surface-secondary hover:bg-border text-text-primary cursor-pointer' : 'opacity-20 cursor-not-allowed'}`}
          >
            <span className="text-xl">←</span>
          </Link>

          {/* Expanded Horizontal Context */}
          <div className="flex-1 px-4 flex items-center justify-between gap-2">
            <div className="text-left flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-[9px] font-black bg-text-primary text-white px-1.5 py-0.5 rounded uppercase shadow-sm shrink-0">
                  {enc.bed?.startsWith('Bed') ? enc.bed : `Bed ${enc.bed}`}
                </span>
                <h4 className="text-xs font-black text-text-primary truncate">{data.name}</h4>
              </div>
              <p className="text-[9px] font-bold text-text-tertiary uppercase tracking-tight mt-0.5 truncate">
                {enc.admitting_diagnosis}
              </p>
            </div>

            <div className="h-6 w-px bg-border-light mx-1" />

            <div className="text-center px-1 max-w-[100px]">
              <p className="text-[7px] font-black text-text-tertiary uppercase tracking-widest mb-0.5">Lead</p>
              <p className="text-[10px] font-bold text-text-primary truncate">{data.consultant}</p>
            </div>

            <div className="h-6 w-px bg-border-light mx-1" />

            <div className="text-right shrink-0">
              <div className="flex items-center justify-end gap-2 mb-0.5">
                <span className={`text-[10px] font-black uppercase ${news2.risk_level === 'HIGH' ? 'text-clinical-critical' : 'text-clinical-normal'}`}>
                  NEWS2 {news2.total_score}
                </span>
                <span className="text-[9px] font-bold text-text-tertiary">D{enc.length_of_stay}</span>
              </div>
              <p className="text-[8px] font-black text-text-tertiary tracking-widest">
                {currentIdx + 1}/{wardList.length} PATIENTS
              </p>
            </div>
          </div>

          {/* Next Button */}
          <Link
            href={nextPatient ? `/dashboard/patient/${nextPatient.patient_id}` : "#"}
            className={`w-11 h-11 flex items-center justify-center rounded-xl transition-all shadow-sm ${nextPatient ? 'bg-surface-secondary hover:bg-border text-text-primary cursor-pointer' : 'opacity-20 cursor-not-allowed'}`}
          >
            <span className="text-xl">→</span>
          </Link>
        </div>
      </div>

      {toast && <Toast message={toast} onClose={() => setToast("")} />}
    </div>
  );
}

/* ── Fixed Clinical Notes Widget ───────────────────────────── */

function ClinicalNotesWidget({ notes }) {
  const [minimized, setMinimized] = useState(true);

  return (
    <div className={`fixed bottom-4 right-6 z-50 transition-all duration-300 ease-in-out flex flex-col ${minimized ? "w-56 h-11" : "w-96 h-96"}`}>
      <div
        onClick={() => setMinimized(!minimized)}
        className={`bg-clinical-info text-white px-4 py-2.5 cursor-pointer flex items-center justify-between shadow-[0_10px_30px_rgba(59,130,246,0.3)] transition-all hover:scale-[1.02] active:scale-[0.98] ${minimized ? "rounded-xl" : "rounded-t-xl"}`}
      >
        <span className="text-[11px] font-bold uppercase tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
          Clinical Notes
        </span>
        <span className="text-xs font-black">{minimized ? "▲" : "▼"}</span>
      </div>

      {!minimized && (
        <div className="bg-white border-x border-b border-border p-4 rounded-b-xl shadow-2xl flex-1 overflow-y-auto custom-scrollbar backdrop-blur-md bg-white/95">
          {notes?.length > 0 ? (
            <div className="space-y-4">
              {notes.map((n, i) => (
                <div key={i} className="pb-3 border-b border-border-light last:border-0 last:pb-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] font-black text-clinical-info uppercase">{n.author}</span>
                    <span className="text-[9px] text-text-tertiary tabular-nums font-medium">
                      {n.date?.slice(5, 16)?.replace("T", " ")}
                    </span>
                  </div>
                  <p className="text-[11px] text-text-secondary leading-relaxed">{n.text}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-text-tertiary text-center py-10 italic">No notes available.</p>
          )}
        </div>
      )}
    </div>
  );
}

/* ── Fixed Safety & Alerts Widget (Top Right) ──────────────── */

function SafetyAlertsWidget({ alerts, flags, onAck, actionLoading }) {
  const [minimized, setMinimized] = useState(false);
  const activeAlerts = alerts.filter(a => !a.acknowledged);
  const totalCount = activeAlerts.length + flags.length;

  if (totalCount === 0) return null;

  return (
    <div className={`fixed bottom-4 left-[260px] z-50 transition-all duration-300 ease-in-out flex flex-col ${minimized ? "w-56 h-11" : "w-96 h-96"}`}>
      <div
        onClick={() => setMinimized(!minimized)}
        className={`bg-clinical-critical text-white px-4 py-2.5 cursor-pointer flex items-center justify-between shadow-[0_10px_30px_rgba(239,68,68,0.3)] transition-all hover:scale-[1.02] active:scale-[0.98] ${minimized ? "rounded-xl" : "rounded-t-xl"}`}
      >
        <div className="flex items-center gap-2">
          <span className="text-xs animate-bounce">⚠️</span>
          <span className="text-[11px] font-bold uppercase tracking-wider">
            Safety & Conflicts
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-white/20 text-[10px] px-1.5 py-0.5 rounded-full font-black">{totalCount}</span>
          <span className="text-xs">{minimized ? "▲" : "▼"}</span>
        </div>
      </div>

      {!minimized && (
        <div className="bg-white border-x border-b border-border p-3 rounded-b-xl shadow-2xl flex-1 overflow-hidden backdrop-blur-md bg-white/95">
          <div className="space-y-3 h-full overflow-y-auto pr-1 custom-scrollbar">
            {/* Rule Alerts */}
            {alerts.length > 0 && (
              <div className="space-y-3">
                {alerts.map((c, i) => {
                  const ack = c.acknowledged;
                  return (
                    <div key={i} className={`flex items-start justify-between gap-3 p-2 rounded-lg transition-all ${ack ? "opacity-30 bg-surface-secondary" : "bg-clinical-critical/5 border border-clinical-critical/10"}`}>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          {!ack && <span className="w-1.5 h-1.5 rounded-full bg-clinical-critical shrink-0 animate-pulse" />}
                          <span className={`text-[11px] ${ack ? "text-text-tertiary line-through" : "text-text-primary font-bold"}`}>
                            {c.message}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-1 ml-3.5">
                          <span className="text-[8px] font-black text-clinical-critical/70 uppercase tracking-tighter">{c.severity}</span>
                        </div>
                      </div>
                      {!ack && (
                        <button
                          onClick={(e) => { e.stopPropagation(); onAck(c); }}
                          disabled={actionLoading}
                          className="text-[10px] font-bold bg-clinical-critical text-white w-6 h-6 flex items-center justify-center rounded-full hover:bg-red-700 transition-all shrink-0 cursor-pointer shadow-sm active:translate-y-px"
                          title="Acknowledge Conflict"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Safety Flags */}
            {flags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-3 border-t border-border-light">
                {flags.map((f, i) => (
                  <span key={i} className="text-[9px] font-black text-clinical-warning bg-clinical-warning-bg/40 border border-clinical-warning-border/20 px-2 py-1 rounded-md uppercase flex items-center gap-1">
                    <span className="text-xs">!</span> {typeof f === 'string' ? f : (f?.text || f?.code)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


/* ── Drug warning (collapsible) ──────────────────────────────── */

function DrugWarning({ w }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="text-xs border border-clinical-warning-border/50 bg-clinical-warning-bg/50 rounded-lg px-3 py-2">
      <div className="flex items-center justify-between">
        <span className="font-bold text-clinical-warning">{w.drug}</span>
        {w.boxed_warning && <span className="text-[9px] font-black text-clinical-critical uppercase">Boxed</span>}
      </div>
      {w.interaction_warnings && (
        <>
          <p className={`text-text-secondary mt-1 leading-relaxed ${open ? "" : "line-clamp-2"}`}>
            {w.interaction_warnings}
          </p>
          {w.interaction_warnings.length > 100 && (
            <button onClick={() => setOpen(!open)} className="text-[10px] font-bold text-clinical-info mt-0.5 hover:underline cursor-pointer">
              {open ? "Less" : "More"}
            </button>
          )}
        </>
      )}
    </div>
  );
}
