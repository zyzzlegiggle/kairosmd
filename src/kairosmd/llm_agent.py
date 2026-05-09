"""LLM integration for clinical triage via DigitalOcean GenAI Agent Platform.

Calls the NVIDIA Nemotron 3 Super 120B model through DO's agent endpoint
to generate per-patient clinical briefings.
"""

import json
import httpx
from kairosmd import config


def _build_patient_context(patient_data: dict) -> str:
    """Build a structured text block from compiled FHIR data for a patient."""
    lines = []

    # Demographics
    name = patient_data.get("name", "Unknown")
    dob = patient_data.get("birthDate", "Unknown")
    gender = patient_data.get("gender", "Unknown")
    reason = patient_data.get("reason_for_visit", "Not specified")
    lines.append(f"PATIENT: {name}, DOB: {dob}, Gender: {gender}")
    lines.append(f"REASON FOR VISIT: {reason}")
    lines.append("")

    # Active conditions
    conditions = patient_data.get("active_conditions", [])
    if conditions:
        lines.append("ACTIVE CONDITIONS:")
        for c in conditions:
            lines.append(f"  - {c}")
        lines.append("")

    # Flagged vitals
    vitals = patient_data.get("flagged_vitals", [])
    if vitals:
        lines.append("FLAGGED VITALS:")
        for v in vitals:
            lines.append(f"  - {v.get('display', v.get('code', '?'))}: "
                         f"{v.get('value', '?')} {v.get('unit', '')} "
                         f"[{v.get('severity', '?')}] {v.get('message', '')}")
        lines.append("")

    # Vital trends
    vtrends = patient_data.get("vital_trends", [])
    if vtrends:
        lines.append("VITAL TRENDS:")
        for t in vtrends:
            lines.append(f"  - {t['display']}: {t['from']} -> {t['to']} ({t['direction']})")
        lines.append("")

    # Flagged labs
    labs = patient_data.get("flagged_labs", [])
    if labs:
        lines.append("FLAGGED LABS:")
        for l in labs:
            lines.append(f"  - {l.get('display', l.get('code', '?'))}: "
                         f"{l.get('value', '?')} {l.get('unit', '')} "
                         f"[{l.get('severity', '?')}] {l.get('message', '')}")
        lines.append("")

    # Lab trends
    ltrends = patient_data.get("lab_trends", [])
    if ltrends:
        lines.append("LAB TRENDS:")
        for t in ltrends:
            lines.append(f"  - {t['display']}: {t['from']} -> {t['to']} ({t['direction']})")
        lines.append("")

    # Drug interactions
    interactions = patient_data.get("drug_interactions", [])
    if interactions:
        lines.append("DRUG INTERACTIONS DETECTED:")
        for ix in interactions:
            lines.append(f"  - {ix['drug_a']} + {ix['drug_b']}: {ix['description']}")
        lines.append("")

    # Polypharmacy
    poly = patient_data.get("polypharmacy")
    if poly:
        lines.append(f"POLYPHARMACY: {poly['description']}")
        lines.append("")

    # Allergy conflicts
    conflicts = patient_data.get("allergy_conflicts", [])
    if conflicts:
        lines.append("ALLERGY CONFLICTS:")
        for c in conflicts:
            lines.append(f"  - Medication: {c['medication']} conflicts with "
                         f"allergy to {c['allergy']} (reaction: {c.get('reaction', '?')})")
        lines.append("")

    # Clinical notes
    notes = patient_data.get("notes_summary", "")
    if notes:
        lines.append(f"CLINICAL NOTES SUMMARY:\n{notes}")
        lines.append("")

    # Priority from rule engine
    priority = patient_data.get("priority", "UNKNOWN")
    reasons = patient_data.get("reasons", [])
    lines.append(f"RULE-BASED PRIORITY: {priority}")
    if reasons:
        lines.append("REASONS:")
        for r in reasons:
            lines.append(f"  - {r}")

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

    # Standard OpenAI-compatible response
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
        # Try to find JSON object in the text
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end])
            except json.JSONDecodeError:
                pass
    return {}


BRIEFING_PROMPT = """\
You are a clinical decision-support assistant for an outpatient clinic triage system.
You are NOT a doctor. You do NOT diagnose. You assist doctors by summarizing data.

Below is compiled FHIR data for a patient who has an appointment today.
Generate a structured clinical briefing in valid JSON format.

Rules:
- Only reference data actually provided below. Never invent medications, conditions, or values.
- If data is incomplete or missing, say so explicitly.
- Write in professional but readable clinical language.
- Keep everything concise. Doctors are busy.

Respond ONLY with valid JSON matching this exact schema:
{
  "pre_visit_summary": "A short paragraph covering who the patient is, age, main conditions, why they are coming in, any concerning trends, current medications, and what has changed since last visit.",
  "priority_reasoning": "A plain-language explanation of why this patient is at their current priority level. Reference specific data points.",
  "briefing_points": ["Point 1", "Point 2", "Point 3", "Point 4"],
  "suggested_questions": ["Question 1", "Question 2", "Question 3"],
  "data_completeness": "complete or incomplete with explanation"
}

PATIENT DATA:
"""


async def generate_patient_briefing(patient_data: dict) -> dict:
    """Generate LLM-powered clinical briefing for a single patient."""
    context = _build_patient_context(patient_data)
    prompt = BRIEFING_PROMPT + context

    try:
        raw = await _call_llm(prompt)
        result = _parse_json_response(raw)

        if not result:
            return _fallback_briefing(patient_data, "LLM returned unparseable response")

        # Validate required fields
        required = ["pre_visit_summary", "priority_reasoning",
                     "briefing_points", "suggested_questions"]
        for field in required:
            if field not in result:
                result[field] = "Not available"

        return result

    except Exception as exc:
        return _fallback_briefing(patient_data, str(exc))


def _fallback_briefing(patient_data: dict, error: str) -> dict:
    """Generate a minimal briefing when LLM is unavailable."""
    name = patient_data.get("name", "Unknown")
    priority = patient_data.get("priority", "UNKNOWN")
    reasons = patient_data.get("reasons", [])
    reason_text = "; ".join(reasons) if reasons else "No specific flags."

    return {
        "pre_visit_summary": f"{name} is scheduled for: "
                             f"{patient_data.get('reason_for_visit', 'routine visit')}. "
                             f"Rule-based priority: {priority}.",
        "priority_reasoning": reason_text,
        "briefing_points": reasons[:4] if reasons else ["Review patient chart"],
        "suggested_questions": [
            "How have you been feeling since your last visit?",
            "Have you noticed any new or worsening symptoms?",
            "Are you taking all your medications as prescribed?",
        ],
        "data_completeness": f"LLM unavailable ({error}). Showing rule-based data only.",
    }


# Legacy function for backward compatibility
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
