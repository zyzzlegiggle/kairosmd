"""Laboratory value reference ranges and flagging logic.

Critical / panic values sourced from publicly documented guidelines
(Labcorp, Mayo Clinic Labs, mainlinehealth.org).  Thresholds vary by
institution - these are representative adult ranges for decision-support.
"""

from __future__ import annotations
from dataclasses import dataclass
from kairosmd.vitals_rules import Severity          # reuse enum


@dataclass(frozen=True)
class LabRange:
    name: str
    unit: str
    normal_low: float
    normal_high: float
    critical_low: float | None = None
    critical_high: float | None = None


# -- Reference ranges keyed by LOINC code ------------------------------
LAB_RANGES: dict[str, LabRange] = {
    "2823-3":  LabRange("Potassium",    "mEq/L",   3.5,   5.0,   2.5,   6.5),
    "2951-2":  LabRange("Sodium",       "mEq/L", 136.0, 145.0, 120.0, 160.0),
    "2345-7":  LabRange("Glucose",      "mmol/L",  4.0,  7.8,   2.0,  30.0),
    "718-7":   LabRange("Hemoglobin",   "g/dL",   12.0,  17.5,   7.0,  20.0),
    "2160-0":  LabRange("Creatinine",   "umol/L",  60.0, 110.0, None, 300.0),
    "6690-2":  LabRange("WBC",          "10*9/L",  4.0,  11.0,   2.0,  30.0),
    "6299-1":  LabRange("WBC",          "10*9/L",  4.0,  11.0,   2.0,  30.0),  # alias
    "777-3":   LabRange("Platelets",    "K/uL",  150.0, 400.0,  50.0, 1000.0),
    "1742-6":  LabRange("ALT",          "U/L",    7.0,   56.0,  None, 1000.0),
    "1920-8":  LabRange("AST",          "U/L",   10.0,   40.0,  None, 1000.0),
    "3094-0":  LabRange("BUN",          "mg/dL",   7.0,   20.0,  None, 100.0),
    "2069-3":  LabRange("Troponin I",   "ng/mL",   0.0,   0.04, None,   0.4),
    # Seed-specific codes
    "1988-5":  LabRange("CRP",          "mg/L",    0.0,   5.0,  None, 200.0),
    "2019-8":  LabRange("Lactate",      "mmol/L",  0.5,   2.0,  None,   4.0),
    "30522-7": LabRange("BNP",          "pg/mL",   0.0, 100.0,  None, 1000.0),
    "33914-3": LabRange("eGFR",         "mL/min", 60.0, 120.0,  15.0, None),
    "6301-5":  LabRange("INR",          "",        0.8,   1.2,  None,   5.0),
    "1960-4":  LabRange("Bicarbonate",  "mmol/L", 22.0,  28.0,  10.0, None),
    "1798-2":  LabRange("Amylase",      "U/L",    30.0, 110.0,  None, 500.0),
}


def assess_lab(loinc_code: str, value: float) -> tuple[Severity, str]:
    """Return (severity, human-readable message) for a lab result."""
    lr = LAB_RANGES.get(loinc_code)
    if lr is None:
        return Severity.NORMAL, f"Unknown lab code {loinc_code}"

    if lr.critical_low is not None and value < lr.critical_low:
        return Severity.CRITICAL, (
            f"{lr.name} critically low: {value} {lr.unit} (critical <{lr.critical_low})"
        )
    if lr.critical_high is not None and value > lr.critical_high:
        return Severity.CRITICAL, (
            f"{lr.name} critically high: {value} {lr.unit} (critical >{lr.critical_high})"
        )
    if value < lr.normal_low:
        return Severity.ABNORMAL, (
            f"{lr.name} below normal: {value} {lr.unit} "
            f"(range {lr.normal_low}-{lr.normal_high})"
        )
    if value > lr.normal_high:
        return Severity.ABNORMAL, (
            f"{lr.name} above normal: {value} {lr.unit} "
            f"(range {lr.normal_low}-{lr.normal_high})"
        )

    return Severity.NORMAL, f"{lr.name} normal: {value} {lr.unit}"


def flag_labs(observations: list[dict]) -> list[dict]:
    """Walk FHIR lab Observations and flag abnormal / critical values."""
    results: list[dict] = []

    for obs in observations:
        codings = obs.get("code", {}).get("coding", [])
        loinc = _extract_loinc(codings)
        vq = obs.get("valueQuantity", {})
        value = vq.get("value")
        effective = obs.get("effectiveDateTime", "")

        if loinc is None or value is None:
            continue

        display = next(
            (c.get("display", loinc) for c in codings if c.get("system") == "http://loinc.org"),
            loinc,
        )
        severity, message = assess_lab(loinc, float(value))
        results.append({
            "code": loinc,
            "display": display,
            "value": value,
            "unit": vq.get("unit", ""),
            "severity": severity.value,
            "message": message,
            "effective": effective,
        })

    return results


def _extract_loinc(codings: list[dict]) -> str | None:
    for c in codings:
        if c.get("system") == "http://loinc.org":
            return c["code"]
    return None
