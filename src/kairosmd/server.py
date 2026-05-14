"""KairosMD MCP Server — Multidisciplinary Ward Round Decision Support (MDS).

Connects to FHIR R4 backend for clinical data.

Exposes 8 MCP tools:
  1. get_ward_round_summary   - Prioritised ward overview (all 20 patients)
  2. get_patient_ward_detail  - Single-patient deep dive
  3. get_discharge_candidates - Discharge readiness assessment
  4. get_conflict_report      - Cross-source conflict detection
  5. record_ward_action       - MDT action persistence
  6. get_action_history       - Clinical audit trail
  7. get_drug_safety_info     - FDA label + FAERS lookup (OpenFDA)
  8. get_dashboard_access     - Visual dashboard links
  9. apply_suggested_plan     - Apply AI plan to clinical notes
"""

from __future__ import annotations
import json
import asyncio
from datetime import date

from mcp.server.fastmcp import FastMCP

from kairosmd import config
from kairosmd.fhir_client import FHIRClient
from kairosmd.ward_engine import compile_patient_ward_data
from kairosmd.llm_agent import generate_patient_briefing
from kairosmd.ward_actions import (
    record_action, get_actions, is_conflict_acknowledged,
    get_escalation_status, get_discharge_override,
)

import os as _os
_port = int(_os.getenv("PORT", 8000))
mcp = FastMCP(
    "KairosMD MDS",
    host="0.0.0.0",
    port=_port
)

def get_fhir_client() -> FHIRClient:
    """Return a FHIR client using configured defaults."""
    return FHIRClient()

# Priority sort order for ward round
PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

import json as _json
import time
from pathlib import Path

CACHE_TTL = 86400  # 24 hours
PERSISTENT_CACHE_PATH = Path(__file__).parent / "ward_cache.json"
_patient_cache: dict[str, tuple[float, dict]] = {}  # pid -> (timestamp, data)


def _load_persistent_cache():
    """Load analyzed patient data from disk if available."""
    global _patient_cache
    if PERSISTENT_CACHE_PATH.exists():
        try:
            raw = PERSISTENT_CACHE_PATH.read_text()
            data = _json.loads(raw)
            # Convert back to our internal tuple format
            _patient_cache = {k: (time.time(), v) for k, v in data.items()}
            print(f"--- [CACHE] Loaded {len(_patient_cache)} patients from disk. ---")
        except Exception as e:
            print(f"--- [CACHE] Error loading disk cache: {e} ---")


def _save_persistent_cache():
    """Save current analyzed patient data to disk."""
    try:
        # Save only the data part, ignore the timestamp
        serializable = {k: v[1] for k, v in _patient_cache.items()}
        PERSISTENT_CACHE_PATH.write_text(_json.dumps(serializable, indent=2))
        print(f"--- [CACHE] Saved {len(_patient_cache)} patients to disk. ---")
    except Exception as e:
        print(f"--- [CACHE] Error saving disk cache: {e} ---")


def _get_cached(pid: str) -> dict | None:
    """Return cached patient data if still fresh."""
    entry = _patient_cache.get(pid)
    if entry and (time.time() - entry[0]) < CACHE_TTL:
        return entry[1]
    return None


def _set_cached(pid: str, data: dict):
    """Store patient data in cache."""
    _patient_cache[pid] = (time.time(), data)


def _invalidate_cache(pid: str):
    """Remove patient from cache to force re-fetch."""
    if pid in _patient_cache:
        del _patient_cache[pid]


def _attach_actions(pid: str, data: dict) -> dict:
    """Re-attach live action metadata to cached patient data.
    This is fast — all in-memory, no FHIR or LLM calls."""
    result = dict(data)  # shallow copy
    actions = get_actions(pid)
    escalation = get_escalation_status(pid)
    discharge_override = get_discharge_override(pid)

    # Re-check conflict acknowledgements
    for i, c in enumerate(result.get("conflicts", [])):
        cid = f"{pid}-conflict-{i}"
        c["conflict_id"] = cid
        c["acknowledged"] = is_conflict_acknowledged(pid, cid)

    result["actions"] = actions
    result["escalation_status"] = escalation
    result["discharge_override"] = discharge_override

    # Merge in-memory actions into clinical notes for instant UI feedback
    # (Bypasses FHIR indexing latency)
    all_notes = list(result.get("clinical_notes", []))
    for a in actions:
        if a["action_type"] in ("clinical_note_added", "conflict_acknowledged"):
            # Avoid duplicate if it already synced to FHIR and came back in clinical_notes
            text = a["detail"] if a["action_type"] == "clinical_note_added" else f"Acknowledged: {a['detail']}"
            if not any(n.get("text") == text for n in all_notes):
                all_notes.append({
                    "date": a["timestamp"],
                    "author": a["clinician"],
                    "text": text,
                    "is_unsynced": True # Optional hint for UI
                })
    
    # Sort notes by date descending
    all_notes.sort(key=lambda x: x.get("date", ""), reverse=True)
    result["clinical_notes"] = all_notes
    
    return result


# -- Helper: process one patient ---------------------------------------
async def _process_patient(pid: str, fhir: FHIRClient) -> dict:
    """Fetch all FHIR data and run ward analysis for a single patient.
    Uses server-side cache to avoid redundant FHIR/LLM calls."""

    # Check cache first
    cached = _get_cached(pid)
    if cached:
        print(f"  [CACHE HIT] {pid}")
        return _attach_actions(pid, cached)

    try:
        # Fetch patient demographics
        patient = await fhir.get_patient(pid)
        name_parts = patient.get("name", [{}])[0]
        name = name_parts.get("text", "")
        if not name:
            given = " ".join(name_parts.get("given", [""]))
            family = name_parts.get("family", "")
            name = f"{given} {family}".strip()
        name = name or "Unknown"
        dob = patient.get("birthDate", "")
        gender = patient.get("gender", "")

        # Fetch all clinical data SEQUENTIALLY to avoid 429
        vitals = await fhir.get_vitals(pid, count=50)
        await asyncio.sleep(0.3)
        labs = await fhir.get_labs(pid, count=50)
        await asyncio.sleep(0.3)
        notes = await fhir.get_clinical_notes(pid, count=20)
        await asyncio.sleep(0.3)
        conditions = await fhir.get_conditions(pid)
        await asyncio.sleep(0.3)
        medications = await fhir.get_medications(pid)
        await asyncio.sleep(0.3)
        allergies = await fhir.get_allergies(pid)
        await asyncio.sleep(0.3)
        encounter = await fhir.get_encounter_for_patient(pid)
        await asyncio.sleep(0.3)
        med_admins = await fhir.get_med_admins(pid)
        await asyncio.sleep(0.3)
        flags = await fhir.get_flags(pid)
        await asyncio.sleep(0.3)
        care_team = await fhir.get_care_team(pid)
        await asyncio.sleep(0.3)
        communications = await fhir.get_communications(pid)
        await asyncio.sleep(0.3)
        diag_reports = await fhir.get_diagnostic_reports(pid)

        # Run ward engine
        result = await compile_patient_ward_data(
            vitals, labs, notes, conditions, medications,
            allergies, med_admins, flags, 
            care_team=care_team,
            communications=communications,
            diag_reports=diag_reports,
            encounter=encounter,
        )

        # Generate LLM briefing
        briefing_context = {
            "name": name, "birthDate": dob, "gender": gender,
            **result,
        }
        briefing = await generate_patient_briefing(briefing_context)

        base_data = {
            "patient_id": pid,
            "name": name,
            "birthDate": dob,
            "gender": gender,
            **result,
            "llm_briefing": briefing,
        }

        # Cache it
        _set_cached(pid, base_data)

        # Attach live actions and return
        return _attach_actions(pid, base_data)

    except Exception as e:
        print(f"  ERROR processing patient {pid}: {e}")
        return {
            "patient_id": pid,
            "name": "Unknown",
            "priority": "MEDIUM",
            "news2": {"total_score": 0, "risk_level": "LOW"},
            "conflicts": [],
            "conflict_count": 0,
            "discharge": {"status": "Requires Review"},
            "error": str(e),
            "llm_briefing": {"data_completeness": "incomplete"},
            "care_team": [
                {"name": "Dr. Mike", "role": "Lead Consultant (MDS)"},
                {"name": "Dr. Amir (HO)", "role": "Junior Doctor"}
            ]
        }


# -- Cache Warmer ------------------------------------------------------
async def warm_cache():
    """Pre-fetch all patient data on startup so the first request is instant."""
    print("\n--- [CACHE] Starting background cache warm-up... ---")
    try:
        client = get_fhir_client()
        patient_ids = await _get_ward_patient_ids(client)
        print(f"--- [CACHE] Warming data for {len(patient_ids)} patients... ---")
        
        for i, pid in enumerate(patient_ids):
            if _get_cached(pid):
                continue
            
            print(f"  [CACHE] {i+1}/{len(patient_ids)}: Processing {pid}...")
            await _process_patient(pid, client)
            
            # Small delay to prevent 429 during warming
            if i < len(patient_ids) - 1:
                await asyncio.sleep(1.0)
                
        print("--- [CACHE] Warm-up complete. All patients ready. ---\n")
        _save_persistent_cache()
    except Exception as e:
        print(f"--- [CACHE] Warm-up failed: {e} ---")




# -- Helper: get all ward patient IDs ---------------------------------
async def _get_ward_patient_ids(fhir: FHIRClient) -> list[str]:
    """Get all patient IDs from the ward manifest (created by seed.py).
    
    On a shared public FHIR server, searching all encounters globally
    returns other users' data. Instead, we read our own manifest.
    """
    import json as _json
    from pathlib import Path

    manifest_path = Path(__file__).parent / "ward_manifest.json"
    
    if not manifest_path.exists():
        print("  [WARN] No ward_manifest.json found. Run `uv run python -m kairosmd.seed` first.")
        return []
    
    try:
        manifest = _json.loads(manifest_path.read_text())
        patient_ids = [entry["patient_id"] for entry in manifest if "patient_id" in entry]
        print(f"  [FHIR] Loaded {len(patient_ids)} patients from ward manifest.")
        return patient_ids
    except Exception as e:
        print(f"  [WARN] Failed to read manifest: {e}")
        return []


# -- Helper: sort ward results ----------------------------------------
def _sort_ward_list(triage_list: list[dict]) -> list[dict]:
    """Sort by: NEWS2 HIGH > has conflicts > MEDIUM > LOW."""
    def sort_key(entry):
        priority = PRIORITY_ORDER.get(entry.get("priority", "LOW"), 2)
        has_conflicts = 0 if entry.get("conflict_count", 0) > 0 else 1
        news2 = -(entry.get("news2", {}).get("total_score", 0))
        return (priority, has_conflicts, news2)
    return sorted(triage_list, key=sort_key)


# -- Helper: slim patient projection for multi-patient tools -----------
def _slim_summary(entry: dict) -> dict:
    """Project a full patient record to a compact summary.

    Strips out raw vitals/labs arrays, full clinical notes text,
    FDA data, care team roster, audit trail, and diagnostic reports.
    Keeps only the clinical bottom-line per patient to minimise
    LLM input token usage on multi-patient tool calls.
    """
    # Compact NEWS2: just score + risk, drop per-parameter breakdown
    news2_full = entry.get("news2", {})
    news2_slim = {
        "total_score": news2_full.get("total_score", 0),
        "risk_level": news2_full.get("risk_level", "LOW"),
    }

    # Compact conflicts: type + short description only
    conflicts_slim = []
    for c in entry.get("conflicts", []):
        conflicts_slim.append({
            "type": c.get("type", ""),
            "description": c.get("description", "")[:120],
            "severity": c.get("severity", ""),
            "acknowledged": c.get("acknowledged", False),
        })

    # Compact LLM briefing: just the summary string
    briefing = entry.get("llm_briefing", {})
    briefing_slim = briefing.get("summary", "") if isinstance(briefing, dict) else str(briefing)[:300]

    # Medication names only (no dosage/code bloat)
    med_names = [m.get("name", "") for m in entry.get("active_medications", [])]

    # Allergy names only
    allergy_names = [a.get("name", "") for a in entry.get("allergies", [])]

    return {
        "patient_id": entry.get("patient_id"),
        "name": entry.get("name"),
        "encounter": entry.get("encounter"),
        "priority": entry.get("priority"),
        "news2": news2_slim,
        "conflict_count": entry.get("conflict_count", 0),
        "conflicts": conflicts_slim,
        "discharge": entry.get("discharge"),
        "active_conditions": entry.get("active_conditions", []),
        "safety_flags": entry.get("safety_flags", []),
        "medications": med_names,
        "allergies": allergy_names,
        "consultant": entry.get("consultant"),
        "briefing": briefing_slim,
        "actions": entry.get("actions", []),
        "escalation_status": entry.get("escalation_status"),
        "discharge_override": entry.get("discharge_override"),
        "dashboard_url": f"{config.DASHBOARD_BASE_URL}/dashboard/patient/{entry.get('patient_id')}",
    }


# =====================================================================
# TOOL 1: get_ward_round_summary
# =====================================================================
@mcp.tool()
async def get_ward_round_summary() -> str:
    """Get the morning ward round summary for all inpatient patients.

    Returns a prioritised list of patients on the ward with:
    - NEWS2 score and risk level
    - Overnight change detection
    - Conflict alerts
    - Discharge readiness
    - AI-generated clinical briefing

    Sorted by clinical priority (high risk first, discharge ready last).
    """
    client = get_fhir_client()
    patient_ids = await _get_ward_patient_ids(client)

    if not patient_ids:
        return json.dumps({
            "error": "No active inpatient encounters found",
            "dashboard_url": f"{config.DASHBOARD_BASE_URL}/dashboard",
        })

    # Process patients sequentially with rate limiting
    ward_list = []
    for i, pid in enumerate(patient_ids):
        print(f"  Processing patient {i+1}/{len(patient_ids)} ({pid})...")
        entry = await _process_patient(pid, client)
        ward_list.append(entry)
        if i < len(patient_ids) - 1:
            await asyncio.sleep(1.0)

    ward_list = _sort_ward_list(ward_list)

    # Summary stats
    high_risk = sum(1 for p in ward_list if p.get("priority") == "HIGH")
    medium_risk = sum(1 for p in ward_list if p.get("priority") == "MEDIUM")
    conflicts_total = sum(p.get("conflict_count", 0) for p in ward_list)
    discharge_ready = sum(1 for p in ward_list
                          if p.get("discharge", {}).get("status") == "Ready")

    # Get ward name from the first patient's encounter info if available
    ward_name = "General Medicine Ward"
    if ward_list:
        ward_name = ward_list[0].get("encounter", {}).get("ward", ward_name)

    # Slim projection: drop raw vitals/labs/notes/FDA to cut token count
    slim_list = [_slim_summary(p) for p in ward_list]

    result = json.dumps({
        "ward": ward_name,
        "date": date.today().isoformat(),
        "total_patients": len(slim_list),
        "high_risk_count": high_risk,
        "medium_risk_count": medium_risk,
        "active_conflicts": conflicts_total,
        "discharge_candidates": discharge_ready,
        "patients": slim_list,
        "dashboard_url": f"{config.DASHBOARD_BASE_URL}/dashboard",
    })

    print(f"\n--- [LOG] Ward Round Summary: {len(slim_list)} patients ---")
    return result


# =====================================================================
# TOOL 2: get_patient_ward_detail
# =====================================================================
@mcp.tool()
async def get_patient_ward_detail(patient_id: str) -> str:
    """Get full ward round detail for a specific patient.

    Args:
        patient_id: The FHIR Patient resource ID.

    Returns detailed clinical data including vitals, labs, medications,
    notes, NEWS2 score, conflicts, discharge readiness, and AI briefing.
    """
    client = get_fhir_client()
    entry = await _process_patient(patient_id, client)
    entry["dashboard_url"] = f"{config.DASHBOARD_BASE_URL}/dashboard/patient/{patient_id}"

    result = json.dumps(entry)
    print(f"\n--- [LOG] Patient Detail: {entry.get('name', 'Unknown')} ---")
    return result


# =====================================================================
# TOOL 3: get_discharge_candidates
# =====================================================================
@mcp.tool()
async def get_discharge_candidates() -> str:
    """Get patients who are ready or near-ready for discharge.

    Returns patients flagged as 'Ready' or 'Requires Review',
    sorted by length of stay (longest first).
    """
    client = get_fhir_client()
    patient_ids = await _get_ward_patient_ids(client)

    candidates = []
    for i, pid in enumerate(patient_ids):
        entry = await _process_patient(pid, client)
        status = entry.get("discharge", {}).get("status", "")
        if status in ("Ready", "Requires Review"):
            candidates.append(entry)
        if i < len(patient_ids) - 1:
            await asyncio.sleep(1.0)

    # Sort by length of stay descending
    candidates.sort(
        key=lambda x: x.get("encounter", {}).get("length_of_stay", 0),
        reverse=True
    )

    # Slim projection to reduce token payload
    slim_candidates = [_slim_summary(c) for c in candidates]

    result = json.dumps({
        "date": date.today().isoformat(),
        "candidate_count": len(slim_candidates),
        "candidates": slim_candidates,
        "dashboard_url": f"{config.DASHBOARD_BASE_URL}/dashboard",
    })

    print(f"\n--- [LOG] Discharge Candidates: {len(slim_candidates)} ---")
    return result


# =====================================================================
# TOOL 4: get_conflict_report
# =====================================================================
@mcp.tool()
async def get_conflict_report() -> str:
    """Get all detected clinical conflicts across the ward.

    Returns patients with active conflicts sorted by severity.
    Includes allergy-medication conflicts, drug interactions,
    missed doses, and note-vs-data contradictions.
    """
    client = get_fhir_client()
    patient_ids = await _get_ward_patient_ids(client)

    conflict_patients = []
    for i, pid in enumerate(patient_ids):
        entry = await _process_patient(pid, client)
        if entry.get("conflict_count", 0) > 0:
            conflict_patients.append(entry)
        if i < len(patient_ids) - 1:
            await asyncio.sleep(1.0)

    # Sort by conflict count descending
    conflict_patients.sort(
        key=lambda x: x.get("conflict_count", 0),
        reverse=True
    )

    total_conflicts = sum(p.get("conflict_count", 0) for p in conflict_patients)

    # Slim projection to reduce token payload
    slim_conflict = [_slim_summary(p) for p in conflict_patients]

    result = json.dumps({
        "date": date.today().isoformat(),
        "patients_with_conflicts": len(slim_conflict),
        "total_conflicts": total_conflicts,
        "patients": slim_conflict,
        "dashboard_url": f"{config.DASHBOARD_BASE_URL}/dashboard",
    })

    print(f"\n--- [LOG] Conflict Report: {total_conflicts} conflicts ---")
    return result


# =====================================================================
# TOOL 5: record_ward_action
# =====================================================================
@mcp.tool()
async def record_ward_action(
    patient_id: str,
    action_type: str,
    detail: str = "",
    conflict_id: str = "",
    clinician: str = "Dr. Mike",
) -> str:
    """Record a clinical action taken by the doctor.

    This is the decision-support layer. It does NOT replace EHR orders.
    It records that a clinician has reviewed and actioned a flagged concern.

    Args:
        patient_id: The FHIR Patient resource ID.
        action_type: One of:
            - conflict_acknowledged: Mark a conflict as reviewed
            - clinical_note_added: Add a clinical response note
            - urgent_review_flagged: Flag patient for immediate bedside review
            - escalation_requested: Request ICU or senior review
            - discharge_approved: Approve discharge
            - discharge_blocked: Block discharge due to new concern
            - pharmacy_review_flagged: Flag medication concern for pharmacist
        detail: Free text note from the clinician explaining the action.
        conflict_id: If acknowledging a specific conflict, its ID.
        clinician: Name of the acting clinician.
    """
    fhir = get_fhir_client()
    action = record_action(
        patient_id=patient_id,
        action_type=action_type,
        detail=detail,
        conflict_id=conflict_id,
        clinician=clinician,
    )

    # PERSISTENCE LAYER: Write back to FHIR for certain action types
    try:
        if action_type in ("clinical_note_added", "conflict_acknowledged"):
            # Create a permanent DocumentReference in FHIR
            note_text = detail if action_type == "clinical_note_added" else f"Acknowledged conflict: {detail}"
            await fhir.create_clinical_note(patient_id, note_text)
            print(f"  [FHIR] Persisted clinical note for {patient_id}")
            
        elif action_type in ("urgent_review_flagged", "escalation_requested"):
            # Create a permanent Flag in FHIR
            flag_code = "URGENT_REVIEW" if action_type == "urgent_review_flagged" else "ESCALATION"
            await fhir.create_safety_flag(patient_id, flag_code, detail)
            print(f"  [FHIR] Persisted safety flag for {patient_id}")
            
        elif action_type in ("discharge_approved", "discharge_blocked"):
            # Create a note regarding discharge decision
            await fhir.create_clinical_note(patient_id, f"DISCHARGE DECISION: {action_type.replace('_', ' ')}. {detail}")
            print(f"  [FHIR] Persisted discharge decision note for {patient_id}")
    except Exception as e:
        print(f"  [FHIR] Warning: Failed to persist to FHIR: {e}")

    # Invalidate cache so new FHIR resources (notes/flags) show up immediately
    _invalidate_cache(patient_id)

    result = json.dumps({
        "status": "recorded",
        "action": action,
        "message": f"Action '{action_type}' recorded and persisted to FHIR for patient {patient_id}",
        "dashboard_url": f"{config.DASHBOARD_BASE_URL}/dashboard/patient/{patient_id}",
    }, indent=2)

    print(f"\n--- [LOG] Action recorded: {action_type} for {patient_id} ---")
    return result


# =====================================================================
# TOOL 6: get_action_history
# =====================================================================
@mcp.tool()
async def get_action_history(patient_id: str) -> str:
    """Get the chronological audit trail of actions taken for a patient.

    Returns a list of all clinical notes, acknowledgements, escalations,
    and status changes recorded by staff.
    """
    actions = get_actions(patient_id)
    # Sort by timestamp ascending (oldest first for timeline)
    actions.sort(key=lambda x: x.get("timestamp", ""))

    result = json.dumps({
        "patient_id": patient_id,
        "action_count": len(actions),
        "history": actions,
        "dashboard_url": f"{config.DASHBOARD_BASE_URL}/dashboard/patient/{patient_id}#timeline",
    }, indent=2)

    print(f"\n--- [LOG] History requested for {patient_id}: {len(actions)} entries ---")
    return result


# =====================================================================
# TOOL 7: get_drug_safety_info
# =====================================================================
@mcp.tool()
async def get_drug_safety_info(drug_name: str, check_interaction_with: str = "") -> str:
    """Look up real FDA safety data for a drug using OpenFDA APIs.

    Returns FDA label warnings, contraindications, and real-world
    adverse event data from the FDA Adverse Event Reporting System (FAERS).

    If check_interaction_with is provided, also returns adverse event
    reports where both drugs appear together.

    Args:
        drug_name: The drug name to look up (e.g. "Amiodarone").
        check_interaction_with: Optional second drug to check combo adverse events.
    """
    from kairosmd.external_apis import (
        get_drug_label, get_adverse_events, get_combo_adverse_events, get_drug_class,
    )

    result = {"drug": drug_name}

    # FDA Label
    label = await get_drug_label(drug_name)
    if label:
        result["fda_label"] = {
            "boxed_warning": label.get("boxed_warning", ""),
            "contraindications": label.get("contraindications", ""),
            "drug_interactions": label.get("drug_interactions", ""),
            "adverse_reactions_summary": label.get("adverse_reactions", "")[:500],
        }
    else:
        result["fda_label"] = None

    # Adverse events
    adverse = await get_adverse_events(drug_name, limit=10)
    if adverse:
        result["adverse_events"] = {
            "total_reports": adverse.get("total_reports", 0),
            "top_reactions": adverse.get("top_adverse_reactions", []),
        }

    # Drug class
    classes = await get_drug_class(drug_name)
    if classes:
        result["drug_classes"] = classes

    # Combo check
    if check_interaction_with:
        combo = await get_combo_adverse_events(drug_name, check_interaction_with)
        if combo:
            result["interaction_evidence"] = {
                "with": check_interaction_with,
                "total_combo_reports": combo.get("total_combo_reports", 0),
                "top_reactions_together": combo.get("top_reactions_together", []),
            }

    result["dashboard_url"] = f"{config.DASHBOARD_BASE_URL}/dashboard"
    output = json.dumps(result, indent=2)
    print(f"\n--- [LOG] Drug safety lookup: {drug_name} ---")
    return output


# =====================================================================
# TOOL 8: get_dashboard_access
# =====================================================================
@mcp.tool()
async def get_dashboard_access() -> str:
    """Get direct links to the visual clinical dashboards.

    Use this when the user specifically asks to 'open the dashboard',
    'show me the board', or 'give me the full view'.
    """
    return json.dumps({
        "main_ward_board": f"{config.DASHBOARD_BASE_URL}/dashboard",
        "dashboard_url": f"{config.DASHBOARD_BASE_URL}/dashboard",
        "message": "Click the link above to open the visual clinical interface."
    }, indent=2)


# =====================================================================
# TOOL 9: apply_suggested_plan
# =====================================================================
@mcp.tool()
async def apply_suggested_plan(
    patient_id: str,
    plan_text: str,
    clinician: str = "Dr. Mike",
) -> str:
    """Apply the AI-suggested plan adjustments to the patient's clinical notes.

    This tool takes a suggested plan (usually from the briefing) and 
    persists it as a signed clinical note in the FHIR record.

    Args:
        patient_id: The FHIR Patient resource ID.
        plan_text: The plan text to add to the notes.
        clinician: Name of the acting clinician.
    """
    return await record_ward_action(
        patient_id=patient_id,
        action_type="clinical_note_added",
        detail=f"Applied Suggested Plan: {plan_text}",
        clinician=clinician
    )


# -- Entry point -------------------------------------------------------
def main():
    import sys
    import threading
    import time
    import os
    import uvicorn
    from starlette.responses import JSONResponse
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware

    def background_warmer():
        # Wait for the server to be fully up
        time.sleep(2)
        asyncio.run(warm_cache())

    # Load existing cache from disk immediately
    _load_persistent_cache()

    # Start warming in a background thread so it doesn't block mcp.run()
    threading.Thread(target=background_warmer, daemon=True).start()

    if "--sse" in sys.argv:
        port = int(os.getenv("PORT", 8000))
        
        async def health_check(request):
            return JSONResponse({
                "status": "healthy", 
                "service": "KairosMD",
                "cache_size": len(_patient_cache)
            })

        # Add CORS middleware to allow any client to connect
        middleware = [
            Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        ]
        
        app = mcp.sse_app()
        # Note: We wrap the app or add middleware to the existing Starlette app
        app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        app.add_route("/", health_check)
        
        print(f"Starting KairosMD MDS SSE on 0.0.0.0:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port, timeout_keep_alive=60)
    else:
        # If no arguments, we still want to default to SSE on cloud platforms
        if os.getenv("PORT"):
            print("PORT environment variable detected. Defaulting to SSE transport...")
            # Re-call main with --sse simulated
            sys.argv.append("--sse")
            main()
        else:
            mcp.run()
