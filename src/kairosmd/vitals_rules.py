"""Vital-sign reference ranges and flagging logic.

Ranges based on publicly documented adult clinical guidelines
(AHA/ACC, WHO). These are for decision-support only - never a
substitute for clinical judgement.
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    NORMAL = "normal"
    ABNORMAL = "abnormal"
    CRITICAL = "critical"


@dataclass(frozen=True)
class VitalRange:
    name: str
    unit: str
    normal_low: float
    normal_high: float
    critical_low: float | None = None
    critical_high: float | None = None


# -- Reference ranges keyed by LOINC code ------------------------------
VITAL_RANGES: dict[str, VitalRange] = {
    "8867-4":  VitalRange("Heart Rate",        "bpm",          60,  100,  40,   150),
    "8480-6":  VitalRange("Systolic BP",        "mmHg",         90,  140,  80,   200),
    "8462-4":  VitalRange("Diastolic BP",       "mmHg",         60,   90,  40,   120),
    "8310-5":  VitalRange("Body Temperature",   "deg C",      36.1, 37.8, 35.0,  40.0),
    "9279-1":  VitalRange("Respiratory Rate",   "breaths/min",  12,   20,   8,    35),
    "2708-6":  VitalRange("SpO2",               "%",            95,  100,  88,   None),
}


def assess_vital(loinc_code: str, value: float) -> tuple[Severity, str]:
    """Return (severity, human-readable message) for a single vital reading."""
    vr = VITAL_RANGES.get(loinc_code)
    if vr is None:
        return Severity.NORMAL, f"Unknown vital code {loinc_code}"

    if vr.critical_low is not None and value < vr.critical_low:
        return Severity.CRITICAL, (
            f"{vr.name} critically low: {value} {vr.unit} "
            f"(critical <{vr.critical_low})"
        )
    if vr.critical_high is not None and value > vr.critical_high:
        return Severity.CRITICAL, (
            f"{vr.name} critically high: {value} {vr.unit} "
            f"(critical >{vr.critical_high})"
        )

    if value < vr.normal_low:
        return Severity.ABNORMAL, (
            f"{vr.name} below normal: {value} {vr.unit} "
            f"(range {vr.normal_low}-{vr.normal_high})"
        )
    if value > vr.normal_high:
        return Severity.ABNORMAL, (
            f"{vr.name} above normal: {value} {vr.unit} "
            f"(range {vr.normal_low}-{vr.normal_high})"
        )

    return Severity.NORMAL, f"{vr.name} normal: {value} {vr.unit}"


# -- Process a list of FHIR Observation resources ----------------------
def flag_vitals(observations: list[dict]) -> list[dict]:
    """Walk through FHIR Observation resources, assess each value."""
    results: list[dict] = []

    for obs in observations:
        effective = obs.get("effectiveDateTime", "")

        # handle top-level valueQuantity (simple vitals)
        vq = obs.get("valueQuantity")
        codings = obs.get("code", {}).get("coding", [])
        loinc = _extract_loinc(codings)

        if vq and loinc:
            _append_result(results, loinc, codings, vq, effective)

        # handle component-based (e.g. blood pressure panel)
        for comp in obs.get("component", []):
            comp_codings = comp.get("code", {}).get("coding", [])
            comp_loinc = _extract_loinc(comp_codings)
            comp_vq = comp.get("valueQuantity")
            if comp_loinc and comp_vq:
                _append_result(results, comp_loinc, comp_codings, comp_vq, effective)

    return results


# -- internal helpers --------------------------------------------------
def _extract_loinc(codings: list[dict]) -> str | None:
    for c in codings:
        if c.get("system") == "http://loinc.org":
            return c["code"]
    return None


def _append_result(
    results: list[dict],
    loinc: str,
    codings: list[dict],
    vq: dict,
    effective: str,
):
    value = vq.get("value")
    if value is None:
        return
    display = next(
        (c.get("display", loinc) for c in codings if c.get("system") == "http://loinc.org"),
        loinc,
    )
    severity, message = assess_vital(loinc, float(value))
    results.append({
        "code": loinc,
        "display": display,
        "value": value,
        "unit": vq.get("unit", ""),
        "severity": severity.value,
        "message": message,
        "effective": effective,
    })
