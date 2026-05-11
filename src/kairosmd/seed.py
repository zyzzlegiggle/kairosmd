"""MDS Scenario-Based Seeder.
Generates 20 high-fidelity clinical scenarios for General Medicine.
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
    """Generate realistic NEWS2 vitals based on a clinical trend with natural jitter."""
    # Base values for a healthy-ish adult
    rr, spo2, sbp, hr, temp = 16, 97, 125, 75, 36.8
    
    if trend == "deteriorating":
        # RR rises, SpO2 falls, SBP falls, HR rises
        rr += (hour // 4) * 2
        spo2 -= (hour // 4) * 2
        sbp -= (hour // 4) * 5
        hr += (hour // 4) * 5
        temp = round(random.uniform(38.0, 39.2), 1) if hour > 12 else round(random.uniform(36.8, 37.5), 1)
    elif trend == "improving":
        # Vitals normalize over time
        rr = max(14, 24 - (hour // 4) * 2)
        spo2 = min(99, 88 + (hour // 4) * 2)
        hr = max(68, 110 - (hour // 4) * 5)
        temp = round(random.uniform(36.4, 37.0), 1)
    else:
        # Stable — small natural fluctuation
        temp = round(random.uniform(36.4, 37.2), 1)
    
    # Add realistic physiological jitter
    rr = max(8, rr + random.randint(-2, 2))
    spo2 = min(100, max(80, spo2 + random.randint(-1, 1)))
    sbp = max(70, sbp + random.randint(-5, 5))
    hr = max(50, hr + random.randint(-4, 4))
    
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

    # Track IDs for manifest (returned at end of function)

    # 3. CareTeam
    members = [
        {"name": p_info["consultant"]["name"], "role": "Responsible Consultant"},
        {"name": "Dr. Mike", "role": "Lead Consultant (MDS)"},
        {"name": "Dr. Amir (HO)", "role": "Junior Doctor"},
        {"name": random.choice(NURSES), "role": "Primary Nurse"}
    ]
    await fhir.create_care_team(pid, members)

    # 4. Flags
    for f in s.get("flags", []):
        await fhir.create_safety_flag(pid, f["code"], f["detail"])

    # 5. Allergies
    for a in s.get("allergies", []):
        await fhir.create_allergy(pid, a["code"], a["name"], criticality=a.get("criticality", "high"))

    # 6. Vitals (6 time points in last 24h)
    for h in [0, 4, 8, 12, 16, 20]:
        # Add random minute offset to simulate real charting times
        minute_jitter = random.randint(-30, 30)
        v_time = (NOW - timedelta(hours=24-h, minutes=minute_jitter)).isoformat()
        vitals = get_vitals_for_trend(s.get("vitals_trend", "stable"), h)
        for code, val in vitals.items():
            await fhir.create_observation(pid, code, val, v_time, eid)

    # 7. Labs
    for i, lab in enumerate(s.get("labs", [])):
        # Admission lab — randomize the baseline (±10-15% of current value)
        baseline_factor = round(random.uniform(0.82, 0.95), 2)
        admission_val = round(lab["value"] * baseline_factor, 1)
        admission_time = (NOW - timedelta(days=p_info["day"], hours=random.randint(0, 4))).isoformat()
        await fhir.create_observation(pid, lab["code"], admission_val, admission_time, eid, display=lab["name"])
        
        # Recent lab — add small jitter to the defined value (±5%)
        jitter = round(lab["value"] * random.uniform(-0.05, 0.05), 1)
        recent_val = round(lab["value"] + jitter, 1)
        recent_time = (NOW - timedelta(hours=random.randint(1, 4))).isoformat()
        await fhir.create_observation(pid, lab["code"], recent_val, recent_time, eid, display=lab["name"])

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
        # Administration (only for active meds — one completed dose)
        if m.get("status", "active") == "active":
            await fhir.create_medication_administration(pid, m["name"], "completed", (NOW - timedelta(hours=4)).isoformat(), random.choice(NURSES))

    # 10. Audit History (Communications)
    if s["bed"] in ["1", "3", "7", "15"]:
        await fhir.create_communication(pid, p_info["consultant"]["name"], "Ward Team", "Critical result reviewed. Plan updated.", (NOW - timedelta(hours=6)).isoformat())

    return {"patient_id": pid, "encounter_id": eid, "bed": bed, "name": p_info["name"], "condition": p_info["condition"]}

async def main():
    import json
    from pathlib import Path

    await purge_ward()
    manifest = []
    for s in SCENARIOS:
        result = await seed_patient_scenario(s)
        manifest.append(result)
        await asyncio.sleep(0.5)

    # Save manifest so the server knows our patient IDs
    manifest_path = Path(__file__).parent / "ward_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\n--- [SEED] MDS General Medicine Seeding Complete! ---")
    print(f"--- [SEED] Manifest saved: {manifest_path} ---")
    print(f"--- [SEED] {len(manifest)} patients registered ---")

if __name__ == "__main__":
    asyncio.run(main())
