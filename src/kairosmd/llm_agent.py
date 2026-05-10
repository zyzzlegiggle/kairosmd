"""LLM integration for ward round briefings

Calls NVIDIA Nemotron 3 Super 120B
to generate per-patient ward round briefings.
"""

import json
import httpx
from kairosmd import config


def _build_ward_context(patient_data: dict) -> str:
    """Build structured text from compiled ward round data for a patient."""
    lines = []

    # Demographics
    name = patient_data.get("name", "Unknown")
    dob = patient_data.get("birthDate", "Unknown")
    gender = patient_data.get("gender", "Unknown")
    lines.append(f"PATIENT: {name}, DOB: {dob}, Gender: {gender}")

    # Encounter info
    enc = patient_data.get("encounter", {})
    if enc:
        lines.append(f"WARD: {enc.get('ward', '?')}, BED: {enc.get('bed', '?')}")
        lines.append(f"ADMISSION DATE: {enc.get('admission_date', '?')[:10]}")
        lines.append(f"ADMITTING DIAGNOSIS: {enc.get('admitting_diagnosis', '?')}")
        lines.append(f"LENGTH OF STAY: {enc.get('length_of_stay', '?')} days")
    lines.append("")

    # NEWS2
    news2 = patient_data.get("news2", {})
    if news2:
        lines.append(f"NEWS2 SCORE: {news2.get('total_score', '?')} ({news2.get('risk_level', '?')})")
        breakdown = news2.get("breakdown", {})
        for param, data in breakdown.items():
            lines.append(f"  {param}: {data.get('value', '?')} (score {data.get('score', '?')})")
        lines.append("")

    # Active conditions
    conditions = patient_data.get("active_conditions", [])
    if conditions:
        lines.append("ACTIVE CONDITIONS:")
        for c in conditions:
            lines.append(f"  - {c}")
        lines.append("")

    # Vital trends (24h)
    vtrends = patient_data.get("vital_trends", [])
    if vtrends:
        lines.append("VITAL TRENDS (24h):")
        for t in vtrends:
            flag = " [CONCERNING]" if t.get("concerning") else ""
            lines.append(f"  - {t['parameter']}: {t['oldest']} -> {t['newest']} ({t['direction']}){flag}")
        lines.append("")

    # Lab trends
    ltrends = patient_data.get("lab_trends", [])
    if ltrends:
        lines.append("LAB TRENDS:")
        for t in ltrends:
            lines.append(f"  - {t['parameter']}: {t['oldest']} -> {t['newest']} ({t['direction']})")
        lines.append("")

    # Flagged vitals/labs
    fv = patient_data.get("flagged_vitals", [])
    if fv:
        lines.append("FLAGGED VITALS:")
        for v in fv:
            lines.append(f"  - {v.get('message', str(v))}")
        lines.append("")

    fl = patient_data.get("flagged_labs", [])
    if fl:
        lines.append("FLAGGED LABS:")
        for l in fl:
            lines.append(f"  - {l.get('message', str(l))}")
        lines.append("")

    # Conflicts
    conflicts = patient_data.get("conflicts", [])
    if conflicts:
        lines.append("DETECTED CONFLICTS:")
        for c in conflicts:
            lines.append(f"  - [{c.get('severity', '?')}] {c.get('message', str(c))}")
        lines.append("")

    # Clinical notes
    notes = patient_data.get("clinical_notes", [])
    if notes:
        lines.append("CLINICAL NOTES:")
        for n in notes:
            lines.append(f"  [{n.get('type', 'Note')}] {n.get('date', '')[:16]}")
            lines.append(f"  {n.get('text', '')[:300]}")
            lines.append("")

    # Discharge status
    discharge = patient_data.get("discharge", {})
    if discharge:
        lines.append(f"DISCHARGE STATUS: {discharge.get('status', '?')}")
        lines.append(f"  {discharge.get('summary', '')}")
        for b in discharge.get("blockers", []):
            lines.append(f"  BLOCKER: {b}")
        lines.append("")

    # Safety flags
    sf = patient_data.get("safety_flags", [])
    if sf:
        lines.append("SAFETY FLAGS:")
        for f in sf:
            lines.append(f"  - {f}")
        lines.append("")

    # FDA Safety Data (from OpenFDA API)
    fda = patient_data.get("fda_safety", {})
    if fda:
        warnings = fda.get("drug_warnings", [])
        if warnings:
            lines.append("FDA DRUG WARNINGS (from openFDA):")
            for w in warnings:
                drug = w.get("drug", "?")
                parts = []
                if w.get("boxed_warning"):
                    parts.append("BOXED WARNING")
                if w.get("has_contraindications"):
                    parts.append("HAS CONTRAINDICATIONS")
                lines.append(f"  - {drug}: {', '.join(parts)}")
                if w.get("interaction_warnings"):
                    lines.append(f"    Interactions: {w['interaction_warnings'][:200]}")
            lines.append("")

        evidence = fda.get("interaction_evidence", [])
        if evidence:
            lines.append("FDA ADVERSE EVENT EVIDENCE (from FAERS):")
            for ev in evidence:
                drugs = " + ".join(ev.get("drugs", []))
                reports = ev.get("fda_reports", 0)
                reactions = ", ".join(ev.get("top_reactions", []))
                lines.append(f"  - {drugs}: {reports} reports. Top reactions: {reactions}")
            lines.append("")

    return "\n".join(lines)


async def _call_llm(user_message: str) -> str:
    """Send a message to the DO agent endpoint and return raw content."""
    endpoint = config.LLM_ENDPOINT.rstrip("/")
    url = f"{endpoint}/api/v1/chat/completions"

    headers = {"Content-Type": "application/json"}
    if config.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LLM_API_KEY}"

    payload = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "user", "content": user_message}
        ],
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if "choices" in data:
        return data["choices"][0]["message"]["content"] or ""

    return json.dumps(data)


def _parse_json_response(raw: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
    return {}


WARD_BRIEFING_PROMPT = """\
You are a clinical decision-support assistant for an inpatient hospital ward round system.
You are NOT a doctor. You do NOT diagnose. You assist consultants by summarizing overnight changes.

Below is compiled FHIR data for an inpatient on a general medicine ward.
Generate a structured ward round briefing in valid JSON format.

Rules:
- Only reference data actually provided below. Never invent medications, conditions, or values.
- If data is incomplete or missing, say so explicitly.
- Write in professional clinical language using proper medical terminology.
- Keep everything concise. Consultants are doing a ward round with limited time per patient.
- Focus on what has CHANGED since the last review.

Respond ONLY with valid JSON matching this exact schema:
{
  "overnight_summary": "A concise paragraph (max 150 words) covering what changed overnight. Use SOAP-adjacent format. Focus on trends, events, and any deterioration or improvement.",
  "conflict_highlights": "Plain language explanation of any detected conflicts. If no conflicts, say 'No conflicts detected.'",
  "ward_round_talking_points": ["Point 1", "Point 2", "Point 3", "Point 4"],
  "suggested_plan_adjustments": "If data suggests the current plan needs review, state what and why. If plan appears appropriate, confirm briefly.",
  "data_completeness": "complete or brief note on what is missing"
}

PATIENT DATA:
"""


async def generate_patient_briefing(patient_data: dict) -> dict:
    """Generate LLM-powered ward round briefing for a single patient."""
    context = _build_ward_context(patient_data)
    prompt = WARD_BRIEFING_PROMPT + context

    try:
        raw = await _call_llm(prompt)
        result = _parse_json_response(raw)

        if not result:
            return _fallback_briefing(patient_data, "Response parsing error")

        required = ["overnight_summary", "conflict_highlights",
                     "ward_round_talking_points", "suggested_plan_adjustments"]
        for field in required:
            if field not in result:
                result[field] = "Not available"

        return result

    except Exception as exc:
        return _fallback_briefing(patient_data, str(exc))


def _fallback_briefing(patient_data: dict, error: str) -> dict:
    """Generate a minimal briefing when LLM is unavailable."""
    name = patient_data.get("name", "Unknown")
    news2 = patient_data.get("news2", {})
    conflicts = patient_data.get("conflicts", [])
    conditions = patient_data.get("active_conditions", [])

    conflict_text = "; ".join(c.get("message", "") for c in conflicts) if conflicts else "None detected"
    condition_text = ", ".join(conditions[:3]) if conditions else "Not available"

    return {
        "overnight_summary": (
            f"{name} - NEWS2: {news2.get('total_score', '?')} ({news2.get('risk_level', '?')}). "
            f"Conditions: {condition_text}. "
            f"Automated summary unavailable - review chart directly."
        ),
        "conflict_highlights": conflict_text,
        "ward_round_talking_points": [
            "Review overnight observations",
            "Check medication chart",
            "Assess discharge readiness",
        ],
        "suggested_plan_adjustments": "Automated suggestion unavailable. Review data manually.",
        "data_completeness": f"Summary generation limit or error ({error}). Showing rule-based data only.",
    }


# Legacy function for backward compatibility with risk_engine
async def analyse_notes(notes_text: str) -> dict:
    """Send clinical notes for structured risk assessment."""
    if not notes_text.strip():
        return {
            "concerns": [], "keywords_found": [],
            "summary": "No clinical notes available.",
            "note_risk_score": 0,
        }

    prompt = (
        "You are a clinical assistant. Analyze these clinical notes and respond "
        "with valid JSON: {\"concerns\": [...], \"keywords_found\": [...], "
        "\"summary\": \"...\", \"note_risk_score\": 0-30}\n\n"
        f"Clinical notes:\n{notes_text}"
    )

    try:
        raw = await _call_llm(prompt)
        result = _parse_json_response(raw)
        if result and "note_risk_score" in result:
            return result
    except Exception:
        pass

    return {
        "concerns": [], "keywords_found": [],
        "summary": notes_text[:300] if notes_text else "No notes.",
        "note_risk_score": 0,
    }
