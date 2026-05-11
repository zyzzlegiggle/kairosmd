"""Async FHIR R4 client for HAPI FHIR server.

Handles Patient, Appointment, Observation (vitals + labs),
DocumentReference (clinical notes), and Condition resources.
"""

import httpx
import asyncio
import random
from datetime import date
from kairosmd import config

MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds, doubles on each retry


class FHIRClient:
    """Lightweight async wrapper around FHIR R4 REST API with SHARP context support."""

    def __init__(
        self, 
        base_url: str | None = None, 
        access_token: str | None = None,
        context_bundle: dict | None = None
    ):
        self.base_url = (base_url or config.FHIR_BASE_URL).rstrip("/")
        self.access_token = access_token or config.FHIR_ACCESS_TOKEN
        self.context_bundle = context_bundle
        self._client: httpx.AsyncClient | None = None

    # -- lifecycle ------------------------------------------------------
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"Accept": "application/fhir+json"}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # -- helpers --------------------------------------------------------
    async def search(self, resource_type: str, params: dict) -> list[dict]:
        """Execute a FHIR search. Checks context_bundle first, then retries on 429."""
        
        # Check SHARP Context Bundle first
        if self.context_bundle:
            results = []
            entries = self.context_bundle.get("entry", [])
            for entry in entries:
                res = entry.get("resource", {})
                if res.get("resourceType") != resource_type:
                    continue
                
                # Simple param filtering (e.g. patient=ID)
                match = True
                for k, v in params.items():
                    if k.startswith("_"): continue # Skip sort/count
                    
                    # Handle common FHIR search params
                    if k == "patient" or k == "subject":
                        # res["patient"]["reference"] == "Patient/ID" or "ID"
                        ref = res.get(k, {}).get("reference", "")
                        if v not in ref: match = False
                    elif k == "practitioner":
                        ref = res.get(k, {}).get("reference", "")
                        if v not in ref: match = False
                
                if match:
                    results.append(res)
            
            if results:
                print(f"  [SHARP] Context Hit: {len(results)} {resource_type} resources")
                return results

        client = await self._get_client()
        delay = RETRY_DELAY
        for attempt in range(MAX_RETRIES + 1):
            resp = await client.get(f"/{resource_type}", params=params)
            if resp.status_code == 429:
                if attempt < MAX_RETRIES:
                    print(f"  [FHIR] 429 on {resource_type}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                else:
                    print(f"  [FHIR] 429 on {resource_type}, max retries reached")
                    return []
            if resp.status_code == 400:
                print(f"  [FHIR] 400 Bad Request on {resource_type}. URL: {resp.url}")
                return []
            resp.raise_for_status()
            bundle = resp.json()
            return [e["resource"] for e in bundle.get("entry", [])]
        return []

    async def _read(self, resource_type: str, resource_id: str) -> dict:
        """Read a single FHIR resource. Checks context_bundle first."""
        if self.context_bundle:
            entries = self.context_bundle.get("entry", [])
            for entry in entries:
                res = entry.get("resource", {})
                if res.get("resourceType") == resource_type and res.get("id") == resource_id:
                    print(f"  [SHARP] Context Hit: {resource_type}/{resource_id}")
                    return res

        client = await self._get_client()
        resp = await client.get(f"/{resource_type}/{resource_id}")
        resp.raise_for_status()
        return resp.json()

    # -- Appointments ---------------------------------------------------
    async def get_appointments(
        self, practitioner_id: str, target_date: str | None = None
    ) -> list[dict]:
        """Fetch appointments for a practitioner on a given date."""
        return await self.search("Appointment", {
            "practitioner": practitioner_id,
            "date": target_date or date.today().isoformat(),
            "_count": "50",
            "_sort": "date",
        })

    # -- Patients -------------------------------------------------------
    async def get_patient(self, patient_id: str) -> dict:
        return await self._read("Patient", patient_id)

    async def get_patients_batch(self, patient_ids: list[str]) -> list[dict]:
        patients = []
        for pid in patient_ids:
            try:
                patients.append(await self.get_patient(pid))
            except Exception:
                continue
        return patients

    # -- Vitals ---------------------------------------------------------
    async def get_vitals(self, patient_id: str, count: int = 20) -> list[dict]:
        """Fetch vital-sign Observations sorted newest-first."""
        return await self.search("Observation", {
            "patient": patient_id,
            "category": "vital-signs",
            "_sort": "-date",
            "_count": str(count),
        })

    # -- Labs -----------------------------------------------------------
    async def get_labs(self, patient_id: str, count: int = 30) -> list[dict]:
        """Fetch laboratory Observations sorted newest-first."""
        return await self.search("Observation", {
            "patient": patient_id,
            "category": "laboratory",
            "_sort": "-date",
            "_count": str(count),
        })

    # -- Clinical Notes -------------------------------------------------
    async def get_clinical_notes(self, patient_id: str, count: int = 10) -> list[dict]:
        """Fetch DocumentReference resources (nursing/doctor notes)."""
        return await self.search("DocumentReference", {
            "patient": patient_id,
            "_sort": "-date",
            "_count": str(count),
        })

    # -- Conditions -----------------------------------------------------
    async def get_conditions(self, patient_id: str) -> list[dict]:
        """Fetch active Condition resources for chronic-disease context."""
        return await self.search("Condition", {
            "patient": patient_id,
            "clinical-status": "active",
            "_count": "50",
        })

    # -- Medications ----------------------------------------------------
    async def get_medications(self, patient_id: str) -> list[dict]:
        """Fetch active MedicationRequest resources."""
        return await self.search("MedicationRequest", {
            "patient": patient_id,
            "status": "active",
            "_count": "50",
        })

    # -- Allergies ------------------------------------------------------
    async def get_allergies(self, patient_id: str) -> list[dict]:
        """Fetch AllergyIntolerance resources."""
        return await self.search("AllergyIntolerance", {
            "patient": patient_id,
            "_count": "50",
        })

    # -- Encounters (inpatient) -----------------------------------------
    async def get_encounters(self, patient_id: str = "", status: str = "in-progress") -> list[dict]:
        """Fetch inpatient Encounters. If no patient_id, fetch all active."""
        params = {"status": status, "_count": "50"}
        if patient_id:
            params["patient"] = patient_id
        results = await self.search("Encounter", params)
        # Client-side filter for IMP class since HAPI may not support class search
        return [e for e in results
                if e.get("class", {}).get("code") == "IMP"]

    async def get_encounter_for_patient(self, patient_id: str) -> dict | None:
        """Get the current active inpatient encounter for a patient."""
        encs = await self.get_encounters(patient_id)
        return encs[0] if encs else None

    # -- MedicationAdministration ---------------------------------------
    async def get_med_admins(self, patient_id: str, count: int = 50) -> list[dict]:
        """Fetch MedicationAdministration records."""
        return await self.search("MedicationAdministration", {
            "patient": patient_id,
            "_count": str(count),
        })

    # -- Procedures -----------------------------------------------------
    async def get_procedures(self, patient_id: str) -> list[dict]:
        return await self.search("Procedure", {
            "patient": patient_id,
            "_count": "20",
        })

    # -- DiagnosticReport -----------------------------------------------
    async def get_diagnostic_reports(self, patient_id: str) -> list[dict]:
        return await self.search("DiagnosticReport", {
            "patient": patient_id,
            "_count": "20",
        })

    # -- CareTeam -------------------------------------------------------
    async def get_care_team(self, patient_id: str) -> list[dict]:
        results = await self.search("CareTeam", {
            "patient": patient_id,
            "_count": "5",
        })
        # Client-side filter for active status
        return [ct for ct in results if ct.get("status") == "active"] or results

    # -- Communications (Audit Trail) -----------------------------------
    async def get_communications(self, patient_id: str) -> list[dict]:
        """Fetch Communication resources (Audit Trail) for a patient."""
        return await self.search("Communication", {
            "subject": f"Patient/{patient_id}",
            "_sort": "-sent",
            "_count": "20",
        })

    # -- Flags ----------------------------------------------------------
    async def get_flags(self, patient_id: str) -> list[dict]:
        results = await self.search("Flag", {
            "patient": patient_id,
            "_count": "10",
        })
        # Client-side filter for active status
        return [f for f in results if f.get("status") in ("active", "current", "completed")] or results

    async def _post(self, resource: str, data: dict) -> dict:
        """Create a new resource on the FHIR server."""
        client = await self._get_client()
        resp = await client.post(f"/{resource}", json=data)
        if resp.status_code in (200, 201):
            return resp.json()
        if resp.status_code == 412:
            # Duplicate resource — already exists from a previous seed run. Safe to skip.
            print(f"  [FHIR] Skipping duplicate {resource} (412)")
            return {"resourceType": resource, "id": "existing"}
        print(f"  [FHIR] Error creating {resource}: {resp.status_code} - {resp.text[:300]}")
        resp.raise_for_status()
        return resp.json()

    async def create_patient(self, name: str, gender: str, birthDate: str) -> dict:
        """Create a Patient resource, or return existing one if duplicate."""
        # Search for existing patient with same name first (idempotent)
        existing = await self.search("Patient", {"name": name, "_count": "1"})
        if existing:
            print(f"  [FHIR] Found existing Patient: {name} (id={existing[0]['id']})")
            return existing[0]

        p = {
            "resourceType": "Patient",
            "name": [{"text": name}],
            "gender": gender,
            "birthDate": birthDate,
        }
        try:
            return await self._post("Patient", p)
        except Exception:
            # If creation still fails (412), try searching again
            existing = await self.search("Patient", {"name": name, "_count": "1"})
            if existing:
                print(f"  [FHIR] Recovered existing Patient: {name} (id={existing[0]['id']})")
                return existing[0]
            raise

    async def create_encounter(self, patient_id: str, status: str, start_time: str, ward: str, bed: str, reason: str) -> dict:
        """Create an inpatient Encounter resource, or return existing one."""
        # Check if patient already has an active encounter
        existing = await self.get_encounters(patient_id)
        if existing:
            print(f"  [FHIR] Found existing Encounter for Patient/{patient_id}")
            return existing[0]

        e = {
            "resourceType": "Encounter",
            "status": status,
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "IMP", "display": "inpatient"},
            "subject": {"reference": f"Patient/{patient_id}"},
            "period": {"start": start_time},
            "reasonCode": [{"text": reason}],
            "location": [{
                "location": {"display": f"{ward} - Bed {bed}"},
                "status": "active"
            }]
        }
        try:
            return await self._post("Encounter", e)
        except Exception:
            existing = await self.get_encounters(patient_id)
            if existing:
                return existing[0]
            raise

    async def create_observation(self, patient_id: str, code: str, value: float, timestamp: str, encounter_id: str = None, display: str = None) -> dict:
        """Create an Observation (vitals or labs)."""
        category = "vital-signs" if code in ["9279-1", "59408-5", "8480-6", "8867-4", "8310-5", "67775-7"] else "laboratory"
        
        coding = {"system": "http://loinc.org", "code": code}
        if display:
            coding["display"] = display

        obs = {
            "resourceType": "Observation",
            "status": "final",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": category}]}],
            "code": {"coding": [coding]},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": timestamp,
            "valueQuantity": {"value": value}
        }
        if encounter_id:
            obs["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        return await self._post("Observation", obs)

    async def _delete(self, resource: str, resource_id: str):
        """Delete a resource from the FHIR server."""
        client = await self._get_client()
        resp = await client.delete(f"/{resource}/{resource_id}")
        if resp.status_code not in (200, 204, 410):
            print(f"  [FHIR] Error deleting {resource}/{resource_id}: {resp.status_code}")
        return resp.status_code

    # -- Persistence Methods --------------------------------------------

    async def create_clinical_note(self, patient_id: str, text: str, author: str = "Dr. Mike") -> dict:
        """Create a DocumentReference for a clinical decision note."""
        import base64
        from datetime import datetime, timezone
        encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")
        
        doc = {
            "resourceType": "DocumentReference",
            "status": "current",
            "type": {"text": "Clinical Decision Note"},
            "subject": {"reference": f"Patient/{patient_id}"},
            "date": datetime.now(timezone.utc).isoformat(),
            "author": [{"display": author}],
            "description": "Ward Round Decision Support Note",
            "content": [{"attachment": {"contentType": "text/plain", "data": encoded}}]
        }
        return await self._post("DocumentReference", doc)

    async def create_safety_flag(self, patient_id: str, code: str, detail: str) -> dict:
        """Create a Flag resource for clinical escalation/safety."""
        flag = {
            "resourceType": "Flag",
            "status": "active",
            "category": [{"text": "Clinical Safety"}],
            "code": {"text": f"{code}: {detail}"},
            "subject": {"reference": f"Patient/{patient_id}"}
        }
        return await self._post("Flag", flag)

    async def create_care_team(self, patient_id: str, members: list[dict]) -> dict:
        """Create a CareTeam resource."""
        ct = {
            "resourceType": "CareTeam",
            "status": "active",
            "subject": {"reference": f"Patient/{patient_id}"},
            "participant": [
                {
                    "role": [{"text": m["role"]}],
                    "member": {"display": m["name"]}
                } for m in members
            ]
        }
        return await self._post("CareTeam", ct)

    async def create_allergy(self, patient_id: str, code: str, display: str, criticality: str = "high") -> dict:
        """Create an AllergyIntolerance resource."""
        allergy = {
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
            "criticality": criticality,
            "code": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": code}], "text": display},
            "patient": {"reference": f"Patient/{patient_id}"}
        }
        return await self._post("AllergyIntolerance", allergy)

    async def create_medication_request(self, patient_id: str, medication: dict, requester: str) -> dict:
        """Create a MedicationRequest resource."""
        mr = {
            "resourceType": "MedicationRequest",
            "status": medication.get("status", "active"),
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": medication["code"]}],
                "text": medication["name"]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "requester": {"display": requester},
            "dosageInstruction": [{"text": medication["dosage"]}]
        }
        return await self._post("MedicationRequest", mr)

    async def create_medication_administration(self, patient_id: str, medication_name: str, status: str, time: str, performer: str) -> dict:
        """Create a MedicationAdministration resource."""
        ma = {
            "resourceType": "MedicationAdministration",
            "status": status,
            "medicationCodeableConcept": {"text": medication_name},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": time,
            "performer": [{"actor": {"display": performer}}]
        }
        return await self._post("MedicationAdministration", ma)

    async def create_diagnostic_report(self, patient_id: str, type_code: str, type_text: str, conclusion: str, date: str) -> dict:
        """Create a DiagnosticReport resource."""
        dr = {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": type_code}], "text": type_text},
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": date,
            "conclusion": conclusion
        }
        return await self._post("DiagnosticReport", dr)


    async def create_communication(self, patient_id: str, sender: str, recipient: str, payload: str, timestamp: str) -> dict:
        """Create a Communication resource (Audit Log)."""
        comm = {
            "resourceType": "Communication",
            "status": "completed",
            "subject": {"reference": f"Patient/{patient_id}"},
            "sent": timestamp,
            "sender": {"display": sender},
            "recipient": [{"display": recipient}],
            "payload": [{"contentString": payload}]
        }
        return await self._post("Communication", comm)

