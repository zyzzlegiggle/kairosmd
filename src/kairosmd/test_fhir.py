"""Minimal test to debug 412 on HAPI FHIR public server."""
import httpx
import json

BASE = "https://hapi.fhir.org/baseR4"

patient = {
    "resourceType": "Patient",
    "name": [{"text": "Test KairosMD"}],
    "gender": "male",
    "birthDate": "1990-01-01",
}

# Attempt 1: json= (httpx sets Content-Type: application/json)
print("--- Attempt 1: json= parameter ---")
r1 = httpx.post(f"{BASE}/Patient", json=patient, timeout=30)
print(f"Status: {r1.status_code}")
print(f"Headers sent: {dict(r1.request.headers)}")
print(f"Response: {r1.text[:300]}")
print()

# Attempt 2: content= with application/fhir+json
print("--- Attempt 2: content= with fhir+json ---")
r2 = httpx.post(
    f"{BASE}/Patient",
    content=json.dumps(patient),
    headers={"Content-Type": "application/fhir+json"},
    timeout=30,
)
print(f"Status: {r2.status_code}")
print(f"Headers sent: {dict(r2.request.headers)}")
print(f"Response: {r2.text[:300]}")
print()

# Attempt 3: content= with application/json
print("--- Attempt 3: content= with application/json ---")
r3 = httpx.post(
    f"{BASE}/Patient",
    content=json.dumps(patient),
    headers={"Content-Type": "application/json"},
    timeout=30,
)
print(f"Status: {r3.status_code}")
print(f"Headers sent: {dict(r3.request.headers)}")
print(f"Response: {r3.text[:300]}")
