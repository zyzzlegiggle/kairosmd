"""MDS Scenario-Based Seeder.
Generates 15 high-fidelity clinical scenarios for Ward 4.
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from kairosmd.fhir_client import FHIRClient
from kairosmd.seed_data import SCENARIOS, CONSULTANTS, NURSES, NOW

fhir = FHIRClient()

async def purge_ward():
    """Skip purge on public HAPI FHIR server — shared data cannot be deleted.
    Our system filters by active IMP encounters so old data won't appear."""
    print("--- [PURGE] Skipping purge (public server). Seeding fresh data. ---")

def get_vitals_for_trend(trend: str, hour: int):
    """Generate realistic NEWS2 vitals based on a clinical trend."""
    # Base values for a healthy-ish adult
    rr, spo2, sbp, hr, temp = 16, 97, 125, 75, 36.8
    
    if trend == "deteriorating":
        # RR rises, SpO2 falls, SBP falls, HR rises
        rr += (hour // 4) * 2
        spo2 -= (hour // 4) * 2
        sbp -= (hour // 4) * 5
        hr += (hour // 4) * 5
        temp = 38.5 if hour > 12 else 37.2
    elif trend == "improving":
        # Vitals normalize
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

async def seed_patient_scenario(s: dict):
    """Seed a full clinical story for one patient."""
    p_info = s["patient"]
    bed = s["bed"]
    print(f"--- [SEED] Bed {bed}: {p_info['name']} ({p_info['condition']}) ---")

    # 1. Patient
    patient = await fhir.create_patient(
        name=p_info["name"],
        gender=p_info["gender"],
        birthDate=p_info["dob"]
    )
    pid = patient["id"]

    # 2. Encounter
    start_time = (NOW - timedelta(days=p_info["day"])).isoformat()
    encounter = await fhir.create_encounter(
        patient_id=pid,
        status="in-progress",
        start_time=start_time,
        ward="General Medicine Ward",
        bed=bed,
        reason=p_info["condition"]
    )
    eid = encounter["id"]

    # 3. CareTeam
    members = [
        {"name": p_info["consultant"]["name"], "role": "Responsible Consultant"},
        {"name": "Dr. Sarah (Registrar)", "role": "Senior Resident"},
        {"name": "Dr. Amir (HO)", "role": "Junior Doctor"},
        {"name": random.choice(NURSES), "role": "Primary Nurse"}
    ]
    await fhir.create_care_team(pid, members)

    # 4. Flags
    for f in s.get("flags", []):
        await fhir.create_safety_flag(pid, f["code"], f["detail"])

    # 5. Allergies
    for a in s.get("allergies", []):
        await fhir.create_allergy(pid, a["code"], a["name"])

    # 6. Vitals (6 time points in last 24h)
    for h in [0, 4, 8, 12, 16, 20]:
        v_time = (NOW - timedelta(hours=24-h)).isoformat()
        vitals = get_vitals_for_trend(s.get("vitals_trend", "stable"), h)
        for code, val in vitals.items():
            await fhir.create_observation(pid, code, val, v_time, eid)

    # 7. Labs
    for i, lab in enumerate(s.get("labs", [])):
        # Admission lab
        await fhir.create_observation(pid, lab["code"], lab["value"] * 0.9, start_time, eid)
        # Recent lab
        await fhir.create_observation(pid, lab["code"], lab["value"], (NOW - timedelta(hours=2)).isoformat(), eid)

    # 8. Notes
    notes = s.get("notes", {})
    if "clerking" in notes:
        await fhir.create_clinical_note(pid, notes["clerking"], "Dr. Amir (HO)")
    if "consultant" in notes:
        await fhir.create_clinical_note(pid, notes["consultant"], p_info["consultant"]["name"])
    if "junior" in notes:
        await fhir.create_clinical_note(pid, notes["junior"], "Dr. Amir (HO)")
    if "specialist" in notes:
        await fhir.create_clinical_note(pid, notes["specialist"], "Specialist Consult")
    
    # Nursing notes (Shift based)
    if "nursing_night" in notes:
        await fhir.create_clinical_note(pid, f"NIGHT SHIFT: {notes['nursing_night']}", random.choice(NURSES))
    if "nursing_morning" in notes:
        await fhir.create_clinical_note(pid, f"MORNING SHIFT: {notes['nursing_morning']}", random.choice(NURSES))
    if "nursing_afternoon" in notes:
        await fhir.create_clinical_note(pid, f"AFTERNOON SHIFT: {notes['nursing_afternoon']}", random.choice(NURSES))

    # 9. Meds
    for m in s.get("meds", []):
        await fhir.create_medication_request(pid, m, p_info["consultant"]["name"])
        # Administration (one completed dose)
        await fhir.create_medication_administration(pid, m["name"], "completed", (NOW - timedelta(hours=4)).isoformat(), random.choice(NURSES))

    # 10. Audit History (Communications)
    if s["bed"] in ["1", "3", "7", "15"]:
        await fhir.create_communication(pid, p_info["consultant"]["name"], "Ward Team", "Critical result reviewed. Plan updated.", (NOW - timedelta(hours=6)).isoformat())

async def main():
    await purge_ward()
    for s in SCENARIOS:
        await seed_patient_scenario(s)
        # Small sleep to be kind to the public server
        await asyncio.sleep(0.5)
    print("\n--- [SEED] MDS Ward 4 Seeding Complete! ---")

if __name__ == "__main__":
    asyncio.run(main())
