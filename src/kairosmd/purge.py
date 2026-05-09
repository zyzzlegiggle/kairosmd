"""Purge all KairosMD related resources from the FHIR server."""

import asyncio
from kairosmd.fhir_client import FHIRClient

RESOURCES = [
    "Appointment",
    "Observation",
    "MedicationRequest",
    "Condition",
    "AllergyIntolerance",
    "DocumentReference",
    "Patient",
    "Practitioner"
]

async def purge():
    client = FHIRClient()
    http = await client._get_client()
    
    print("Purging resources from FHIR server...")
    
    for resource_type in RESOURCES:
        print(f"  Searching for {resource_type}s...")
        try:
            # We search for everything and delete. 
            # On public HAPI, we'll limit to a reasonable number to avoid hanging.
            resp = await http.get(f"/{resource_type}?_count=100")
            if resp.status_code != 200:
                print(f"    Failed to search {resource_type}: {resp.status_code}")
                continue
                
            bundle = resp.json()
            entries = bundle.get("entry", [])
            
            if not entries:
                print(f"    No {resource_type}s found.")
                continue
                
            print(f"    Deleting {len(entries)} {resource_type}(s)...")
            for entry in entries:
                rid = entry["resource"]["id"]
                del_resp = await http.delete(f"/{resource_type}/{rid}")
                if del_resp.status_code in (200, 204):
                    print(f"      Deleted {resource_type}/{rid}")
                else:
                    print(f"      Failed to delete {resource_type}/{rid}: {del_resp.status_code}")
        except Exception as e:
            print(f"    Error purging {resource_type}: {e}")

    await client.close()
    print("\nPurge complete. (Note: Only first 100 of each type were purged to avoid timeouts)")

if __name__ == "__main__":
    asyncio.run(purge())
