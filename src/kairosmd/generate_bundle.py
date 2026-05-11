import json
import uuid
import random
from datetime import datetime, timedelta, timezone

# We'll import scenarios and constants from seed_data
from kairosmd.seed_data import SCENARIOS, CONSULTANTS, NURSES, NOW

def get_vitals_for_trend(trend: str, hour: int):
    # Base values for a healthy-ish adult
    rr, spo2, sbp, hr, temp = 16, 97, 125, 75, 36.8
    if trend == "deteriorating":
        rr += (hour // 4) * 2
        spo2 -= (hour // 4) * 2
        sbp -= (hour // 4) * 5
        hr += (hour // 4) * 5
        temp = 38.5 if hour > 12 else 37.2
    elif trend == "improving":
        rr = max(16, 24 - (hour // 4) * 2)
        spo2 = min(98, 88 + (hour // 4) * 2)
        hr = max(72, 110 - (hour // 4) * 5)
    return {
        "9279-1": rr,    # RR
        "59408-5": spo2, # SpO2
        "8480-6": sbp,   # SBP
        "8867-4": hr,    # HR
        "8310-5": temp,  # Temp
        "67775-7": 1.0   # AVPU (Alert)
    }

def generate_bundle():
    entries = []
    
    print(f"--- Generating FHIR Transaction Bundle for {len(SCENARIOS)} scenarios ---")

    for s in SCENARIOS:
        p_info = s["patient"]
        bed = s["bed"]
        
        # 1. Patient
        patient_id = str(uuid.uuid4())
        patient_ref = f"urn:uuid:{patient_id}"
        
        entries.append({
            "fullUrl": patient_ref,
            "resource": {
                "resourceType": "Patient",
                "id": patient_id,
                "name": [{"text": p_info["name"]}],
                "gender": p_info["gender"],
                "birthDate": p_info["dob"]
            },
            "request": {"method": "POST", "url": "Patient"}
        })

        # 2. Encounter
        encounter_id = str(uuid.uuid4())
        encounter_ref = f"urn:uuid:{encounter_id}"
        start_time = (NOW - timedelta(days=p_info["day"])).isoformat()
        
        entries.append({
            "fullUrl": encounter_ref,
            "resource": {
                "resourceType": "Encounter",
                "id": encounter_id,
                "status": "in-progress",
                "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "IMP", "display": "inpatient"},
                "subject": {"reference": patient_ref},
                "period": {"start": start_time},
                "reasonCode": [{"text": p_info["condition"]}],
                "location": [{
                    "location": {"display": f"General Medicine Ward - Bed {bed}"},
                    "status": "active"
                }]
            },
            "request": {"method": "POST", "url": "Encounter"}
        })

        # 3. CareTeam
        careteam_id = str(uuid.uuid4())
        members = [
            {"name": p_info["consultant"]["name"], "role": "Responsible Consultant"},
            {"name": "Dr. Mike", "role": "Lead Consultant (MDS)"},
            {"name": random.choice(NURSES), "role": "Primary Nurse"}
        ]
        
        entries.append({
            "fullUrl": f"urn:uuid:{careteam_id}",
            "resource": {
                "resourceType": "CareTeam",
                "id": careteam_id,
                "status": "active",
                "subject": {"reference": patient_ref},
                "participant": [
                    {"role": [{"text": m["role"]}], "member": {"display": m["name"]}}
                    for m in members
                ]
            },
            "request": {"method": "POST", "url": "CareTeam"}
        })

        # 4. Flags
        for f in s.get("flags", []):
            flag_id = str(uuid.uuid4())
            entries.append({
                "fullUrl": f"urn:uuid:{flag_id}",
                "resource": {
                    "resourceType": "Flag",
                    "id": flag_id,
                    "status": "active",
                    "category": [{"text": "Clinical Safety"}],
                    "code": {"text": f"{f['code']}: {f['detail']}"},
                    "subject": {"reference": patient_ref}
                },
                "request": {"method": "POST", "url": "Flag"}
            })

        # 5. Allergies
        for a in s.get("allergies", []):
            allergy_id = str(uuid.uuid4())
            entries.append({
                "fullUrl": f"urn:uuid:{allergy_id}",
                "resource": {
                    "resourceType": "AllergyIntolerance",
                    "id": allergy_id,
                    "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
                    "criticality": a.get("criticality", "high"),
                    "code": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": a["code"]}], "text": a["name"]},
                    "patient": {"reference": patient_ref}
                },
                "request": {"method": "POST", "url": "AllergyIntolerance"}
            })

        # 6. Vitals (6 time points in last 24h)
        for h in [0, 4, 8, 12, 16, 20]:
            v_time = (NOW - timedelta(hours=24-h)).isoformat()
            vitals = get_vitals_for_trend(s.get("vitals_trend", "stable"), h)
            for code, val in vitals.items():
                obs_id = str(uuid.uuid4())
                category = "vital-signs" if code != "67775-7" else "clinical-test"
                entries.append({
                    "fullUrl": f"urn:uuid:{obs_id}",
                    "resource": {
                        "resourceType": "Observation",
                        "id": obs_id,
                        "status": "final",
                        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
                        "code": {"coding": [{"system": "http://loinc.org", "code": code}]},
                        "subject": {"reference": patient_ref},
                        "encounter": {"reference": encounter_ref},
                        "effectiveDateTime": v_time,
                        "valueQuantity": {"value": val}
                    },
                    "request": {"method": "POST", "url": "Observation"}
                })

        # 7. Labs
        for lab in s.get("labs", []):
            lab_id = str(uuid.uuid4())
            entries.append({
                "fullUrl": f"urn:uuid:{lab_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": lab_id,
                    "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": lab["code"]}], "text": lab["name"]},
                    "subject": {"reference": patient_ref},
                    "effectiveDateTime": (NOW - timedelta(hours=12)).isoformat(),
                    "valueQuantity": {"value": lab["value"], "unit": lab["unit"]},
                    "interpretation": [{"text": lab.get("flag", "")}]
                },
                "request": {"method": "POST", "url": "Observation"}
            })

        # 8. Medications
        for med in s.get("medications", []):
            med_id = str(uuid.uuid4())
            entries.append({
                "fullUrl": f"urn:uuid:{med_id}",
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": med_id,
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": med["code"]}],
                        "text": med["name"]
                    },
                    "subject": {"reference": patient_ref},
                    "dosageInstruction": [{"text": med["dosage"]}]
                },
                "request": {"method": "POST", "url": "MedicationRequest"}
            })

    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": entries
    }
    
    output_file = "ward_bundle.json"
    with open(output_file, "w") as f:
        json.dump(bundle, f, indent=2)
    
    print(f"--- [SUCCESS] Generated FHIR Bundle: {output_file} ---")
    print(f"--- Total resources: {len(entries)} ---")

if __name__ == "__main__":
    generate_bundle()
