"""4-tier outpatient triage scoring engine.

URGENT    - Needs immediate attention today
ATTENTION - Needs careful review, potential issues  
STABLE    - Minor concerns, routine monitoring
ROUTINE   - Normal follow-up, no flags
"""

from kairosmd.vitals_rules import flag_vitals, Severity
from kairosmd.labs_rules import flag_labs
from kairosmd.drug_interactions import (
    check_interactions_local, check_polypharmacy, extract_base_name,
)
from kairosmd.llm_agent import analyse_notes
import base64


def extract_note_text(doc_refs: list[dict]) -> str:
    """Pull plain-text content out of FHIR DocumentReference resources."""
    texts: list[str] = []
    for doc in doc_refs:
        for content in doc.get("content", []):
            attachment = content.get("attachment", {})
            if attachment.get("data"):
                try:
                    decoded = base64.b64decode(attachment["data"]).decode("utf-8", errors="replace")
                    texts.append(decoded)
                except Exception:
                    pass
            if doc.get("description"):
                texts.append(doc["description"])
        text_div = doc.get("text", {}).get("div", "")
        if text_div:
            texts.append(text_div)
    return "\n---\n".join(texts) if texts else ""

# -- Concerning keywords in notes --------------------------------------
URGENT_KEYWORDS = [
    "chest pain", "shortness of breath", "altered consciousness",
    "sepsis", "stroke", "unresponsive", "severe bleeding",
    "acute kidney injury", "dropping", "febrile", "confused",
]
DETERIORATING_KEYWORDS = [
    "worsening", "not improving", "increased pain", "declining",
    "progressing", "trending up", "jumped", "rising",
]


def _detect_trends(flagged: list[dict]) -> list[dict]:
    """Detect worsening trends across time points for same code."""
    by_code: dict[str, list] = {}
    for f in flagged:
        code = f["code"]
        if code not in by_code:
            by_code[code] = []
        by_code[code].append(f)

    trends = []
    for code, readings in by_code.items():
        if len(readings) < 2:
            continue
        sorted_r = sorted(readings, key=lambda x: x.get("effective", ""))
        first_val = sorted_r[0]["value"]
        last_val = sorted_r[-1]["value"]
        if isinstance(first_val, (int, float)) and isinstance(last_val, (int, float)):
            if last_val > first_val * 1.1:
                trends.append({
                    "code": code,
                    "display": sorted_r[0].get("display", code),
                    "direction": "worsening",
                    "from": first_val,
                    "to": last_val,
                })
            elif last_val < first_val * 0.9:
                trends.append({
                    "code": code,
                    "display": sorted_r[0].get("display", code),
                    "direction": "improving",
                    "from": first_val,
                    "to": last_val,
                })
    return trends


def _check_allergy_conflicts(allergies: list[dict], medications: list[dict]) -> list[dict]:
    """Check if any active medication conflicts with known allergies."""
    conflicts = []
    allergy_substances = []
    for a in allergies:
        substance = a.get("code", {}).get("text", "").lower()
        if substance:
            allergy_substances.append((substance, a))

    for med in medications:
        med_text = ""
        mc = med.get("medicationCodeableConcept", {})
        med_text = mc.get("text", "").lower()
        if not med_text:
            for c in mc.get("coding", []):
                med_text = c.get("display", "").lower()
                if med_text:
                    break

        for substance, allergy_res in allergy_substances:
            if substance in med_text or med_text and substance.split()[0] in med_text:
                reaction = ""
                reactions = allergy_res.get("reaction", [])
                if reactions:
                    reaction = reactions[0].get("description", "")
                conflicts.append({
                    "medication": med_text,
                    "allergy": substance,
                    "reaction": reaction,
                })
    return conflicts


async def score_patient_v2(
    vital_obs: list[dict],
    lab_obs: list[dict],
    doc_refs: list[dict],
    conditions: list[dict],
    medications: list[dict],
    allergies: list[dict],
) -> dict:
    """Score a patient using 4-tier outpatient triage logic."""

    reasons = []
    priority = "ROUTINE"

    # 1. Flag vitals and labs
    flagged_vitals = flag_vitals(vital_obs)
    flagged_labs = flag_labs(lab_obs)

    critical_vitals = [v for v in flagged_vitals if v["severity"] == Severity.CRITICAL.value]
    abnormal_vitals = [v for v in flagged_vitals if v["severity"] == Severity.ABNORMAL.value]
    critical_labs = [l for l in flagged_labs if l["severity"] == Severity.CRITICAL.value]
    abnormal_labs = [l for l in flagged_labs if l["severity"] == Severity.ABNORMAL.value]

    # 2. Trends
    vital_trends = _detect_trends(flagged_vitals)
    lab_trends = _detect_trends(flagged_labs)
    worsening_trends = [t for t in vital_trends + lab_trends if t["direction"] == "worsening"]

    # 3. Drug interactions
    med_names = []
    med_rxcuis = []
    for m in medications:
        mc = m.get("medicationCodeableConcept", {})
        name = mc.get("text", "")
        if not name:
            for c in mc.get("coding", []):
                name = c.get("display", "")
                if name:
                    break
        if name:
            med_names.append(extract_base_name(name))
        for c in mc.get("coding", []):
            if c.get("code"):
                med_rxcuis.append(c["code"])

    interactions = check_interactions_local(med_names)
    polypharmacy = check_polypharmacy(len(medications))

    # 4. Allergy conflicts
    allergy_conflicts = _check_allergy_conflicts(allergies, medications)

    # 5. Notes analysis
    note_text = extract_note_text(doc_refs)
    note_lower = note_text.lower()

    urgent_keywords_found = [k for k in URGENT_KEYWORDS if k in note_lower]
    deteriorating_keywords_found = [k for k in DETERIORATING_KEYWORDS if k in note_lower]

    # 6. LLM analysis (best effort)
    llm_result = await analyse_notes(note_text)

    # -- Priority determination ----------------------------------------

    # URGENT: critical values, urgent keywords, allergy conflicts
    if critical_vitals:
        priority = "URGENT"
        for v in critical_vitals:
            reasons.append(f"Critical vital: {v['message']}")

    if critical_labs:
        priority = "URGENT"
        for l in critical_labs:
            reasons.append(f"Critical lab: {l['message']}")

    if urgent_keywords_found:
        priority = "URGENT"
        reasons.append(f"Concerning notes: {', '.join(urgent_keywords_found)}")

    if allergy_conflicts:
        priority = "URGENT"
        for c in allergy_conflicts:
            reasons.append(f"Allergy conflict: {c['medication']} vs allergy to {c['allergy']}")

    # ATTENTION: worsening trends, drug interactions, polypharmacy, deteriorating keywords
    if priority != "URGENT":
        if worsening_trends:
            priority = "ATTENTION"
            for t in worsening_trends:
                reasons.append(f"Worsening trend: {t['display']} {t['from']} -> {t['to']}")

        if interactions:
            priority = "ATTENTION"
            for ix in interactions:
                reasons.append(f"Drug interaction: {ix['drug_a']} + {ix['drug_b']} - {ix['description']}")

        if polypharmacy:
            priority = "ATTENTION"
            reasons.append(polypharmacy["description"])

        if deteriorating_keywords_found and priority != "ATTENTION":
            priority = "ATTENTION"
            reasons.append(f"Notes mention: {', '.join(deteriorating_keywords_found)}")

    # STABLE: mild abnormalities but no critical flags
    if priority == "ROUTINE" and (abnormal_vitals or abnormal_labs):
        priority = "STABLE"
        for v in abnormal_vitals[:3]:
            reasons.append(f"Abnormal vital: {v['message']}")
        for l in abnormal_labs[:3]:
            reasons.append(f"Abnormal lab: {l['message']}")

    if not reasons:
        reasons.append("All values within normal limits. Routine follow-up.")

    # Conditions summary
    condition_names = []
    for cond in conditions:
        name = cond.get("code", {}).get("text", "")
        if not name:
            codings = cond.get("code", {}).get("coding", [])
            name = codings[0].get("display", "Unknown") if codings else "Unknown"
        condition_names.append(name)

    return {
        "priority": priority,
        "reasons": reasons,
        "flagged_vitals": [v for v in flagged_vitals if v["severity"] != "normal"],
        "flagged_labs": [l for l in flagged_labs if l["severity"] != "normal"],
        "vital_trends": vital_trends,
        "lab_trends": lab_trends,
        "drug_interactions": interactions,
        "polypharmacy": polypharmacy,
        "allergy_conflicts": allergy_conflicts,
        "active_conditions": condition_names,
        "notes_summary": llm_result.get("summary", note_text[:300] if note_text else "No notes"),
        "llm_analysis": llm_result,
    }
