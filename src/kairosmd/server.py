"""KairosMD MCP Server - Ward Round Decision Support.

Exposes 5 MCP tools:
  1. get_ward_round_summary  - Full ward overview sorted by priority
  2. get_patient_ward_detail - Deep dive into single patient
  3. get_discharge_candidates - Patients ready or near-ready for discharge
  4. get_conflict_report     - All detected conflicts across the ward
  5. record_ward_action      - Record clinical actions (acknowledge, escalate, etc.)
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

mcp = FastMCP("KairosMD")
fhir = FHIRClient()

# Priority sort order for ward round
PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

# -- Server-side cache -------------------------------------------------
# Caches FHIR + ward engine + LLM results per patient.
# Actions are always re-attached fresh (they're in-memory, instant).
import time

CACHE_TTL = 3600  # 1 hour
_patient_cache: dict[str, tuple[float, dict]] = {}  # pid -> (timestamp, data)


def _get_cached(pid: str) -> dict | None:
    """Return cached patient data if still fresh."""
    entry = _patient_cache.get(pid)
    if entry and (time.time() - entry[0]) < CACHE_TTL:
        return entry[1]
    return None


def _set_cached(pid: str, data: dict):
    """Store patient data in cache."""
    _patient_cache[pid] = (time.time(), data)


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
        given = " ".join(name_parts.get("given", [""]))
        family = name_parts.get("family", "")
        name = f"{given} {family}".strip() or "Unknown"
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

        # Run ward engine
        result = await compile_patient_ward_data(
            vitals, labs, notes, conditions, medications,
            allergies, med_admins, flags, encounter,
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
        }


# -- Helper: get all ward patient IDs ---------------------------------
async def _get_ward_patient_ids(fhir: FHIRClient) -> list[str]:
    """Get all patient IDs from active inpatient encounters."""
    encounters = await fhir.get_encounters()
    patient_ids = []
    for enc in encounters:
        ref = enc.get("subject", {}).get("reference", "")
        if ref.startswith("Patient/"):
            pid = ref.split("/")[1]
            if pid not in patient_ids:
                patient_ids.append(pid)
    return patient_ids


# -- Helper: sort ward results ----------------------------------------
def _sort_ward_list(triage_list: list[dict]) -> list[dict]:
    """Sort by: NEWS2 HIGH > has conflicts > MEDIUM > LOW."""
    def sort_key(entry):
        priority = PRIORITY_ORDER.get(entry.get("priority", "LOW"), 2)
        has_conflicts = 0 if entry.get("conflict_count", 0) > 0 else 1
        news2 = -(entry.get("news2", {}).get("total_score", 0))
        return (priority, has_conflicts, news2)
    return sorted(triage_list, key=sort_key)


# =====================================================================
# TOOL 1: get_ward_round_summary
# =====================================================================
@mcp.tool()
async def get_ward_round_summary() -> str:
    """Get the morning ward round summary for all inpatient patients.

    Returns a prioritised list of all patients on the ward with:
    - NEWS2 score and risk level
    - Overnight change detection
    - Conflict alerts
    - Discharge readiness
    - AI-generated clinical briefing

    Sorted by clinical priority (high risk first, discharge ready last).
    """
    patient_ids = (await _get_ward_patient_ids(fhir))[:2]

    if not patient_ids:
        return json.dumps({
            "error": "No active inpatient encounters found",
            "dashboard_url": "/dashboard",
        })

    # Process patients sequentially with rate limiting
    ward_list = []
    for i, pid in enumerate(patient_ids):
        print(f"  Processing patient {i+1}/{len(patient_ids)} ({pid})...")
        entry = await _process_patient(pid, fhir)
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

    result = json.dumps({
        "ward": "General Medicine Ward 4",
        "date": date.today().isoformat(),
        "total_patients": len(ward_list),
        "high_risk_count": high_risk,
        "medium_risk_count": medium_risk,
        "active_conflicts": conflicts_total,
        "discharge_candidates": discharge_ready,
        "patients": ward_list,
        "dashboard_url": "/dashboard",
    }, indent=2)

    print(f"\n--- [LOG] Ward Round Summary: {len(ward_list)} patients ---")
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
    entry = await _process_patient(patient_id, fhir)
    entry["dashboard_url"] = f"/dashboard/patient/{patient_id}"

    result = json.dumps(entry, indent=2)
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
    patient_ids = (await _get_ward_patient_ids(fhir))[:2]

    candidates = []
    for i, pid in enumerate(patient_ids):
        entry = await _process_patient(pid, fhir)
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

    result = json.dumps({
        "date": date.today().isoformat(),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "dashboard_url": "/dashboard/discharge",
    }, indent=2)

    print(f"\n--- [LOG] Discharge Candidates: {len(candidates)} ---")
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
    patient_ids = (await _get_ward_patient_ids(fhir))[:2]

    conflict_patients = []
    for i, pid in enumerate(patient_ids):
        entry = await _process_patient(pid, fhir)
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

    result = json.dumps({
        "date": date.today().isoformat(),
        "patients_with_conflicts": len(conflict_patients),
        "total_conflicts": total_conflicts,
        "patients": conflict_patients,
        "dashboard_url": "/dashboard/conflicts",
    }, indent=2)

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
    """
    action = record_action(
        patient_id=patient_id,
        action_type=action_type,
        detail=detail,
        conflict_id=conflict_id,
    )

    result = json.dumps({
        "status": "recorded",
        "action": action,
        "message": f"Action '{action_type}' recorded for patient {patient_id}",
    }, indent=2)

    print(f"\n--- [LOG] Action recorded: {action_type} for {patient_id} ---")
    return result


# -- Entry point -------------------------------------------------------
def main():
    import sys
    if "--sse" in sys.argv:
        print("Starting KairosMD in SSE mode (default port 8000)")
        mcp.run(transport="sse")
    else:
        mcp.run()
