"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { callMCPTool } from "../../shared/mcp.js";

function DischargeCard({ patient }) {
  const status = patient.discharge?.status || "Not Ready";
  const override = patient.discharge_override;
  const displayStatus = override ? (override === "discharge_approved" ? "APPROVED" : "BLOCKED") : status;
  
  const statusColors = {
    "Ready": "border-clinical-normal bg-clinical-normal-bg text-clinical-normal",
    "Requires Review": "border-clinical-warning bg-clinical-warning-bg text-clinical-warning",
    "APPROVED": "border-clinical-normal bg-clinical-normal text-white",
    "BLOCKED": "border-clinical-critical bg-clinical-critical text-white",
    "Not Ready": "border-border bg-surface-secondary text-text-tertiary",
  };

  return (
    <div className={`rounded-xl border p-5 shadow-sm transition-all hover:shadow-md bg-white ${status === 'Ready' || override === 'discharge_approved' ? 'ring-2 ring-clinical-normal ring-offset-2' : ''}`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-sm font-bold text-text-primary">{patient.name}</h4>
          <p className="text-[10px] font-bold text-text-tertiary uppercase tracking-wider">Bed {patient.encounter?.bed} • {patient.encounter?.admitting_diagnosis}</p>
        </div>
        <span className={`text-[9px] font-black px-2 py-1 rounded uppercase ${statusColors[displayStatus] || statusColors["Not Ready"]}`}>
          {displayStatus}
        </span>
      </div>

      <div className="space-y-2 mb-5">
        {(patient.discharge?.checklist || []).map((item, i) => (
          <div key={i} className="flex items-center gap-2 text-xs">
            <span className={item.met ? "text-clinical-normal font-bold" : "text-clinical-critical font-bold"}>
              {item.met ? "✓" : "✗"}
            </span>
            <span className={item.met ? "text-text-secondary" : "text-text-primary font-medium"}>{item.item}</span>
          </div>
        ))}
      </div>

      <div className="flex gap-2 border-t border-border pt-4">
        <Link 
          href={`/dashboard/patient/${patient.patient_id}`}
          className="flex-1 text-center text-[10px] font-bold py-2 rounded-lg bg-surface-secondary text-text-secondary hover:bg-border transition-colors"
        >
          View Full Record
        </Link>
      </div>
    </div>
  );
}

export default function DischargeBoard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    callMCPTool("get_discharge_candidates")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center animate-pulse text-text-tertiary font-bold uppercase tracking-widest text-xs">Loading Discharge Board...</div>;
  if (error) return <div className="p-8 text-clinical-critical bg-clinical-critical-bg rounded-xl border border-clinical-critical-border m-6">{error}</div>;

  const candidates = data?.candidates || [];
  const ready = candidates.filter(c => c.discharge?.status === "Ready" || c.discharge_override === "discharge_approved");
  const review = candidates.filter(c => c.discharge?.status === "Requires Review" && !c.discharge_override);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-black text-text-primary tracking-tight">Discharge Planning Board</h2>
        <p className="text-[10px] font-bold text-clinical-info uppercase tracking-[0.2em] mt-1">Bed Management & Flow Optimization</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Ready to Go */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b-2 border-clinical-normal pb-2">
            <h3 className="text-xs font-black text-clinical-normal uppercase tracking-widest">Ready for Discharge</h3>
            <span className="text-xs font-bold bg-clinical-normal text-white px-2 py-0.5 rounded-full">{ready.length}</span>
          </div>
          <div className="grid gap-4">
            {ready.length > 0 ? ready.map(p => <DischargeCard key={p.patient_id} patient={p} />) : (
              <p className="text-xs text-text-tertiary italic py-10 text-center bg-surface-secondary rounded-xl">No patients fully cleared for discharge.</p>
            )}
          </div>
        </section>

        {/* Pending Review */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b-2 border-clinical-warning pb-2">
            <h3 className="text-xs font-black text-clinical-warning uppercase tracking-widest">Requires Review</h3>
            <span className="text-xs font-bold bg-clinical-warning text-white px-2 py-0.5 rounded-full">{review.length}</span>
          </div>
          <div className="grid gap-4">
            {review.length > 0 ? review.map(p => <DischargeCard key={p.patient_id} patient={p} />) : (
              <p className="text-xs text-text-tertiary italic py-10 text-center bg-surface-secondary rounded-xl">No patients pending review.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
