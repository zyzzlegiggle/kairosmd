"""
KairosMD - Seed script to populate HAPI FHIR with test data.
Creates a Practitioner, Patients, Appointments, Vitals, Labs, and Clinical Notes.
"""

import asyncio
import uuid
import random
from datetime import datetime, timedelta, timezone
from kairosmd.fhir_client import FHIRClient

async def seed():
    client = FHIRClient()
    print("Seeding test data to HAPI FHIR...")

    try:
        # 1. Create a Practitioner (The Doctor)
        practitioner = {
            "resourceType": "Practitioner",
            "name": [{"family": "Kairos", "given": ["Doctor"]}],
            "identifier": [{"system": "http://kairosmd.ai/id", "value": str(uuid.uuid4())[:8]}]
        }
        resp = await (await client._get_client()).post("/Practitioner", json=practitioner)
        prac_id = resp.json()["id"]
        print(f"Created Practitioner: {prac_id}")

        # 2. Create Patients with different risk profiles
        profiles = [
            {"name": "Stable Patient", "vitals": "normal", "labs": "normal", "notes": "Patient is doing well.", "app_offset": 1},
            {"name": "Critical Patient", "vitals": "critical", "labs": "abnormal", "notes": "Patient reporting severe chest pain and dizziness.", "app_offset": 2},
            {"name": "Deteriorating Patient", "vitals": "abnormal", "labs": "normal", "notes": "Patient seems confused and agitated overnight.", "app_offset": 3},
            {"name": "Routine Follow-up", "vitals": "normal", "labs": "normal", "notes": "Routine post-op follow up.", "app_offset": 4},
        ]

        patient_ids = []
        for profile in profiles:
            p_data = {
                "resourceType": "Patient",
                "name": [{"family": profile["name"].split()[-1], "given": [profile["name"].split()[0]]}],
                "gender": random.choice(["male", "female"]),
                "birthDate": "1980-01-01"
            }
            p_resp = await (await client._get_client()).post("/Patient", json=p_data)
            pid = p_resp.json()["id"]
            patient_ids.append(pid)
            print(f"Created Patient: {pid} ({profile['name']})")

            # Create Appointment
            start_time = (datetime.now(timezone.utc) + timedelta(hours=profile["app_offset"])).isoformat()
            appt = {
                "resourceType": "Appointment",
                "status": "booked",
                "start": start_time,
                "end": (datetime.now(timezone.utc) + timedelta(hours=profile["app_offset"], minutes=30)).isoformat(),
                "participant": [
                    {"actor": {"reference": f"Patient/{pid}"}, "status": "accepted"},
                    {"actor": {"reference": f"Practitioner/{prac_id}"}, "status": "accepted"}
                ]
            }
            await (await client._get_client()).post("/Appointment", json=appt)

            # Add Vitals (Observation)
            if profile["vitals"] == "critical":
                hr, sbp, dbp = 155, 85, 45 # Critical high HR, low BP
            elif profile["vitals"] == "abnormal":
                hr, sbp, dbp = 110, 145, 95 # Mildly elevated
            else:
                hr, sbp, dbp = 75, 120, 80  # Normal

            vitals_obs = [
                {"code": "8867-4", "display": "Heart Rate", "value": hr, "unit": "bpm"},
                {"code": "8480-6", "display": "Systolic BP", "value": sbp, "unit": "mmHg"},
                {"code": "8462-4", "display": "Diastolic BP", "value": dbp, "unit": "mmHg"},
            ]
            for v in vitals_obs:
                obs = {
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
                    "code": {"coding": [{"system": "http://loinc.org", "code": v["code"], "display": v["display"]}]},
                    "subject": {"reference": f"Patient/{pid}"},
                    "effectiveDateTime": datetime.now(timezone.utc).isoformat(),
                    "valueQuantity": {"value": v["value"], "unit": v["unit"], "system": "http://unitsofmeasure.org", "code": v["unit"]}
                }
                await (await client._get_client()).post("/Observation", json=obs)

            # Add Notes (DocumentReference)
            note = {
                "resourceType": "DocumentReference",
                "status": "current",
                "subject": {"reference": f"Patient/{pid}"},
                "date": datetime.now(timezone.utc).isoformat(),
                "description": profile["notes"],
                "content": [{"attachment": {"contentType": "text/plain", "data": ""}}] # Placeholder
            }
            await (await client._get_client()).post("/DocumentReference", json=note)

        print(f"\nSeeding complete!")
        print(f"Set your .env DEFAULT_PRACTITIONER_ID={prac_id}")
        
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(seed())
