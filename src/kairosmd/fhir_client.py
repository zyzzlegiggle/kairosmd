"""Async FHIR R4 client for HAPI FHIR server.

Handles Patient, Appointment, Observation (vitals + labs),
DocumentReference (clinical notes), and Condition resources.
"""

import httpx
from datetime import date
from kairosmd import config


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
        """Execute a FHIR search and return the list of resources."""
        client = await self._get_client()
        resp = await client.get(f"/{resource}", params=params)
        resp.raise_for_status()
        bundle = resp.json()
        return [e["resource"] for e in bundle.get("entry", [])]

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
