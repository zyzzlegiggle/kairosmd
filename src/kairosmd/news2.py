"""NEWS2 (National Early Warning Score 2) calculator.

Calculates NEWS2 from the latest vital signs and returns
score, risk level, and parameter-level breakdown.

Score bands:
  0-4:  LOW risk
  5-6:  MEDIUM risk (or 3 in any single parameter)
  7+:   HIGH risk - urgent clinical review required
"""

from __future__ import annotations


# -- Scoring tables ----------------------------------------------------

def _score_rr(rr: float) -> int:
    if rr <= 8: return 3
    if rr <= 11: return 1
    if rr <= 20: return 0
    if rr <= 24: return 2
    return 3

def _score_spo2_scale1(spo2: float) -> int:
    """SpO2 Scale 1 - for patients NOT on supplemental O2 target 88-92%."""
    if spo2 <= 91: return 3
    if spo2 <= 93: return 2
    if spo2 <= 95: return 1
    return 0

def _score_spo2_scale2(spo2: float) -> int:
    """SpO2 Scale 2 - for patients with hypercapnic respiratory failure
    on prescribed O2 (target 88-92%)."""
    if spo2 <= 83: return 3
    if spo2 <= 85: return 2
    if spo2 <= 87: return 1
    if spo2 <= 92: return 0  # on target
    if spo2 <= 94: return 1
    if spo2 <= 96: return 2
    return 3

def _score_on_air(on_supplemental_o2: bool) -> int:
    return 2 if on_supplemental_o2 else 0

def _score_sbp(sbp: float) -> int:
    if sbp <= 90: return 3
    if sbp <= 100: return 2
    if sbp <= 110: return 1
    if sbp <= 219: return 0
    return 3

def _score_hr(hr: float) -> int:
    if hr <= 40: return 3
    if hr <= 50: return 1
    if hr <= 90: return 0
    if hr <= 110: return 1
    if hr <= 130: return 2
    return 3

def _score_consciousness(gcs: float) -> int:
    """Alert (GCS 15) = 0, any reduction = 3 (CVPU)."""
    return 0 if gcs >= 15 else 3

def _score_temp(temp: float) -> int:
    if temp <= 35.0: return 3
    if temp <= 36.0: return 1
    if temp <= 38.0: return 0
    if temp <= 39.0: return 1
    return 2


# -- LOINC code mapping ------------------------------------------------
LOINC_MAP = {
    "8480-6": "sbp",
    "8462-4": "dbp",
    "8867-4": "hr",
    "9279-1": "rr",
    "2708-6": "spo2",
    "8310-5": "temp",
    "9269-2": "gcs",
}


def extract_latest_vitals(observations: list[dict]) -> dict:
    """Extract the most recent value for each vital sign from FHIR Observations."""
    latest: dict[str, tuple[str, float]] = {}  # key -> (datetime, value)

    for obs in observations:
        codings = obs.get("code", {}).get("coding", [])
        loinc = None
        for c in codings:
            if c.get("system") == "http://loinc.org":
                loinc = c.get("code")
                break
        if not loinc or loinc not in LOINC_MAP:
            continue

        key = LOINC_MAP[loinc]
        dt = obs.get("effectiveDateTime", "")
        val = obs.get("valueQuantity", {}).get("value")
        if val is None:
            continue

        if key not in latest or dt > latest[key][0]:
            latest[key] = (dt, float(val))

    return {k: v[1] for k, v in latest.items()}


def calculate_news2(
    vitals: dict,
    on_supplemental_o2: bool = False,
    use_scale2: bool = False,
) -> dict:
    """Calculate NEWS2 score from a vitals dictionary.

    Args:
        vitals: dict with keys: sbp, hr, rr, spo2, temp, gcs
        on_supplemental_o2: True if patient is receiving supplemental O2
        use_scale2: True if patient has hypercapnic respiratory failure

    Returns:
        dict with total score, risk level, and per-parameter breakdown
    """
    breakdown = {}

    # Respiratory rate
    rr = vitals.get("rr")
    if rr is not None:
        breakdown["respiratory_rate"] = {"value": rr, "score": _score_rr(rr)}

    # SpO2
    spo2 = vitals.get("spo2")
    if spo2 is not None:
        spo2_score = _score_spo2_scale2(spo2) if use_scale2 else _score_spo2_scale1(spo2)
        breakdown["spo2"] = {"value": spo2, "score": spo2_score,
                             "scale": "scale2" if use_scale2 else "scale1"}

    # Supplemental O2
    breakdown["supplemental_o2"] = {"value": on_supplemental_o2,
                                     "score": _score_on_air(on_supplemental_o2)}

    # Systolic BP
    sbp = vitals.get("sbp")
    if sbp is not None:
        breakdown["systolic_bp"] = {"value": sbp, "score": _score_sbp(sbp)}

    # Heart rate
    hr = vitals.get("hr")
    if hr is not None:
        breakdown["heart_rate"] = {"value": hr, "score": _score_hr(hr)}

    # Consciousness (GCS)
    gcs = vitals.get("gcs")
    if gcs is not None:
        breakdown["consciousness"] = {"value": gcs, "score": _score_consciousness(gcs)}

    # Temperature
    temp = vitals.get("temp")
    if temp is not None:
        breakdown["temperature"] = {"value": temp, "score": _score_temp(temp)}

    # Total score
    total = sum(item["score"] for item in breakdown.values())

    # Risk level
    any_param_3 = any(item["score"] >= 3 for item in breakdown.values())
    if total >= 7:
        risk = "HIGH"
        clinical_response = "Urgent clinical review required"
    elif total >= 5 or any_param_3:
        risk = "MEDIUM"
        clinical_response = "Urgent ward-based response required"
    else:
        risk = "LOW"
        clinical_response = "Routine monitoring"

    return {
        "total_score": total,
        "risk_level": risk,
        "clinical_response": clinical_response,
        "breakdown": breakdown,
        "any_parameter_score_3": any_param_3,
    }


def calculate_news2_from_observations(
    observations: list[dict],
    on_supplemental_o2: bool = False,
    use_scale2: bool = False,
) -> dict:
    """Convenience: calculate NEWS2 directly from FHIR Observations."""
    vitals = extract_latest_vitals(observations)
    return calculate_news2(vitals, on_supplemental_o2, use_scale2)
