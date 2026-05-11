"""Discharge readiness assessment for inpatient patients.

Evaluates whether a patient is ready for discharge based on:
- Vital signs stability
- Lab results resolution
- IV medication dependency
- Follow-up plan documentation
- Pending results
"""

from __future__ import annotations
from kairosmd.news2 import extract_latest_vitals


# -- Status labels -----------------------------------------------------
READY = "Ready"
NOT_READY = "Not Ready"
REQUIRES_REVIEW = "Requires Review"


def assess_discharge_readiness(
    vitals_obs: list[dict],
    labs_obs: list[dict],
    medications: list[dict],
    notes: list[dict],
    flags: list[dict],
    news2_score: int,
    encounter: dict | None = None,
) -> dict:
    """Assess whether patient meets discharge criteria.

    Returns dict with status, checklist items, and blocking reasons.
    """
    checklist = []
    blockers = []

    # 1. Vitals within acceptable range (NEWS2 <= 2)
    vitals_ok = news2_score <= 2
    checklist.append({
        "item": "Vitals within acceptable range",
        "met": vitals_ok,
        "detail": f"NEWS2 score: {news2_score}" + (" (acceptable)" if vitals_ok else " (too high)"),
    })
    if not vitals_ok:
        blockers.append(f"NEWS2 score {news2_score} is above discharge threshold (<=2)")

    # 2. No critical lab values
    critical_labs = _check_critical_labs(labs_obs)
    labs_ok = len(critical_labs) == 0
    checklist.append({
        "item": "All critical labs resolved or stable",
        "met": labs_ok,
        "detail": "No critical labs" if labs_ok else f"{len(critical_labs)} critical lab(s)",
    })
    if not labs_ok:
        for cl in critical_labs:
            blockers.append(f"Critical lab: {cl}")

    # 3. Not IV-dependent (all meds oral or can be switched)
    iv_meds = _check_iv_dependency(medications)
    iv_ok = len(iv_meds) == 0
    checklist.append({
        "item": "Not dependent on IV medications",
        "met": iv_ok,
        "detail": "All oral/SC medications" if iv_ok else f"{len(iv_meds)} IV med(s) active",
    })
    if not iv_ok:
        for m in iv_meds:
            blockers.append(f"IV medication active: {m}")

    # 4. Follow-up plan documented (check progress notes for discharge/follow-up keywords)
    has_plan = _check_follow_up_plan(notes)
    checklist.append({
        "item": "Follow-up plan documented",
        "met": has_plan,
        "detail": "Plan found in notes" if has_plan else "No discharge/follow-up plan found",
    })
    if not has_plan:
        blockers.append("No follow-up or discharge plan documented in notes")

    # 5. No pending results (check for nil-by-mouth or pending flags)
    pending = _check_pending_flags(flags)
    no_pending = len(pending) == 0
    checklist.append({
        "item": "No pending results or procedures blocking discharge",
        "met": no_pending,
        "detail": "No blockers" if no_pending else f"{len(pending)} pending item(s)",
    })
    if not no_pending:
        for p in pending:
            blockers.append(f"Pending: {p}")

    # 6. Afebrile for 24+ hours
    afebrile = _check_afebrile(vitals_obs)
    checklist.append({
        "item": "Afebrile for 24 hours",
        "met": afebrile,
        "detail": "Afebrile" if afebrile else "Fever recorded in last 24 hours",
    })
    if not afebrile:
        blockers.append("Patient has had fever in last 24 hours")

    # 7. Social and Functional Stability (Scan notes for social care/mobility readiness)
    social_ok = _check_social_functional(notes)
    checklist.append({
        "item": "Social and functional stability documented",
        "met": social_ok,
        "detail": "Social/Functional readiness noted" if social_ok else "No social care or mobility clearance found",
    })
    if not social_ok:
        blockers.append("Pending social care or functional (PT/OT) review")

    # Determine overall status
    critical_blockers = [b for b in blockers if "critical" in b.lower() or "IV" in b or "NEWS2" in b]
    if len(blockers) == 0:
        status = READY
    elif len(critical_blockers) > 0:
        status = NOT_READY
    else:
        status = REQUIRES_REVIEW

    met_count = sum(1 for c in checklist if c["met"])

    return {
        "status": status,
        "checklist": checklist,
        "blockers": blockers,
        "met_count": met_count,
        "total_count": len(checklist),
        "summary": f"{met_count}/{len(checklist)} criteria met - {status}",
    }


# -- Internal helpers --------------------------------------------------

def _check_critical_labs(labs_obs: list[dict]) -> list[str]:
    """Return list of critical lab descriptions."""
    critical = []
    CRITICAL_RANGES = {
        "2823-3": ("Potassium", 3.0, 5.5),
        "2951-2": ("Sodium", 125, 150),
        "2160-0": ("Creatinine", 0, 3.0),
        "718-7":  ("Hemoglobin", 7.0, 20.0),
    }

    # Get latest value per LOINC
    latest: dict[str, tuple[str, float]] = {}
    for obs in labs_obs:
        codings = obs.get("code", {}).get("coding", [])
        loinc = ""
        for c in codings:
            if c.get("system") == "http://loinc.org":
                loinc = c.get("code", "")
        if loinc not in CRITICAL_RANGES:
            continue
        val = obs.get("valueQuantity", {}).get("value")
        dt = obs.get("effectiveDateTime", "")
        if val is not None and (loinc not in latest or dt > latest[loinc][0]):
            latest[loinc] = (dt, float(val))

    for loinc, (dt, val) in latest.items():
        name, low, high = CRITICAL_RANGES[loinc]
        if val < low or val > high:
            critical.append(f"{name}: {val} (range {low}-{high})")

    return critical


def _check_iv_dependency(medications: list[dict]) -> list[str]:
    """Return list of active IV medication names."""
    iv_meds = []
    for med in medications:
        if med.get("status") != "active":
            continue
        dosage = med.get("dosageInstruction", [{}])
        route = ""
        for d in dosage:
            route = d.get("route", {}).get("text", "") or d.get("text", "")
        name = med.get("medicationCodeableConcept", {}).get("text", "")
        if "intravenous" in route.lower() or "iv " in name.lower():
            iv_meds.append(name)
    return iv_meds


def _check_follow_up_plan(notes: list[dict]) -> bool:
    """Check if any note mentions discharge or follow-up plan."""
    import base64
    plan_keywords = ["discharge", "follow-up", "follow up", "outpatient",
                     "gp review", "clinic review", "plan discharge"]
    for note in notes:
        text = ""
        for content in note.get("content", []):
            att = content.get("attachment", {})
            if att.get("data"):
                try:
                    text = base64.b64decode(att["data"]).decode("utf-8", errors="replace")
                except Exception:
                    pass
        if note.get("description"):
            text = text or note.get("description", "")
        if any(kw in text.lower() for kw in plan_keywords):
            return True
    return False


def _check_pending_flags(flags: list[dict]) -> list[str]:
    """Check for flags that block discharge (NBM, pending results)."""
    pending = []
    for flag in flags:
        code_text = flag.get("code", {}).get("text", "").lower()
        if "nil by mouth" in code_text or "nbm" in code_text or "surgery" in code_text:
            pending.append(flag.get("code", {}).get("text", "Pending item"))
    return pending


def _check_afebrile(vitals_obs: list[dict]) -> bool:
    """Check if patient has been afebrile (temp < 38.0) across all readings."""
    for obs in vitals_obs:
        codings = obs.get("code", {}).get("coding", [])
        loinc = ""
        for c in codings:
            if c.get("system") == "http://loinc.org":
                loinc = c.get("code", "")
        if loinc != "8310-5":
            continue
        val = obs.get("valueQuantity", {}).get("value")
        if val is not None and val >= 38.0:
            return False
    return True


def _check_social_functional(notes: list[dict]) -> bool:
    """Check if notes mention social care or functional readiness."""
    import base64
    social_keywords = [
        "package of care", "poc ", "socially fit", "safe at home",
        "mobility stable", "walking well", "physio review complete",
        "occupational therapy", "ot review", "mffd", "medically fit"
    ]
    for note in notes:
        text = ""
        for content in note.get("content", []):
            att = content.get("attachment", {})
            if att.get("data"):
                try:
                    text = base64.b64decode(att["data"]).decode("utf-8", errors="replace")
                except Exception:
                    pass
        if note.get("description"):
            text = text or note.get("description", "")
        if any(kw in text.lower() for kw in social_keywords):
            return True
    return False
