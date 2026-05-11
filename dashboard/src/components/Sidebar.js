"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { callMCPTool } from "@/lib/mcp";

function NavLink({ href, label, icon, active = false }) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-lg transition-colors ${
        active 
          ? "bg-sidebar-active text-sidebar-text-active" 
          : "text-sidebar-text hover:bg-sidebar-hover hover:text-sidebar-text-active"
      }`}
    >
      <span className="text-base leading-none">{icon}</span>
      <span>{label}</span>
    </Link>
  );
}

export default function Sidebar() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();

  useEffect(() => {
    callMCPTool("get_ward_round_summary")
      .then((data) => {
        const sorted = (data.patients || []).sort((a, b) => {
          const bedA = parseInt(a.encounter?.bed) || 999;
          const bedB = parseInt(b.encounter?.bed) || 999;
          return bedA - bedB;
        });
        setPatients(sorted);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <aside className="w-60 bg-sidebar border-r border-white/10 flex flex-col fixed inset-y-0 left-0 z-20">
      {/* Brand */}
      <div className="px-6 py-8">
        <h1 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
          <span className="text-clinical-info">Kairos</span>MD
        </h1>
        <p className="text-[10px] text-sidebar-text font-semibold uppercase tracking-widest mt-1 opacity-60">Ward Support System</p>
      </div>

      {/* Navigation */}
      <nav className="px-3 py-4 space-y-1">
        <NavLink href="/dashboard" label="Ward Home" icon={"\u2302"} active={pathname === "/dashboard"} />
      </nav>

      {/* Dynamic Patient List */}
      <div className="flex-1 overflow-y-auto border-t border-white/5 mt-4">
        <div className="mt-6">
          <div className="px-4 mb-2 text-[10px] font-bold text-sidebar-text uppercase tracking-widest">Ward Census</div>
          <div className="space-y-0.5">
            {loading ? (
              <div className="px-4 py-2 text-[10px] text-sidebar-text uppercase tracking-widest animate-pulse">Loading Census...</div>
            ) : (
              patients.map((p) => {
                const isActive = pathname.includes(`/patient/${p.patient_id}`);
                const rawBed = p.encounter?.bed || "--";
                const displayBed = rawBed.toLowerCase().includes("bed") 
                  ? rawBed.replace(/bed\s*/i, "B") 
                  : rawBed.startsWith("B") ? rawBed : `B${rawBed}`;

                return (
                  <Link
                    key={p.patient_id}
                    href={`/dashboard/patient/${p.patient_id}`}
                    className={`flex items-center gap-3 px-4 py-2 text-xs font-medium transition-colors group ${
                      isActive ? "bg-sidebar-active text-sidebar-text-active" : "text-sidebar-text hover:bg-sidebar-hover hover:text-sidebar-text-active"
                    }`}
                  >
                    <div className={`w-1.5 h-1.5 rounded-full ${
                      p.priority === "HIGH" ? "bg-clinical-critical" : 
                      p.priority === "MEDIUM" ? "bg-clinical-warning" : "bg-clinical-normal"
                    }`} />
                    <span className="w-8 text-[10px] tabular-nums opacity-50 shrink-0">{displayBed}</span>
                    <span className="truncate">{p.name}</span>
                  </Link>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Clinician Identity Switcher */}
      <div className="px-4 py-4 border-t border-white/10 bg-black/10">
        <div className="mb-3">
          <p className="text-[10px] text-sidebar-text font-bold uppercase tracking-widest opacity-60">Acting Clinician</p>
        </div>
        <div className="space-y-2">
          {[
            { name: "Dr. Mike", role: "Consultant", initial: "DM" },
            { name: "Dr. Sarah", role: "Registrar", initial: "DS" }
          ].map((doc) => {
            let isSelected = false;
            if (typeof window !== 'undefined') {
              const current = localStorage.getItem("clinician_name") || "Dr. Mike";
              isSelected = current === doc.name;
            } else {
              // Server-side default
              isSelected = doc.name === "Dr. Mike";
            }
            
            return (
              <button
                key={doc.name}
                onClick={() => {
                  if (typeof window !== 'undefined') {
                    localStorage.setItem("clinician_name", doc.name);
                    localStorage.setItem("clinician_role", doc.role);
                    window.location.reload();
                  }
                }}
                className={`w-full flex items-center gap-3 p-2 rounded-lg transition-all text-left ${
                  isSelected ? "bg-white/10 ring-1 ring-white/20" : "hover:bg-white/5 opacity-50"
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold text-white ${
                  isSelected ? "bg-clinical-info" : "bg-sidebar-text/20"
                }`}>
                  {doc.initial}
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-white truncate">{doc.name}</p>
                  <p className="text-[9px] text-sidebar-text truncate">{doc.role}</p>
                </div>
                {isSelected && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-clinical-info" />}
              </button>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
