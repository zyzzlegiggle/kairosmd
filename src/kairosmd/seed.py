"""Seed inpatient ward data into HAPI FHIR R4 server."""

import asyncio
import base64
import random
from datetime import datetime, timedelta, timezone

from kairosmd.fhir_client import FHIRClient
from kairosmd.seed_data import PROFILES

NOW = datetime.now(timezone.utc)

# LOINC display names for vital signs
VITAL_DISPLAY = {
    "8480-6": "Systolic BP", "8462-4": "Diastolic BP",
    "8867-4": "Heart Rate", "9279-1": "Respiratory Rate",
    "2708-6": "SpO2", "8310-5": "Body Temperature",
    "9269-2": "Glasgow Coma Scale",
}

# LOINC display names for common labs
LAB_DISPLAY = {
    "6690-2": "WBC", "718-7": "Hemoglobin", "777-3": "Platelets",
    "2951-2": "Sodium", "2823-3": "Potassium", "2160-0": "Creatinine",
    "3094-0": "BUN", "2345-7": "Glucose", "1988-5": "CRP",
    "33959-8": "Procalcitonin", "1742-6": "ALT", "1920-8": "AST",
    "30934-4": "BNP", "2069-3": "Troponin I",
    "48065-7": "D-Dimer", "2744-1": "pH", "20591-1": "Ketones",
    "2019-8": "pCO2", "2703-7": "pO2",
}


async def _post(http, resource_type, body):
    """POST a FHIR resource, handling duplicates gracefully."""
    resp = await http.post(f"/{resource_type}", json=body)
    if resp.status_code in (200, 201):
        rid = resp.json().get("id")
        if not rid:
            loc = resp.headers.get("Location", "")
            if f"/{resource_type}/" in loc:
                rid = loc.split(f"/{resource_type}/")[1].split("/")[0]
        return rid
    if "duplicating existing resource" in resp.text:
        try:
            rid = resp.text.split(f"{resource_type}/")[1].split("<")[0].strip()
            return rid
        except Exception:
            pass
    print(f"    WARN: Failed {resource_type}: {resp.status_code}")
    return None


async def seed():
    client = FHIRClient()
    http = await client._get_client()

    print(f"Seeding {len(PROFILES)} inpatient patients...")

    # 1. Practitioner (consultant)
    prac = {
        "resourceType": "Practitioner", "active": True,
        "name": [{"family": "Reynolds", "given": ["Sarah"], "prefix": ["Dr"]}],
    }
    prac_id = await _post(http, "Practitioner", prac)
    if not prac_id:
        print("FATAL: Could not create Practitioner.")
        return
    print(f"Practitioner: {prac_id}")

    for i, p in enumerate(PROFILES):
        given, family = p["name"]
        label = f"{given} {family}"
        print(f"  [{i+1}/{len(PROFILES)}] {label}...")

        # 2. Patient
        pt = {
            "resourceType": "Patient", "active": True,
            "name": [{"family": family, "given": [given]}],
            "gender": p["gender"], "birthDate": p["dob"],
        }
        pid = await _post(http, "Patient", pt)
        if not pid:
            continue

        # 3. Encounter (inpatient)
        admit = NOW - timedelta(days=p["admission_days_ago"])
        enc = {
            "resourceType": "Encounter", "status": "in-progress",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                      "code": "IMP", "display": "inpatient encounter"},
            "subject": {"reference": f"Patient/{pid}"},
            "participant": [{"individual": {"reference": f"Practitioner/{prac_id}",
                                            "display": "Dr Sarah Reynolds"}}],
            "period": {"start": admit.isoformat()},
            "reasonCode": [{"text": p["encounter_reason"]}],
            "location": [{"location": {"display": f"{p['ward']} - {p['bed']}"},
                          "status": "active"}],
        }
        enc_id = await _post(http, "Encounter", enc)

        # 4. Conditions
        for icd, display in p["conditions"]:
            cond = {
                "resourceType": "Condition",
                "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                               "code": "active"}]},
                "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm",
                                     "code": icd, "display": display}], "text": display},
                "subject": {"reference": f"Patient/{pid}"},
            }
            if enc_id:
                cond["encounter"] = {"reference": f"Encounter/{enc_id}"}
            await _post(http, "Condition", cond)

        # 5. Allergies
        for substance, reaction in p.get("allergies", []):
            allergy = {
                "resourceType": "AllergyIntolerance",
                "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                                               "code": "active"}]},
                "code": {"text": substance},
                "patient": {"reference": f"Patient/{pid}"},
                "reaction": [{"manifestation": [{"text": reaction}]}],
            }
            await _post(http, "AllergyIntolerance", allergy)

        # 6. Medications
        med_ids = {}
        for med_name, rxnorm, dose, freq, route, status in p.get("medications", []):
            med_req = {
                "resourceType": "MedicationRequest", "status": status,
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                "code": str(rxnorm), "display": med_name}],
                    "text": med_name},
                "subject": {"reference": f"Patient/{pid}"},
                "dosageInstruction": [{"text": f"{dose} {freq}",
                                       "route": {"text": route}}],
            }
            if enc_id:
                med_req["encounter"] = {"reference": f"Encounter/{enc_id}"}
            mid = await _post(http, "MedicationRequest", med_req)
            if mid:
                med_ids[med_name] = mid

        # 7. MedicationAdministration
        for med_name, hours_ago, status in p.get("med_admin", []):
            admin_time = (NOW - timedelta(hours=hours_ago)).isoformat()
            admin = {
                "resourceType": "MedicationAdministration",
                "status": "completed" if status == "given" else ("not-done" if status == "missed" else "on-hold"),
                "medicationCodeableConcept": {"text": med_name},
                "subject": {"reference": f"Patient/{pid}"},
                "effectiveDateTime": admin_time,
            }
            if status != "given":
                admin["statusReason"] = [{"text": f"Dose {status}"}]
            await _post(http, "MedicationAdministration", admin)

        # 8. Vitals
        for hours_ago, sbp, dbp, hr, rr, spo2, temp, gcs in p["vitals"]:
            eff = (NOW - timedelta(hours=hours_ago, minutes=random.randint(0, 30))).isoformat()
            vitals_data = [
                ("8480-6", sbp, "mmHg"), ("8462-4", dbp, "mmHg"),
                ("8867-4", hr, "bpm"), ("9279-1", rr, "breaths/min"),
                ("2708-6", spo2, "%"), ("8310-5", temp, "Cel"),
                ("9269-2", gcs, "{score}"),
            ]
            for loinc, val, unit in vitals_data:
                obs = {
                    "resourceType": "Observation", "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                              "code": "vital-signs"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": loinc,
                                         "display": VITAL_DISPLAY.get(loinc, loinc)}]},
                    "subject": {"reference": f"Patient/{pid}"},
                    "effectiveDateTime": eff,
                    "valueQuantity": {"value": val, "unit": unit,
                                      "system": "http://unitsofmeasure.org", "code": unit},
                }
                if enc_id:
                    obs["encounter"] = {"reference": f"Encounter/{enc_id}"}
                await _post(http, "Observation", obs)

        # 9. Labs
        for hours_ago, lab_dict in p["labs"]:
            eff = (NOW - timedelta(hours=hours_ago, minutes=random.randint(0, 30))).isoformat()
            for loinc, (val, unit) in lab_dict.items():
                obs = {
                    "resourceType": "Observation", "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                              "code": "laboratory"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": loinc,
                                         "display": LAB_DISPLAY.get(loinc, loinc)}]},
                    "subject": {"reference": f"Patient/{pid}"},
                    "effectiveDateTime": eff,
                    "valueQuantity": {"value": val, "unit": unit,
                                      "system": "http://unitsofmeasure.org", "code": unit},
                }
                if enc_id:
                    obs["encounter"] = {"reference": f"Encounter/{enc_id}"}
                await _post(http, "Observation", obs)

        # 10. Notes (DocumentReference)
        notes = p.get("notes", {})
        # Admission note
        if notes.get("admission"):
            doc = {
                "resourceType": "DocumentReference", "status": "current",
                "type": {"text": "Admission Clerking Note"},
                "subject": {"reference": f"Patient/{pid}"},
                "date": admit.isoformat(),
                "description": "Admission Clerking Note",
                "content": [{"attachment": {
                    "contentType": "text/plain",
                    "data": base64.b64encode(notes["admission"].encode()).decode(),
                }}],
            }
            await _post(http, "DocumentReference", doc)

        # Nursing notes
        for hours_ago, text in notes.get("nursing", []):
            doc = {
                "resourceType": "DocumentReference", "status": "current",
                "type": {"text": "Nursing Shift Note"},
                "subject": {"reference": f"Patient/{pid}"},
                "date": (NOW - timedelta(hours=hours_ago)).isoformat(),
                "description": "Nursing Shift Note",
                "content": [{"attachment": {
                    "contentType": "text/plain",
                    "data": base64.b64encode(text.encode()).decode(),
                }}],
            }
            await _post(http, "DocumentReference", doc)

        # Progress note
        if notes.get("progress"):
            doc = {
                "resourceType": "DocumentReference", "status": "current",
                "type": {"text": "Medical Progress Note"},
                "subject": {"reference": f"Patient/{pid}"},
                "date": (NOW - timedelta(hours=6)).isoformat(),
                "description": "Medical Progress Note",
                "content": [{"attachment": {
                    "contentType": "text/plain",
                    "data": base64.b64encode(notes["progress"].encode()).decode(),
                }}],
            }
            await _post(http, "DocumentReference", doc)

        # 11. Procedures
        for proc_name, proc_date in p.get("procedures", []):
            proc = {
                "resourceType": "Procedure", "status": "completed",
                "code": {"text": proc_name},
                "subject": {"reference": f"Patient/{pid}"},
                "performedDateTime": proc_date,
            }
            if enc_id:
                proc["encounter"] = {"reference": f"Encounter/{enc_id}"}
            await _post(http, "Procedure", proc)

        # 12. DiagnosticReport
        for report_name, report_date, report_text in p.get("diagnostics", []):
            dr = {
                "resourceType": "DiagnosticReport", "status": "final",
                "code": {"text": report_name},
                "subject": {"reference": f"Patient/{pid}"},
                "effectiveDateTime": report_date,
                "conclusion": report_text,
            }
            if enc_id:
                dr["encounter"] = {"reference": f"Encounter/{enc_id}"}
            await _post(http, "DiagnosticReport", dr)

        # 13. CareTeam
        members = p.get("care_team", [])
        if members:
            ct = {
                "resourceType": "CareTeam", "status": "active",
                "subject": {"reference": f"Patient/{pid}"},
                "participant": [
                    {"role": [{"text": role}],
                     "member": {"display": f"{name} ({dept})"}}
                    for name, role, dept in members
                ],
            }
            if enc_id:
                ct["encounter"] = {"reference": f"Encounter/{enc_id}"}
            await _post(http, "CareTeam", ct)

        # 14. Flags
        for flag_code, flag_status, flag_text in p.get("flags", []):
            flag = {
                "resourceType": "Flag", "status": "active",
                "category": [{"text": flag_code}],
                "code": {"text": f"{flag_code}: {flag_status} - {flag_text}"},
                "subject": {"reference": f"Patient/{pid}"},
            }
            await _post(http, "Flag", flag)

        print(f"    Done: {label}")
        await asyncio.sleep(0.3)  # rate limit gap

    await client.close()
    print(f"\nDone. Set DEFAULT_PRACTITIONER_ID={prac_id} in .env")


if __name__ == "__main__":
    asyncio.run(seed())
