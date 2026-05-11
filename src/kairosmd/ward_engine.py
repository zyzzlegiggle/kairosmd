"""Ward round orchestration engine.

Compiles all clinical data for a patient, runs NEWS2, conflict detection,
discharge assessment, and overnight trend analysis. Returns a unified
patient summary dict ready for LLM briefing and dashboard display.
"""

from __future__ import annotations
import asyncio
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
            "author": doc.get("author", [{}])[0].get("display", "Unknown Clinician"),
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
            "history": [{"time": r[0], "value": r[1]} for r in readings],
        })

    return trends


LAB_DISPLAY_MAP = {
    "6299-1": "WBC",
    "1988-5": "CRP",
    "2019-8": "Lactate",
    "2160-0": "Creatinine",
    "33914-3": "eGFR",
    "30522-7": "BNP",
    "2823-3": "Potassium",
    "2028-9": "CO2",
    "20570-8": "HbA1c",
    "2276-4": "Ferritin",
    "718-7": "Hemoglobin",
    "2345-7": "Glucose",
    "4544-3": "HbA1c",
}


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
                display = c.get("display") or LAB_DISPLAY_MAP.get(loinc, loinc)
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
            "history": [{"time": r[0], "value": r[1]} for r in readings],
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
    care_team: list[dict] | None = None,
    communications: list[dict] | None = None,
    diag_reports: list[dict] | None = None,
    encounter: dict | None = None,
) -> dict:
    """Compile all ward round analysis for a single patient.

    Returns a dict with NEWS2, conflicts, discharge status, trends, and notes.
    """
    # 1. NEWS2
    news2 = calculate_news2_from_observations(vitals)

    # 2. Conflicts (local rule engine)
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
    condition_names = [cond.get("code", {}).get("text", "") or 
                       cond.get("code", {}).get("coding", [{}])[0].get("display", "Unknown") 
                       for cond in conditions]

    # 9. Safety flags (with detail)
    safety_flags = []
    for f in flags:
        text = f.get("code", {}).get("text", "Unknown Flag")
        safety_flags.append(text)

    # 10. Care Team & Consultant
    team_members = []
    responsible_consultant = "Unassigned"
    if care_team:
        for ct in care_team:
            for part in ct.get("participant", []):
                name = part.get("member", {}).get("display", "Unknown")
                role = part.get("role", [{}])[0].get("text", "Member")
                team_members.append({"name": name, "role": role})
                if "Consultant" in role:
                    responsible_consultant = name

    # 11. Audit Trail (Communications)
    audit_trail = []
    if communications:
        for c in communications:
            audit_trail.append({
                "date": c.get("sent", ""),
                "from": c.get("sender", {}).get("display", "Unknown"),
                "to": c.get("recipient", [{}])[0].get("display", "Team"),
                "message": c.get("payload", [{}])[0].get("contentString", "")
            })

    # 12. Diagnostic Reports
    diagnostic_conclusions = []
    if diag_reports:
        for dr in diag_reports:
            diagnostic_conclusions.append({
                "test": dr.get("code", {}).get("text", "Report"),
                "conclusion": dr.get("conclusion", ""),
                "date": dr.get("effectiveDateTime", "")
            })

    # 13. FDA Safety Enrichment
    fda_safety = await _enrich_with_fda_data(medications, conflicts)

    # 14. Normalize active medications for dashboard display
    active_meds = []
    for med in medications:
        name = med.get("medicationCodeableConcept", {}).get("text", "")
        if not name:
            codings = med.get("medicationCodeableConcept", {}).get("coding", [])
            name = codings[0].get("display", "Unknown") if codings else "Unknown"
        dosage_list = med.get("dosageInstruction", [])
        dosage = dosage_list[0].get("text", "") if dosage_list else ""
        active_meds.append({
            "name": name,
            "dosage": dosage,
            "status": med.get("status", "active"),
            "code": med.get("medicationCodeableConcept", {}).get("coding", [{}])[0].get("code", ""),
        })

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
        "active_medications": active_meds,
        "allergies": [{"name": a.get("code", {}).get("text", ""), "criticality": a.get("criticality", "low")} for a in allergies],
        "care_team": team_members,
        "consultant": responsible_consultant,
        "audit_trail": audit_trail,
        "diagnostic_reports": diagnostic_conclusions,
        "priority": news2["risk_level"],
        "fda_safety": fda_safety,
    }


async def _enrich_with_fda_data(medications: list[dict], conflicts: list[dict]) -> dict:
    """Fetch real FDA data for medications and drug interaction conflicts.
    
    Non-blocking: if OpenFDA is slow or down, returns empty gracefully.
    """
    from kairosmd.external_apis import get_drug_label, get_combo_adverse_events
    
    fda_data = {"drug_warnings": [], "interaction_evidence": []}

    try:
        # Get FDA warnings for each unique active medication
        seen_meds = set()
        med_names = []
        for med in medications:
            name = med.get("medicationCodeableConcept", {}).get("text", "")
            if name:
                base = name.split()[0].replace(",", "").replace(";", "") # Clean up common separators
                if base not in seen_meds:
                    med_names.append(base)
                    seen_meds.add(base)

        # Fetch labels (with rate limiting)
        for name in med_names[:6]:  # Cap at 6 to avoid API overload
            label = await get_drug_label(name)
            if label and (label.get("boxed_warning") or label.get("contraindications")):
                fda_data["drug_warnings"].append({
                    "drug": name,
                    "boxed_warning": bool(label.get("boxed_warning")),
                    "has_contraindications": bool(label.get("contraindications")),
                    "interaction_warnings": label.get("drug_interactions", "")[:300],
                })
            await asyncio.sleep(0.15)

        # For detected drug interactions, get real-world adverse event evidence
        for conflict in conflicts:
            if conflict.get("type") == "drug_drug_interaction":
                drugs = conflict.get("drugs", [])
                if len(drugs) >= 2:
                    combo = await get_combo_adverse_events(drugs[0], drugs[1])
                    if combo and combo.get("total_combo_reports", 0) > 0:
                        fda_data["interaction_evidence"].append({
                            "drugs": drugs,
                            "fda_reports": combo["total_combo_reports"],
                            "top_reactions": [r["reaction"] for r in combo.get("top_reactions_together", [])[:3]],
                        })
                    await asyncio.sleep(0.15)

    except Exception as e:
        fda_data["api_error"] = str(e)

    return fda_data
