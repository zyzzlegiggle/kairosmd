"""External clinical API integrations.

Integrates free, no-auth clinical APIs to enhance decision support:
  1. OpenFDA Drug Labels  - Real warnings, contraindications, boxed warnings
  2. OpenFDA Adverse Events - Real-world adverse event frequency for drug combos
  3. RxNorm (NLM)          - Drug name normalization and drug class lookup
"""

import httpx
import asyncio
from functools import lru_cache

# -- Config ----------------------------------------------------------------
OPENFDA_BASE = "https://api.fda.gov"
RXNORM_BASE = "https://rxnav.nlm.nih.gov/REST"
_cache: dict[str, dict] = {}  # Simple in-memory cache


# ==========================================================================
# 1. OpenFDA Drug Labels
# ==========================================================================
async def get_drug_label(drug_name: str) -> dict | None:
    """Fetch FDA drug label data (warnings, contraindications, boxed warnings).
    
    Returns structured safety information from the FDA drug label database.
    Free, no auth required. Rate limit: 240 requests/min without API key.
    """
    cache_key = f"label:{drug_name.lower()}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"{OPENFDA_BASE}/drug/label.json"
    params = {
        "search": f'openfda.generic_name:"{drug_name}"',
        "limit": "1",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()

        results = data.get("results", [])
        if not results:
            return None

        label = results[0]
        parsed = {
            "drug_name": drug_name,
            "boxed_warning": _first_text(label.get("boxed_warning", [])),
            "warnings": _first_text(label.get("warnings", [])),
            "contraindications": _first_text(label.get("contraindications", [])),
            "drug_interactions": _first_text(label.get("drug_interactions", [])),
            "adverse_reactions": _first_text(label.get("adverse_reactions", []))[:500],
            "pregnancy_category": _first_text(label.get("pregnancy", [])),
        }
        _cache[cache_key] = parsed
        return parsed

    except Exception:
        return None


async def get_drug_labels_batch(drug_names: list[str]) -> list[dict]:
    """Fetch FDA labels for multiple drugs, with rate limiting."""
    results = []
    for name in drug_names:
        label = await get_drug_label(name)
        if label:
            results.append(label)
        await asyncio.sleep(0.25)  # Rate limit: stay well under 240/min
    return results


# ==========================================================================
# 2. OpenFDA Adverse Events
# ==========================================================================
async def get_adverse_events(drug_name: str, limit: int = 5) -> dict | None:
    """Fetch real-world adverse event reports for a drug from FDA FAERS.
    
    Returns top adverse reactions reported to the FDA for this drug.
    """
    cache_key = f"adverse:{drug_name.lower()}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"{OPENFDA_BASE}/drug/event.json"
    params = {
        "search": f'patient.drug.openfda.generic_name:"{drug_name}"',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": str(limit),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()

        events = data.get("results", [])
        parsed = {
            "drug_name": drug_name,
            "top_adverse_reactions": [
                {"reaction": e.get("term", ""), "count": e.get("count", 0)}
                for e in events
            ],
            "total_reports": sum(e.get("count", 0) for e in events),
        }
        _cache[cache_key] = parsed
        return parsed

    except Exception:
        return None


async def get_combo_adverse_events(drug_a: str, drug_b: str, limit: int = 5) -> dict | None:
    """Fetch adverse events reported when two drugs are taken together.
    
    This searches FAERS for reports where both drugs appear in the same case.
    High report counts for a combo = real-world evidence of interaction risk.
    """
    cache_key = f"combo:{drug_a.lower()}+{drug_b.lower()}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"{OPENFDA_BASE}/drug/event.json"
    search_query = (
        f'patient.drug.openfda.generic_name:"{drug_a}"'
        f' AND patient.drug.openfda.generic_name:"{drug_b}"'
    )
    params = {
        "search": search_query,
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": str(limit),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()

        events = data.get("results", [])
        parsed = {
            "drug_a": drug_a,
            "drug_b": drug_b,
            "top_reactions_together": [
                {"reaction": e.get("term", ""), "count": e.get("count", 0)}
                for e in events
            ],
            "total_combo_reports": sum(e.get("count", 0) for e in events),
        }
        _cache[cache_key] = parsed
        return parsed

    except Exception:
        return None


# ==========================================================================
# 3. RxNorm - Drug name normalization and class lookup
# ==========================================================================
async def get_rxcui(drug_name: str) -> str | None:
    """Look up the RxCUI (normalized drug ID) for a drug name.
    
    Free, no auth. RxNorm is the standard US drug nomenclature.
    """
    cache_key = f"rxcui:{drug_name.lower()}"
    if cache_key in _cache:
        return _cache[cache_key]

    url = f"{RXNORM_BASE}/rxcui.json"
    params = {"name": drug_name, "search": "1"}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()

        candidates = data.get("idGroup", {}).get("rxnormId", [])
        if candidates:
            rxcui = candidates[0]
            _cache[cache_key] = rxcui
            return rxcui
        return None

    except Exception:
        return None


async def get_drug_class(drug_name: str) -> list[str]:
    """Get the pharmacological class(es) for a drug via RxNorm → RxClass.
    
    Useful for cross-class allergy detection (e.g., all penicillins).
    """
    cache_key = f"class:{drug_name.lower()}"
    if cache_key in _cache:
        return _cache[cache_key]

    rxcui = await get_rxcui(drug_name)
    if not rxcui:
        return []

    url = f"{RXNORM_BASE}/rxclass/class/byRxcui.json"
    params = {"rxcui": rxcui, "relaSource": "ATC"}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            data = resp.json()

        classes = []
        for entry in data.get("rxclassDrugInfoList", {}).get("rxclassDrugInfo", []):
            class_name = entry.get("rxclassMinConceptItem", {}).get("className", "")
            if class_name and class_name not in classes:
                classes.append(class_name)

        _cache[cache_key] = classes
        return classes

    except Exception:
        return []


# ==========================================================================
# 4. Enrichment: Combine everything for a medication safety profile
# ==========================================================================
async def get_medication_safety_profile(drug_name: str) -> dict:
    """Build a comprehensive safety profile for a drug using all APIs.
    
    Combines FDA label data + adverse event data + drug class info.
    This is the main entry point for the conflict detector to use.
    """
    label, adverse, drug_classes = await asyncio.gather(
        get_drug_label(drug_name),
        get_adverse_events(drug_name),
        get_drug_class(drug_name),
        return_exceptions=True,
    )

    return {
        "drug_name": drug_name,
        "fda_label": label if isinstance(label, dict) else None,
        "adverse_events": adverse if isinstance(adverse, dict) else None,
        "drug_classes": drug_classes if isinstance(drug_classes, list) else [],
    }


# -- Helpers ---------------------------------------------------------------
def _first_text(items: list) -> str:
    """Extract first text item from FDA label array field."""
    if items and isinstance(items, list):
        return items[0][:1000] if isinstance(items[0], str) else ""
    return ""
