"""Seed HAPI FHIR with 15 realistic chronic patient scenarios."""

import asyncio
import base64
import random
from datetime import datetime, timedelta, timezone
from kairosmd.fhir_client import FHIRClient
from kairosmd.seed_data import PROFILES

LOINC_DISPLAY = {
    "8480-6": "Systolic Blood Pressure", "8462-4": "Diastolic Blood Pressure",
    "8867-4": "Heart Rate", "9279-1": "Respiratory Rate",
    "2708-6": "Oxygen Saturation", "8310-5": "Body Temperature",
    "6690-2": "WBC", "718-7": "Hemoglobin", "777-3": "Platelets",
    "2951-2": "Sodium", "2823-3": "Potassium", "2160-0": "Creatinine",
    "3094-0": "BUN", "2345-7": "Glucose", "1742-6": "ALT", "1920-8": "AST",
    "30934-4": "BNP", "2069-3": "Troponin I",
}


async def seed():
    client = FHIRClient()
    http = await client._get_client()
    now = datetime.now(timezone.utc)
    today = now.date()

    print("Seeding 15 patients to HAPI FHIR...")

    # Create practitioner
    prac = {"resourceType": "Practitioner",
            "name": [{"family": "Kairos", "given": ["Doctor"]}]}
    resp = await http.post("/Practitioner", json=prac)
    
    if resp.status_code not in (200, 201):
        # Handle HAPI duplicate resource error
        error_text = resp.text
        if "Can not create resource duplicating existing resource:" in error_text:
            try:
                # Extract Practitioner/12345
                parts = error_text.split("Practitioner/")[1].split("</td>")[0].split(" <")[0].strip()
                # Remove any HTML tags if present
                prac_id = parts.split("<")[0].strip()
                print(f"Using existing Practitioner: {prac_id}")
            except Exception:
                print(f"Failed to create practitioner: {error_text}")
                return
        else:
            print(f"Failed to create practitioner: {error_text}")
            return
    else:
        resp_json = resp.json()
        prac_id = resp_json.get("id")
        
        if not prac_id:
            # Try to extract from Location header
            location = resp.headers.get("Location", "")
            if "/Practitioner/" in location:
                prac_id = location.split("/Practitioner/")[1].split("/")[0]
            
    if not prac_id:
        print("Could not determine Practitioner ID from response.")
        return
        
    print(f"Practitioner: {prac_id}")

    for i, p in enumerate(PROFILES):
        given, family = p["name"]
        label = f"{given} {family}"

        # 1. Patient
        pt = {"resourceType": "Patient",
              "name": [{"family": family, "given": [given]}],
              "gender": p["gender"], "birthDate": p["dob"]}
        resp = await http.post("/Patient", json=pt)
        pid = None
        if resp.status_code in (200, 201):
            pid = resp.json().get("id")
            if not pid:
                location = resp.headers.get("Location", "")
                if "/Patient/" in location:
                    pid = location.split("/Patient/")[1].split("/")[0]
        elif "Can not create resource duplicating existing resource:" in resp.text:
            try:
                # Extract Patient/12345
                parts = resp.text.split("Patient/")[1].split("</td>")[0].split(" <")[0].strip()
                pid = parts.split("<")[0].strip()
                print(f"  Using existing Patient: {pid}")
            except Exception:
                pass
        
        if not pid:
            print(f"  Failed to create patient {label}: {resp.text}")
            continue

        # 2. Appointment - Randomize minutes and ensure it's today
        minute = random.choice([0, 15, 30, 45])
        start = datetime(today.year, today.month, today.day,
                         p["appt_hour"], minute, tzinfo=timezone.utc)
        appt = {"resourceType": "Appointment", "status": "booked",
                "start": start.isoformat(),
                "end": (start + timedelta(minutes=30)).isoformat(),
                "description": p["appt_reason"],
                "participant": [
                    {"actor": {"reference": f"Patient/{pid}"}, "status": "accepted"},
                    {"actor": {"reference": f"Practitioner/{prac_id}"}, "status": "accepted"},
                ]}
        await http.post("/Appointment", json=appt)

        # 3. Conditions
        for icd, display in p["conditions"]:
            cond = {"resourceType": "Condition",
                    "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                                   "code": "active"}]},
                    "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm",
                                         "code": icd, "display": display}],
                             "text": display},
                    "subject": {"reference": f"Patient/{pid}"}}
            await http.post("/Condition", json=cond)

        # 4. Allergies
        for substance, reaction in p["allergies"]:
            allergy = {"resourceType": "AllergyIntolerance",
                       "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                                                      "code": "active"}]},
                       "code": {"text": substance},
                       "patient": {"reference": f"Patient/{pid}"},
                       "reaction": [{"description": reaction}]}
            await http.post("/AllergyIntolerance", json=allergy)

        # 5. Medications
        for med_name, rxcui, dose, freq, route in p["medications"]:
            med = {"resourceType": "MedicationRequest", "status": "active",
                   "intent": "order",
                   "medicationCodeableConcept": {
                       "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                                   "code": str(rxcui), "display": med_name}],
                       "text": med_name},
                   "subject": {"reference": f"Patient/{pid}"},
                   "dosageInstruction": [{"text": f"{dose} {freq}",
                                          "route": {"text": route}}]}
            await http.post("/MedicationRequest", json=med)

        # 6. Vitals (each time point creates individual observations)
        for days_ago, sbp, dbp, hr, rr, spo2, temp in p["vitals"]:
            # Randomize the exact time within that day
            offset_hours = random.randint(0, 23)
            offset_mins = random.randint(0, 59)
            eff = (now - timedelta(days=days_ago, hours=offset_hours, minutes=offset_mins)).isoformat()
            vitals_data = [
                ("8480-6", sbp, "mmHg"), ("8462-4", dbp, "mmHg"),
                ("8867-4", hr, "bpm"), ("9279-1", rr, "breaths/min"),
                ("2708-6", spo2, "%"), ("8310-5", temp, "deg C"),
            ]
            for loinc, val, unit in vitals_data:
                obs = {"resourceType": "Observation", "status": "final",
                       "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                                  "code": "vital-signs"}]}],
                       "code": {"coding": [{"system": "http://loinc.org",
                                            "code": loinc,
                                            "display": LOINC_DISPLAY.get(loinc, loinc)}]},
                       "subject": {"reference": f"Patient/{pid}"},
                       "effectiveDateTime": eff,
                       "valueQuantity": {"value": val, "unit": unit,
                                         "system": "http://unitsofmeasure.org"}}
                await http.post("/Observation", json=obs)

        # 7. Labs
        for days_ago, lab_dict in p["labs"]:
            # Randomize the exact time within that day
            offset_hours = random.randint(0, 23)
            offset_mins = random.randint(0, 59)
            eff = (now - timedelta(days=days_ago, hours=offset_hours, minutes=offset_mins)).isoformat()
            for loinc, (val, unit) in lab_dict.items():
                obs = {"resourceType": "Observation", "status": "final",
                       "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                                  "code": "laboratory"}]}],
                       "code": {"coding": [{"system": "http://loinc.org",
                                            "code": loinc,
                                            "display": LOINC_DISPLAY.get(loinc, loinc)}]},
                       "subject": {"reference": f"Patient/{pid}"},
                       "effectiveDateTime": eff,
                       "valueQuantity": {"value": val, "unit": unit,
                                         "system": "http://unitsofmeasure.org"}}
                await http.post("/Observation", json=obs)

        # 8. Clinical notes
        note_b64 = base64.b64encode(p["notes"].encode()).decode()
        doc = {"resourceType": "DocumentReference", "status": "current",
               "subject": {"reference": f"Patient/{pid}"},
               "date": now.isoformat(),
               "description": p["notes"][:200],
               "content": [{"attachment": {"contentType": "text/plain",
                                           "data": note_b64}}]}
        await http.post("/DocumentReference", json=doc)

        print(f"  [{i+1}/15] {label} -> Patient/{pid}")

    await client.close()
    print(f"\nDone. Set DEFAULT_PRACTITIONER_ID={prac_id} in .env")


if __name__ == "__main__":
    asyncio.run(seed())
