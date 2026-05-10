"""Debug: Check what encounters actually exist on the FHIR server for our patients."""
import asyncio
import json
from kairosmd.fhir_client import FHIRClient

fhir = FHIRClient()

async def main():
    # Known patient IDs from the seed output
    patient_ids = ["132024923", "132024980", "132025034"]
    
    print("=== Checking encounters for seeded patients ===\n")
    for pid in patient_ids:
        print(f"--- Patient {pid} ---")
        
        # Get ALL encounters (not filtered)
        encs = await fhir.search("Encounter", {"patient": pid, "_count": "5"})
        print(f"  Total encounters found: {len(encs)}")
        for enc in encs:
            print(f"  ID: {enc.get('id')}")
            print(f"  Status: {enc.get('status')}")
            print(f"  Class: {enc.get('class', {})}")
            locs = enc.get("location", [])
            for l in locs:
                print(f"  Location display: '{l.get('location', {}).get('display', 'NONE')}'")
            print()
    
    # Also check: what does get_encounters return?
    print("\n=== What does get_encounters(status='in-progress') return? ===")
    all_encs = await fhir.get_encounters(status="in-progress")
    print(f"Total IMP encounters: {len(all_encs)}")
    ward_count = 0
    for enc in all_encs[:5]:
        locs = enc.get("location", [])
        loc_display = " ".join([l.get("location", {}).get("display", "") for l in locs])
        subj = enc.get("subject", {}).get("reference", "?")
        has_ward = "General Medicine Ward" in loc_display
        if has_ward:
            ward_count += 1
        print(f"  {subj} | status={enc.get('status')} | location='{loc_display}' | match={has_ward}")
    print(f"\nMatching 'General Medicine Ward': {ward_count} out of {len(all_encs)}")

asyncio.run(main())
