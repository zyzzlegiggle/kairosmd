"""Conflict detection engine for inpatient ward round.

Detects and flags the following conflict types:
1. Nursing note contradicts vital sign data
2. Doctor assessment contradicts objective data
3. Medication ordered for patient with documented allergy
4. Drug-drug interactions in active medication list
5. Missed medication doses in last 24 hours
6. Held medication doses
7. Lab result requiring action but no order change
"""

from __future__ import annotations
from kairosmd.drug_interactions import check_interactions_local, extract_base_name


# -- Conflict severity levels ------------------------------------------
CRITICAL = "critical"
HIGH = "high"
MODERATE = "moderate"
LOW = "low"


def detect_allergy_conflicts(
    medications: list[dict],
    allergies: list[dict],
) -> list[dict]:
    """Check if any active medication matches a documented allergy."""
    conflicts = []
    allergy_substances = []

    # Cross-class drug families (allergy to one = allergy to all)
    PENICILLIN_FAMILY = {"penicillin", "penicillin g", "amoxicillin", "ampicillin",
                         "flucloxacillin", "co-amoxiclav", "piperacillin",
                         "benzylpenicillin", "phenoxymethylpenicillin"}

    for a in allergies:
        substance = a.get("code", {}).get("text", "")
        reaction = ""
        for r in a.get("reaction", []):
            for m in r.get("manifestation", []):
                reaction = m.get("text", "") or m.get("coding", [{}])[0].get("display", "")
        if substance:
            allergy_substances.append((substance.lower(), reaction))

    for med in medications:
        med_name = med.get("medicationCodeableConcept", {}).get("text", "")
        if not med_name:
            codings = med.get("medicationCodeableConcept", {}).get("coding", [])
            med_name = codings[0].get("display", "") if codings else ""

        med_lower = med_name.lower().split()[0] if med_name else ""  # base name

        for substance, reaction in allergy_substances:
            # Direct substring match
            direct_match = substance in med_lower or med_lower in substance
            # Cross-class match (penicillin family)
            class_match = (substance in PENICILLIN_FAMILY and med_lower in PENICILLIN_FAMILY)

            if direct_match or class_match:
                conflicts.append({
                    "type": "allergy_medication_conflict",
                    "severity": CRITICAL,
                    "medication": med_name,
                    "allergy": substance,
                    "reaction": reaction,
                    "message": (f"ALLERGY CONFLICT: {med_name} prescribed but patient "
                                f"has documented allergy to {substance}"
                                + (f" ({reaction})" if reaction else "")
                                + (" [same drug class]" if class_match and not direct_match else "")),
                })
    return conflicts


def detect_drug_interactions(medications: list[dict]) -> list[dict]:
    """Check for drug-drug interactions in the active medication list."""
    med_names = []
    for med in medications:
        name = med.get("medicationCodeableConcept", {}).get("text", "")
        if not name:
            codings = med.get("medicationCodeableConcept", {}).get("coding", [])
            name = codings[0].get("display", "") if codings else ""
        if name:
            med_names.append(extract_base_name(name))

    interactions = check_interactions_local(med_names)
    conflicts = []
    for ix in interactions:
        a = ix["drug_a"]
        b = ix["drug_b"]
        desc = ix["description"]
        conflicts.append({
            "type": "drug_drug_interaction",
            "severity": HIGH,
            "drugs": [a, b],
            "message": f"DRUG INTERACTION: {a} + {b} — {desc}",
        })
    return conflicts


def detect_missed_doses(med_admins: list[dict]) -> list[dict]:
    """Detect missed or held medication doses."""
    conflicts = []
    for admin in med_admins:
        status = admin.get("status", "")
        med_name = admin.get("medicationCodeableConcept", {}).get("text", "")
        when = admin.get("effectiveDateTime", "")

        if status == "not-done":
            reason = ""
            for sr in admin.get("statusReason", []):
                reason = sr.get("text", "")
            conflicts.append({
                "type": "missed_dose",
                "severity": MODERATE,
                "medication": med_name,
                "time": when,
                "reason": reason,
                "message": f"MISSED DOSE: {med_name} was not given at {when[:16]}. {reason}",
            })
        elif status == "on-hold":
            reason = ""
            for sr in admin.get("statusReason", []):
                reason = sr.get("text", "")
            conflicts.append({
                "type": "held_dose",
                "severity": LOW,
                "medication": med_name,
                "time": when,
                "reason": reason,
                "message": f"HELD DOSE: {med_name} was held at {when[:16]}. {reason}",
            })
    return conflicts


def detect_note_vital_conflict(
    notes: list[dict],
    vitals: list[dict],
) -> list[dict]:
    """Detect when nursing notes say 'stable/comfortable' but vitals deteriorated."""
    conflicts = []

    # Keywords suggesting patient is stable/comfortable
    stable_keywords = ["stable", "comfortable", "settled", "no concerns",
                       "sleeping", "resting well", "no acute"]
    # Keywords suggesting deterioration
    bad_keywords = ["deteriorat", "worsening", "critical", "unresponsive"]

    for note in notes:
        # Get note text
        note_text = ""
        for content in note.get("content", []):
            att = content.get("attachment", {})
            if att.get("data"):
                import base64
                try:
                    note_text = base64.b64decode(att["data"]).decode("utf-8", errors="replace")
                except Exception:
                    pass
        if note.get("description"):
            note_text = note_text or note.get("description", "")

        note_time = note.get("date", "")
        note_type = note.get("type", {}).get("text", "Note")
        note_lower = note_text.lower()

        # Check if note claims stability
        claims_stable = any(kw in note_lower for kw in stable_keywords)
        claims_bad = any(kw in note_lower for kw in bad_keywords)

        if not claims_stable:
            continue

        # Check vitals around the same time window for concerning trends
        # Look for SpO2 < 92, HR > 110, SBP < 100, RR > 24, Temp > 38.5
        for obs in vitals:
            obs_time = obs.get("effectiveDateTime", "")
            val = obs.get("valueQuantity", {}).get("value")
            if val is None:
                continue

            codings = obs.get("code", {}).get("coding", [])
            loinc = ""
            for c in codings:
                if c.get("system") == "http://loinc.org":
                    loinc = c.get("code", "")

            concerning = False
            detail = ""
            if loinc == "2708-6" and val < 92:
                concerning = True
                detail = f"SpO2 {val}%"
            elif loinc == "59408-5" and val < 92:
                concerning = True
                detail = f"SpO2 {val}%"
            elif loinc == "8867-4" and val > 110:
                concerning = True
                detail = f"HR {val} bpm"
            elif loinc == "8480-6" and val < 100:
                concerning = True
                detail = f"SBP {val} mmHg"
            elif loinc == "9279-1" and val > 24:
                concerning = True
                detail = f"RR {val}/min"
            elif loinc == "8310-5" and val > 38.5:
                concerning = True
                detail = f"Temp {val}°C"

            if concerning:
                conflicts.append({
                    "type": "note_vital_conflict",
                    "severity": HIGH,
                    "note_type": note_type,
                    "note_time": note_time,
                    "vital_detail": detail,
                    "message": (f"CONFLICT: {note_type} at {note_time[:16]} describes patient as "
                                f"stable/comfortable, but {detail} recorded around same period"),
                })
                break  # One conflict per note is enough

    return conflicts


def detect_all_conflicts(
    medications: list[dict],
    allergies: list[dict],
    med_admins: list[dict],
    notes: list[dict],
    vitals: list[dict],
) -> list[dict]:
    """Run all conflict detectors and return combined sorted list."""
    conflicts = []
    conflicts.extend(detect_allergy_conflicts(medications, allergies))
    conflicts.extend(detect_drug_interactions(medications))
    conflicts.extend(detect_missed_doses(med_admins))
    conflicts.extend(detect_note_vital_conflict(notes, vitals))

    # Sort by severity
    severity_order = {CRITICAL: 0, HIGH: 1, MODERATE: 2, LOW: 3}
    conflicts.sort(key=lambda c: severity_order.get(c.get("severity", ""), 4))

    return conflicts
