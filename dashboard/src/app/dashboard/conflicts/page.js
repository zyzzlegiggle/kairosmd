"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { callMCPTool } from "../../../shared/mcp.js";

function ConflictRow({ conflict, patientId, patientName, bed }) {
  const urgencyColors = {
    "CRITICAL": "bg-clinical-critical text-white",
    "WARNING": "bg-clinical-warning text-white",
    "INFO": "bg-clinical-info text-white",
  };

  return (
    <div className="group border-b border-border hover:bg-surface-secondary transition-colors p-4">
      <div className="flex items-start gap-4">
        <div className={`w-2 h-12 rounded-full shrink-0 ${urgencyColors[conflict.urgency] || urgencyColors["INFO"]}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-1">
            <span className="text-[10px] font-black uppercase tracking-widest text-text-tertiary">Bed {bed}</span>
            <span className="text-sm font-bold text-text-primary">{patientName}</span>
          </div>
          <h4 className="text-sm font-bold text-clinical-critical mb-1">{conflict.type.replace(/_/g, " ")}</h4>
          <p className="text-xs text-text-secondary leading-relaxed">{conflict.description}</p>
        </div>
        <div className="flex flex-col gap-2">
          <Link 
            href={`/dashboard/patient/${patientId}`}
            className="text-[10px] font-bold py-1.5 px-3 rounded bg-clinical-info text-white hover:bg-blue-700 transition-colors text-center"
          >
            Review
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function ConflictBoard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    callMCPTool("get_conflict_report")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-8 text-center animate-pulse text-text-tertiary font-bold uppercase tracking-widest text-xs">Loading Safety Board...</div>;
  if (error) return <div className="p-8 text-clinical-critical bg-clinical-critical-bg rounded-xl border border-clinical-critical-border m-6">{error}</div>;

  const patients = data?.patients_with_conflicts || [];
  const totalConflicts = patients.reduce((acc, p) => acc + (p.conflicts?.length || 0), 0);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-end justify-between border-b-4 border-clinical-critical pb-4">
        <div>
          <h2 className="text-2xl font-black text-text-primary tracking-tight">Clinical Safety Board</h2>
          <p className="text-[10px] font-bold text-clinical-critical uppercase tracking-[0.2em] mt-1 italic">Silent Contradiction Detection Engine</p>
        </div>
        <div className="text-right">
          <span className="text-4xl font-black text-clinical-critical leading-none">{totalConflicts}</span>
          <p className="text-[10px] font-black text-text-tertiary uppercase">Active Conflicts</p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-border shadow-xl overflow-hidden">
        {patients.length > 0 ? (
          patients.map(p => (
            <div key={p.patient_id}>
              {p.conflicts.map((c, i) => (
                <ConflictRow 
                  key={`${p.patient_id}-${i}`} 
                  conflict={c} 
                  patientId={p.patient_id} 
                  patientName={p.name} 
                  bed={p.encounter?.bed} 
                />
              ))}
            </div>
          ))
        ) : (
          <div className="py-20 text-center">
            <div className="text-4xl mb-4">✓</div>
            <p className="text-sm font-bold text-clinical-normal uppercase tracking-widest">No active clinical conflicts detected.</p>
          </div>
        )}
      </div>
    </div>
  );
}
