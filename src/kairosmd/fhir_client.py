"""Async FHIR R4 client for HAPI FHIR server.

Handles Patient, Appointment, Observation (vitals + labs),
DocumentReference (clinical notes), and Condition resources.
"""

import httpx
import asyncio
from datetime import date
from kairosmd import config

MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds, doubles on each retry


class FHIRClient:
    """Lightweight async wrapper around FHIR R4 REST API."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or config.FHIR_BASE_URL).rstrip("/")
        self._client: httpx.AsyncClient | None = None

    # -- lifecycle ------------------------------------------------------
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Accept": "application/fhir+json"},
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # -- helpers --------------------------------------------------------
    async def _search(self, resource: str, params: dict) -> list[dict]:
        """Execute a FHIR search with retry on 429."""
        client = await self._get_client()
        delay = RETRY_DELAY
        for attempt in range(MAX_RETRIES + 1):
            resp = await client.get(f"/{resource}", params=params)
            if resp.status_code == 429:
                if attempt < MAX_RETRIES:
                    print(f"  [FHIR] 429 on {resource}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                else:
                    print(f"  [FHIR] 429 on {resource}, max retries reached")
                    return []
            if resp.status_code == 400:
                print(f"  [FHIR] 400 Bad Request on {resource}. URL: {resp.url}")
                print(f"  [FHIR] Response: {resp.text[:200]}")
                return []
            resp.raise_for_status()
            bundle = resp.json()
            return [e["resource"] for e in bundle.get("entry", [])]
        return []

    async def _read(self, resource: str, resource_id: str) -> dict:
        client = await self._get_client()
        resp = await client.get(f"/{resource}/{resource_id}")
        resp.raise_for_status()
        return resp.json()

    # -- Appointments ---------------------------------------------------
    async def get_appointments(
        self, practitioner_id: str, target_date: str | None = None
    ) -> list[dict]:
        """Fetch appointments for a practitioner on a given date."""
        return await self._search("Appointment", {
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
        return await self._search("Observation", {
            "patient": patient_id,
            "category": "vital-signs",
            "_sort": "-date",
            "_count": str(count),
        })

    # -- Labs -----------------------------------------------------------
    async def get_labs(self, patient_id: str, count: int = 30) -> list[dict]:
        """Fetch laboratory Observations sorted newest-first."""
        return await self._search("Observation", {
            "patient": patient_id,
            "category": "laboratory",
            "_sort": "-date",
            "_count": str(count),
        })

    # -- Clinical Notes -------------------------------------------------
    async def get_clinical_notes(self, patient_id: str, count: int = 10) -> list[dict]:
        """Fetch DocumentReference resources (nursing/doctor notes)."""
        return await self._search("DocumentReference", {
            "patient": patient_id,
            "_sort": "-date",
            "_count": str(count),
        })

    # -- Conditions -----------------------------------------------------
    async def get_conditions(self, patient_id: str) -> list[dict]:
        """Fetch active Condition resources for chronic-disease context."""
        return await self._search("Condition", {
            "patient": patient_id,
            "clinical-status": "active",
            "_count": "50",
        })

    # -- Medications ----------------------------------------------------
    async def get_medications(self, patient_id: str) -> list[dict]:
        """Fetch active MedicationRequest resources."""
        return await self._search("MedicationRequest", {
            "patient": patient_id,
            "status": "active",
            "_count": "50",
        })

    # -- Allergies ------------------------------------------------------
    async def get_allergies(self, patient_id: str) -> list[dict]:
        """Fetch AllergyIntolerance resources."""
        return await self._search("AllergyIntolerance", {
            "patient": patient_id,
            "_count": "50",
        })

    # -- Encounters (inpatient) -----------------------------------------
    async def get_encounters(self, patient_id: str = "", status: str = "in-progress") -> list[dict]:
        """Fetch inpatient Encounters. If no patient_id, fetch all active."""
        params = {"status": status, "_count": "50"}
        if patient_id:
            params["patient"] = patient_id
        results = await self._search("Encounter", params)
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
        return await self._search("MedicationAdministration", {
            "patient": patient_id,
            "_count": str(count),
        })

    # -- Procedures -----------------------------------------------------
    async def get_procedures(self, patient_id: str) -> list[dict]:
        return await self._search("Procedure", {
            "patient": patient_id,
            "_count": "20",
        })

    # -- DiagnosticReport -----------------------------------------------
    async def get_diagnostic_reports(self, patient_id: str) -> list[dict]:
        return await self._search("DiagnosticReport", {
            "patient": patient_id,
            "_count": "20",
        })

    # -- CareTeam -------------------------------------------------------
    async def get_care_team(self, patient_id: str) -> list[dict]:
        results = await self._search("CareTeam", {
            "patient": patient_id,
            "_count": "5",
        })
        # Client-side filter for active status
        return [ct for ct in results if ct.get("status") == "active"] or results

    # -- Flags ----------------------------------------------------------
    async def get_flags(self, patient_id: str) -> list[dict]:
        results = await self._search("Flag", {
            "patient": patient_id,
            "_count": "10",
        })
        # Client-side filter for active status
        return [f for f in results if f.get("status") == "active"] or results

