"""Composite risk-scoring engine.

Combines signals from vitals, labs, clinical notes (LLM), conditions,
and time-since-last-review into a single 0-100 urgency score.

Score bands:
  >=70  CRITICAL  - immediate attention required
  50-69 HIGH     - urgent, review within 1 hour
  30-49 MODERATE - semi-urgent, review within 2-4 hours
   0-29 LOW      - routine scheduled review
"""

from __future__ import annotations
import base64
from datetime import datetime, timezone

from kairosmd.vitals_rules import flag_vitals, Severity
from kairosmd.labs_rules import flag_labs
from kairosmd.llm_agent import analyse_notes


# -- Weights -----------------------------------------------------------
WEIGHT_VITAL_CRITICAL = 15
WEIGHT_VITAL_ABNORMAL = 5
WEIGHT_LAB_CRITICAL = 20
WEIGHT_LAB_ABNORMAL = 5
WEIGHT_CONDITION = 3           # per active chronic condition
WEIGHT_STALE_REVIEW_PER_HR = 2 # per hour beyond 8 h since last review
MAX_SCORE = 100

RISK_BANDS = [
    (70, "CRITICAL", "Immediate attention required"),
    (50, "HIGH",     "Urgent - review within 1 hour"),
    (30, "MODERATE", "Semi-urgent - review within 2-4 hours"),
    ( 0, "LOW",      "Routine scheduled review"),
]


def _band(score: int) -> tuple[str, str]:
    for threshold, label, desc in RISK_BANDS:
        if score >= threshold:
            return label, desc
    return "LOW", "Routine scheduled review"


# -- Note text extraction ----------------------------------------------
def extract_note_text(doc_refs: list[dict]) -> str:
    """Pull plain-text content out of FHIR DocumentReference resources."""
    texts: list[str] = []
    for doc in doc_refs:
        for content in doc.get("content", []):
            attachment = content.get("attachment", {})
            # inline data (base64)
            if attachment.get("data"):
                try:
                    decoded = base64.b64decode(attachment["data"]).decode("utf-8", errors="replace")
                    texts.append(decoded)
                except Exception:
                    pass
            # plain-text title / description fallback
            if doc.get("description"):
                texts.append(doc["description"])
        # some servers put text in doc.text.div
        text_div = doc.get("text", {}).get("div", "")
        if text_div:
            texts.append(text_div)
    return "\n---\n".join(texts) if texts else ""


# -- Main scoring function ---------------------------------------------
async def score_patient(
    vital_obs: list[dict],
    lab_obs: list[dict],
    doc_refs: list[dict],
    conditions: list[dict],
    last_reviewed: str | None = None,
) -> dict:
    """Compute composite risk score for a single patient.

    Returns a dict with score, band, breakdown of contributing factors,
    and the LLM note analysis.
    """
    score = 0
    reasons: list[str] = []

    # -- 1. Vitals -----------------------------------------------------
    flagged_vitals = flag_vitals(vital_obs)
    for fv in flagged_vitals:
        if fv["severity"] == Severity.CRITICAL.value:
            score += WEIGHT_VITAL_CRITICAL
            reasons.append(f"CRITICAL: {fv['message']}")
        elif fv["severity"] == Severity.ABNORMAL.value:
            score += WEIGHT_VITAL_ABNORMAL
            reasons.append(f"ABNORMAL: {fv['message']}")

    # -- 2. Labs -------------------------------------------------------
    flagged_labs = flag_labs(lab_obs)
    for fl in flagged_labs:
        if fl["severity"] == Severity.CRITICAL.value:
            score += WEIGHT_LAB_CRITICAL
            reasons.append(f"CRITICAL: {fl['message']}")
        elif fl["severity"] == Severity.ABNORMAL.value:
            score += WEIGHT_LAB_ABNORMAL
            reasons.append(f"ABNORMAL: {fl['message']}")

    # -- 3. Clinical notes (LLM) --------------------------------------
    note_text = extract_note_text(doc_refs)
    llm_result = await analyse_notes(note_text)
    note_score = llm_result.get("note_risk_score", 0)
    score += note_score
    if llm_result.get("concerns"):
        for c in llm_result["concerns"]:
            reasons.append(f"Note concern: {c}")

    # -- 4. Chronic conditions -----------------------------------------
    condition_names: list[str] = []
    for cond in conditions:
        name = cond.get("code", {}).get("text", "")
        if not name:
            codings = cond.get("code", {}).get("coding", [])
            name = codings[0].get("display", "Unknown") if codings else "Unknown"
        condition_names.append(name)
        score += WEIGHT_CONDITION

    if condition_names:
        reasons.append(f"Active conditions: {', '.join(condition_names)}")

    # -- 5. Time since last review -------------------------------------
    if last_reviewed:
        try:
            last_dt = datetime.fromisoformat(last_reviewed).replace(tzinfo=timezone.utc)
            hours_ago = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
            if hours_ago > 8:
                stale_points = int((hours_ago - 8) * WEIGHT_STALE_REVIEW_PER_HR)
                score += stale_points
                reasons.append(
                    f"Last reviewed {hours_ago:.1f}h ago (+{stale_points} pts)"
                )
        except Exception:
            pass

    # clamp
    score = min(score, MAX_SCORE)
    band_label, band_desc = _band(score)

    return {
        "risk_score": score,
        "risk_band": band_label,
        "risk_description": band_desc,
        "reasons": reasons,
        "flagged_vitals": flagged_vitals,
        "flagged_labs": flagged_labs,
        "llm_analysis": llm_result,
        "active_conditions": condition_names,
    }
