"""LLM integration for clinical note analysis.

Uses httpx to communicate with OpenAI-compatible endpoints
to interpret unstructured notes and extract clinical concerns.
"""

import json
import httpx
from kairosmd import config

SYSTEM_PROMPT = """\
You are a clinical decision-support assistant embedded in a hospital triage system.
You will receive clinical notes (nursing notes, doctor notes, progress notes) for a patient.

Your task:
1. Identify any concerning clinical patterns or deterioration signals.
2. Flag keywords/phrases like: deteriorating, confused, agitated, pain, unresponsive, hypotensive, tachycardic, desaturation, fall risk, sepsis.
3. Summarise the key clinical concerns in 2-3 sentences.
4. Assign a note_risk_score from 0-30 based on how alarming the notes are:
   - 0-5: routine / stable
   - 6-15: some concerns worth monitoring
   - 16-25: significant concerns requiring attention
   - 26-30: alarming - immediate review needed

Respond ONLY with valid JSON matching this schema:
{
  "concerns": ["string"],
  "keywords_found": ["string"],
  "summary": "string",
  "note_risk_score": int
}
"""

async def analyse_notes(notes_text: str) -> dict:
    """Send clinical notes for structured risk assessment using httpx."""
    if not notes_text.strip():
        return {
            "concerns": [],
            "keywords_found": [],
            "summary": "No clinical notes available.",
            "note_risk_score": 0,
        }

    url = f"{config.LLM_ENDPOINT.rstrip('/')}/chat/completions"
    headers = {
        "Content-Type": "application/json"
    }
    
    # Only add Authorization header if key is provided
    if config.LLM_API_KEY:
        headers["Authorization"] = f"Bearer {config.LLM_API_KEY}"
    
    payload = {
        "model": config.LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Clinical notes:\n\n{notes_text}"}
        ],
        "temperature": 0.1,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"}
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            raw = data["choices"][0]["message"]["content"] or "{}"
            
            # Robust cleaning
            raw = raw.strip()
            if raw.startswith("```"):
                lines = raw.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw = "\n".join(lines).strip()
            
            return json.loads(raw)
    except Exception as exc:
        return {
            "concerns": [],
            "keywords_found": [],
            "summary": f"LLM analysis failed: {exc}",
            "note_risk_score": 0,
        }
