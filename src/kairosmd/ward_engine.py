"""Ward round orchestration engine.

Compiles all clinical data for a patient, runs NEWS2, conflict detection,
discharge assessment, and overnight trend analysis. Returns a unified
patient summary dict ready for LLM briefing and dashboard display.
"""

from __future__ import annotations
import base64
from datetime import datetime, timezone

from kairosmd.news2 import calculate_news2_from_observations, extract_latest_vitals
from kairosmd.conflict_detector import detect_all_conflicts
from kairosmd.discharge_assessor import assess_discharge_readiness
from kairosmd.vitals_rules import flag_vitals
from kairosmd.labs_rules import flag_labs


# -- Priority sorting order --------------------------------------------
PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _extract_note_text(doc_refs: list[dict]) -> list[dict]:
    """Extract text and metadata from DocumentReference resources."""
    results = []
    for doc in doc_refs:
        text = ""
        for content in doc.get("content", []):
            att = content.get("attachment", {})
            if att.get("data"):
                try:
                    text = base64.b64decode(att["data"]).decode("utf-8", errors="replace")
                except Exception:
                    pass
        if not text and doc.get("description"):
            text = doc.get("description", "")
        results.append({
            "type": doc.get("type", {}).get("text", "Note"),
            "date": doc.get("date", ""),
            "text": text,
        })
    return results


def _detect_overnight_trends(vitals_obs: list[dict]) -> list[dict]:
    """Compare vitals over 24h and flag improving/stable/deteriorating."""
    # Group by LOINC code, sort by time
    by_code: dict[str, list[tuple[str, float]]] = {}
    for obs in vitals_obs:
        codings = obs.get("code", {}).get("coding", [])
        loinc = ""
        display = ""
        for c in codings:
            if c.get("system") == "http://loinc.org":
                loinc = c.get("code", "")
                display = c.get("display", loinc)
        val = obs.get("valueQuantity", {}).get("value")
        dt = obs.get("effectiveDateTime", "")
        if loinc and val is not None:
            by_code.setdefault(loinc, []).append((dt, float(val), display))

    trends = []
    for loinc, readings in by_code.items():
        if len(readings) < 2:
            continue
        readings.sort(key=lambda x: x[0])
        oldest_val = readings[0][1]
        newest_val = readings[-1][1]
        display = readings[0][2]
        diff = newest_val - oldest_val
        pct = abs(diff / oldest_val * 100) if oldest_val != 0 else 0

        if pct < 5:
            direction = "stable"
        elif diff > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        # Determine if the trend is clinically concerning
        concerning = False
        # SpO2 decreasing is bad
        if loinc == "2708-6" and direction == "decreasing" and pct > 5:
            concerning = True
        # HR or RR increasing is bad
        elif loinc in ("8867-4", "9279-1") and direction == "increasing" and pct > 10:
            concerning = True
        # SBP decreasing is bad
        elif loinc == "8480-6" and direction == "decreasing" and pct > 10:
            concerning = True
        # Temp increasing is bad
        elif loinc == "8310-5" and direction == "increasing" and newest_val > 38.0:
            concerning = True
        # GCS decreasing is bad
        elif loinc == "9269-2" and direction == "decreasing":
            concerning = True

        trends.append({
            "parameter": display,
            "loinc": loinc,
            "oldest": oldest_val,
            "newest": newest_val,
            "direction": direction,
            "change_pct": round(pct, 1),
            "concerning": concerning,
        })

    return trends


def _detect_lab_trends(labs_obs: list[dict]) -> list[dict]:
    """Compare lab values over time and flag changes."""
    by_code: dict[str, list[tuple[str, float, str]]] = {}
    for obs in labs_obs:
        codings = obs.get("code", {}).get("coding", [])
        loinc = ""
        display = ""
        for c in codings:
            if c.get("system") == "http://loinc.org":
                loinc = c.get("code", "")
                display = c.get("display", loinc)
        val = obs.get("valueQuantity", {}).get("value")
        dt = obs.get("effectiveDateTime", "")
        if loinc and val is not None:
            by_code.setdefault(loinc, []).append((dt, float(val), display))

    trends = []
    for loinc, readings in by_code.items():
        if len(readings) < 2:
            continue
        readings.sort(key=lambda x: x[0])
        oldest_val = readings[0][1]
        newest_val = readings[-1][1]
        display = readings[0][2]

        diff = newest_val - oldest_val
        if oldest_val != 0:
            direction = "increasing" if diff > 0 else ("decreasing" if diff < 0 else "stable")
        else:
            direction = "stable"

        trends.append({
            "parameter": display, "loinc": loinc,
            "oldest": oldest_val, "newest": newest_val,
            "direction": direction,
        })

    return trends


def _calc_length_of_stay(encounter: dict | None) -> int:
    """Calculate length of stay in days from encounter period."""
    if not encounter:
        return 0
    start = encounter.get("period", {}).get("start", "")
    if not start:
        return 0
    try:
        admit_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        return max(1, (datetime.now(timezone.utc) - admit_dt).days)
    except Exception:
        return 0


def _get_encounter_info(encounter: dict | None) -> dict:
    """Extract ward, bed, and admission info from Encounter."""
    if not encounter:
        return {"ward": "Unknown", "bed": "Unknown", "admission_date": "", "length_of_stay": 0}
    location = ""
    for loc in encounter.get("location", []):
        location = loc.get("location", {}).get("display", "")
    parts = location.split(" - ") if location else ["Unknown", "Unknown"]
    ward = parts[0] if len(parts) > 0 else "Unknown"
    bed = parts[1] if len(parts) > 1 else "Unknown"

    return {
        "ward": ward,
        "bed": bed,
        "admission_date": encounter.get("period", {}).get("start", ""),
        "admitting_diagnosis": encounter.get("reasonCode", [{}])[0].get("text", ""),
        "length_of_stay": _calc_length_of_stay(encounter),
    }


async def compile_patient_ward_data(
    vitals: list[dict],
    labs: list[dict],
    notes: list[dict],
    conditions: list[dict],
    medications: list[dict],
    allergies: list[dict],
    med_admins: list[dict],
    flags: list[dict],
    encounter: dict | None = None,
) -> dict:
    """Compile all ward round analysis for a single patient.

    Returns a dict with NEWS2, conflicts, discharge status, trends, and notes.
    """
    # 1. NEWS2
    news2 = calculate_news2_from_observations(vitals)

    # 2. Conflicts
    conflicts = detect_all_conflicts(medications, allergies, med_admins, notes, vitals)

    # 3. Discharge readiness
    discharge = assess_discharge_readiness(
        vitals, labs, medications, notes, flags, news2["total_score"], encounter
    )

    # 4. Overnight vital trends
    vital_trends = _detect_overnight_trends(vitals)
    lab_trends = _detect_lab_trends(labs)

    # 5. Flagged vitals and labs (existing rule engine)
    flagged_vitals = flag_vitals(vitals)
    flagged_labs = flag_labs(labs)

    # 6. Extract note texts
    parsed_notes = _extract_note_text(notes)

    # 7. Encounter info
    enc_info = _get_encounter_info(encounter)

    # 8. Active conditions
    condition_names = []
    for cond in conditions:
        name = cond.get("code", {}).get("text", "")
        if not name:
            codings = cond.get("code", {}).get("coding", [])
            name = codings[0].get("display", "Unknown") if codings else "Unknown"
        condition_names.append(name)

    # 9. Safety flags
    safety_flags = []
    for f in flags:
        safety_flags.append(f.get("code", {}).get("text", ""))

    return {
        "encounter": enc_info,
        "news2": news2,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
        "discharge": discharge,
        "vital_trends": vital_trends,
        "lab_trends": lab_trends,
        "flagged_vitals": flagged_vitals,
        "flagged_labs": flagged_labs,
        "active_conditions": condition_names,
        "clinical_notes": parsed_notes,
        "safety_flags": safety_flags,
        "priority": news2["risk_level"],
    }
