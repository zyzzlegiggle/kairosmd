"""KairosMD - Clinical Triage MCP Server.

Exposes six tools over the Model Context Protocol so an LLM agent can
fetch, assess, and prioritise a doctor's patient list in real-time.

Run in dev mode :  uv run mcp dev src/kairosmd/server.py
Run in prod     :  uv run mcp run src/kairosmd/server.py
"""

from __future__ import annotations
import json
from datetime import date

from mcp.server.fastmcp import FastMCP

from kairosmd.fhir_client import FHIRClient
from kairosmd.vitals_rules import flag_vitals
from kairosmd.labs_rules import flag_labs
from kairosmd.risk_engine import score_patient, extract_note_text
from kairosmd import config

# -- Initialise MCP server and shared FHIR client ---------------------
mcp = FastMCP("KairosMD")

fhir = FHIRClient()


# -- Helpers -----------------------------------------------------------
def _patient_summary(pt: dict) -> dict:
    """Flatten a FHIR Patient resource into a compact dict."""
    names = pt.get("name", [{}])
    name_parts = names[0] if names else {}
    given = " ".join(name_parts.get("given", []))
    family = name_parts.get("family", "")
    return {
        "id": pt.get("id"),
        "name": f"{given} {family}".strip(),
        "gender": pt.get("gender", "unknown"),
        "birthDate": pt.get("birthDate", ""),
    }


def _appointment_summary(appt: dict) -> dict:
    """Flatten a FHIR Appointment into a compact dict."""
    patient_id = None
    for participant in appt.get("participant", []):
        ref = participant.get("actor", {}).get("reference", "")
        if ref.startswith("Patient/"):
            patient_id = ref.split("/")[1]
            break
    return {
        "appointment_id": appt.get("id"),
        "status": appt.get("status", ""),
        "start": appt.get("start", ""),
        "end": appt.get("end", ""),
        "patient_id": patient_id,
        "description": appt.get("description", ""),
        "service_type": _extract_text(appt.get("serviceType", [])),
    }


def _extract_text(coding_list: list[dict]) -> str:
    for item in coding_list:
        if isinstance(item, dict):
            text = item.get("text")
            if text:
                return text
            for c in item.get("coding", []):
                if c.get("display"):
                    return c["display"]
    return ""


# =====================================================================
#  TOOL 1 - get_ward_patients
# =====================================================================
@mcp.tool()
async def get_ward_patients(
    practitioner_id: str | None = None,
    target_date: str | None = None,
) -> str:
    """Fetch all patients scheduled for a doctor on a given date.

    Returns the appointment list sorted by start time, with basic
    patient demographics.  Defaults to today if no date supplied.

    Args:
        practitioner_id: FHIR Practitioner resource ID. Falls back to
            DEFAULT_PRACTITIONER_ID env var.
        target_date: ISO date string (YYYY-MM-DD). Defaults to today.
    """
    prac_id = practitioner_id or config.DEFAULT_PRACTITIONER_ID
    if not prac_id:
        return json.dumps({"error": "practitioner_id is required"})

    appts = await fhir.get_appointments(prac_id, target_date)
    if not appts:
        return json.dumps({
            "practitioner_id": prac_id,
            "date": target_date or date.today().isoformat(),
            "patient_count": 0,
            "patients": [],
            "note": "No appointments found. Run the seed script first if using the HAPI test server.",
        })

    # collect patient IDs and fetch demographics
    summaries = [_appointment_summary(a) for a in appts]
    patient_ids = list({s["patient_id"] for s in summaries if s["patient_id"]})
    patients_raw = await fhir.get_patients_batch(patient_ids)
    patients_map = {p["id"]: _patient_summary(p) for p in patients_raw}

    roster: list[dict] = []
    for s in summaries:
        pid = s["patient_id"]
        entry = {**s, "patient": patients_map.get(pid, {})}
        roster.append(entry)

    roster.sort(key=lambda x: x.get("start", ""))

    return json.dumps({
        "practitioner_id": prac_id,
        "date": target_date or date.today().isoformat(),
        "patient_count": len(roster),
        "patients": roster,
    }, indent=2)


# =====================================================================
#  TOOL 2 - get_patient_vitals
# =====================================================================
@mcp.tool()
async def get_patient_vitals(patient_id: str) -> str:
    """Pull the latest vital signs for a patient, with abnormal flags.

    Returns each vital reading with severity (normal / abnormal / critical)
    and a human-readable explanation.

    Args:
        patient_id: FHIR Patient resource ID.
    """
    obs = await fhir.get_vitals(patient_id)
    flagged = flag_vitals(obs)
    return json.dumps({
        "patient_id": patient_id,
        "total_readings": len(flagged),
        "vitals": flagged,
    }, indent=2)


# =====================================================================
#  TOOL 3 - get_lab_results
# =====================================================================
@mcp.tool()
async def get_lab_results(patient_id: str) -> str:
    """Fetch recent laboratory values for a patient, flagging abnormals.

    Returns each lab result with severity and explanation.

    Args:
        patient_id: FHIR Patient resource ID.
    """
    obs = await fhir.get_labs(patient_id)
    flagged = flag_labs(obs)
    return json.dumps({
        "patient_id": patient_id,
        "total_results": len(flagged),
        "labs": flagged,
    }, indent=2)


# =====================================================================
#  TOOL 4 - get_clinical_notes
# =====================================================================
@mcp.tool()
async def get_clinical_notes(patient_id: str) -> str:
    """Pull nursing/doctor notes for a patient.

    Returns raw note text extracted from FHIR DocumentReference resources.

    Args:
        patient_id: FHIR Patient resource ID.
    """
    docs = await fhir.get_clinical_notes(patient_id)
    text = extract_note_text(docs)
    return json.dumps({
        "patient_id": patient_id,
        "note_count": len(docs),
        "notes_text": text if text else "No clinical notes found.",
    }, indent=2)


# =====================================================================
#  TOOL 5 - analyze_patient_risk
# =====================================================================
@mcp.tool()
async def analyze_patient_risk(patient_id: str) -> str:
    """Score a single patient by clinical urgency (0-100).

    Combines abnormal vitals, critical labs, LLM analysis of clinical
    notes, active chronic conditions, and time since last review.

    Returns the risk score, band (CRITICAL / HIGH / MODERATE / LOW),
    and a list of reasons explaining the score.

    Args:
        patient_id: FHIR Patient resource ID.
    """
    vitals = await fhir.get_vitals(patient_id)
    labs = await fhir.get_labs(patient_id)
    notes = await fhir.get_clinical_notes(patient_id)
    conditions = await fhir.get_conditions(patient_id)

    result = await score_patient(vitals, labs, notes, conditions)

    patient = {}
    try:
        patient = _patient_summary(await fhir.get_patient(patient_id))
    except Exception:
        pass

    return json.dumps({
        "patient_id": patient_id,
        "patient": patient,
        **result,
    }, indent=2)


# =====================================================================
#  TOOL 6 - generate_priority_list
# =====================================================================
@mcp.tool()
async def generate_priority_list(
    practitioner_id: str | None = None,
    target_date: str | None = None,
) -> str:
    """Generate a priority-ranked patient list for the doctor's day.

    This is the main orchestration tool.  It:
    1. Fetches today's scheduled patients (sorted by appointment time).
    2. Runs risk scoring on every patient (vitals + labs + notes + conditions).
    3. Returns a combined list: scheduled order + priority overlay.

    The response includes both the chronological schedule and a
    priority-ranked view so the doctor sees who needs attention first.

    Args:
        practitioner_id: FHIR Practitioner resource ID.
        target_date: ISO date (YYYY-MM-DD). Defaults to today.
    """
    prac_id = practitioner_id or config.DEFAULT_PRACTITIONER_ID
    if not prac_id:
        return json.dumps({"error": "practitioner_id is required"})

    # 1. get appointments
    appts = await fhir.get_appointments(prac_id, target_date)
    if not appts:
        return json.dumps({
            "practitioner_id": prac_id,
            "date": target_date or date.today().isoformat(),
            "patient_count": 0,
            "schedule": [],
            "priority_list": [],
            "note": "No appointments found.",
        })

    appt_summaries = [_appointment_summary(a) for a in appts]
    patient_ids = list({s["patient_id"] for s in appt_summaries if s["patient_id"]})

    # 2. fetch demographics
    patients_raw = await fhir.get_patients_batch(patient_ids)
    patients_map = {p["id"]: _patient_summary(p) for p in patients_raw}

    # 3. score every patient
    scored: list[dict] = []
    for pid in patient_ids:
        vitals = await fhir.get_vitals(pid)
        labs = await fhir.get_labs(pid)
        notes = await fhir.get_clinical_notes(pid)
        conditions = await fhir.get_conditions(pid)
        risk = await score_patient(vitals, labs, notes, conditions)

        # find appointment time
        appt_time = ""
        for a in appt_summaries:
            if a["patient_id"] == pid:
                appt_time = a.get("start", "")
                break

        scored.append({
            "patient_id": pid,
            "patient": patients_map.get(pid, {}),
            "appointment_time": appt_time,
            **risk,
        })

    # chronological schedule
    schedule = sorted(scored, key=lambda x: x.get("appointment_time", ""))

    # priority-ranked (highest risk first)
    priority = sorted(scored, key=lambda x: x.get("risk_score", 0), reverse=True)

    return json.dumps({
        "practitioner_id": prac_id,
        "date": target_date or date.today().isoformat(),
        "patient_count": len(scored),
        "schedule": schedule,
        "priority_list": priority,
    }, indent=2)


# -- Entry point -------------------------------------------------------
def main():
    import os
    import sys
    
    # Check for SSE mode via flag or env var
    if "--sse" in sys.argv or os.getenv("MCP_TRANSPORT") == "sse":
        print("Starting KairosMD in SSE mode (default port 8000)")
        # Note: In this version of FastMCP, host/port are handled internally 
        # or via CLI if run via 'mcp run'. Calling .run(transport='sse') 
        # starts the built-in server.
        mcp.run(transport="sse")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
