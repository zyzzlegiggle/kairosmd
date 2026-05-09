"""In-memory ward action store.

Records clinical actions taken by doctors in response to
flagged conflicts and decision points. This is the
awareness-and-decision layer — it does NOT replace the EHR.

Actions are keyed by patient_id and include:
- Conflict acknowledgements (reviewed, with optional note)
- Clinical response notes
- Escalation flags (urgent review, ICU referral)
- Discharge status overrides
- Pharmacy review flags

In production this would persist to a database with full
audit trail. For demo purposes, in-memory is sufficient.
"""

from __future__ import annotations
from datetime import datetime, timezone

# In-memory store: patient_id -> list of actions
_actions: dict[str, list[dict]] = {}


def record_action(
    patient_id: str,
    action_type: str,
    detail: str = "",
    conflict_id: str = "",
    clinician: str = "Dr Reynolds",
) -> dict:
    """Record a clinical action for a patient.

    Args:
        patient_id: FHIR Patient ID
        action_type: One of:
            - conflict_acknowledged
            - clinical_note_added
            - urgent_review_flagged
            - escalation_requested
            - discharge_approved
            - discharge_blocked
            - pharmacy_review_flagged
        detail: Free text from the clinician
        conflict_id: Optional reference to specific conflict
        clinician: Name of the acting clinician
    """
    action = {
        "action_type": action_type,
        "detail": detail,
        "conflict_id": conflict_id,
        "clinician": clinician,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "patient_id": patient_id,
    }

    _actions.setdefault(patient_id, []).append(action)
    return action


def get_actions(patient_id: str) -> list[dict]:
    """Get all recorded actions for a patient."""
    return _actions.get(patient_id, [])


def get_all_actions() -> dict[str, list[dict]]:
    """Get all actions across all patients."""
    return dict(_actions)


def get_unreviewed_conflict_ids(patient_id: str) -> set[str]:
    """Get conflict IDs that have NOT been acknowledged."""
    acknowledged = set()
    for a in _actions.get(patient_id, []):
        if a["action_type"] == "conflict_acknowledged" and a["conflict_id"]:
            acknowledged.add(a["conflict_id"])
    return acknowledged


def is_conflict_acknowledged(patient_id: str, conflict_id: str) -> bool:
    """Check if a specific conflict has been acknowledged."""
    for a in _actions.get(patient_id, []):
        if (a["action_type"] == "conflict_acknowledged"
                and a["conflict_id"] == conflict_id):
            return True
    return False


def get_escalation_status(patient_id: str) -> str | None:
    """Get the most recent escalation status for a patient."""
    for a in reversed(_actions.get(patient_id, [])):
        if a["action_type"] in ("urgent_review_flagged", "escalation_requested"):
            return a["action_type"]
    return None


def get_discharge_override(patient_id: str) -> str | None:
    """Get the most recent discharge override for a patient."""
    for a in reversed(_actions.get(patient_id, [])):
        if a["action_type"] in ("discharge_approved", "discharge_blocked"):
            return a["action_type"]
    return None
