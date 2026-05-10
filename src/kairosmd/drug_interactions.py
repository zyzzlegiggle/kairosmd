"""Drug interaction checking via NLM RxNav API (free, no auth)."""

import httpx

RXNAV_BASE = "https://rxnav.nlm.nih.gov/REST"

# Known high-risk pairs (fallback if API is slow/down)
KNOWN_INTERACTIONS = {
    frozenset(["warfarin", "aspirin"]): "Increased bleeding risk",
    frozenset(["sertraline", "tramadol"]): "Serotonin syndrome risk",
    frozenset(["methotrexate", "ibuprofen"]): "Methotrexate toxicity - reduced renal clearance",
    frozenset(["lisinopril", "spironolactone"]): "Hyperkalemia risk - dual potassium retention",
    frozenset(["warfarin", "ibuprofen"]): "Increased bleeding and GI risk",
    frozenset(["gabapentin", "tramadol"]): "Increased CNS depression",
    frozenset(["gabapentin", "oxycodone"]): "Increased CNS depression and respiratory risk",
    frozenset(["zolpidem", "gabapentin"]): "Excessive sedation and fall risk",
    frozenset(["zolpidem", "tramadol"]): "Excessive CNS depression",
    frozenset(["sertraline", "zolpidem"]): "Increased sedation",
    # Pairs from MDS seed scenarios
    frozenset(["digoxin", "amiodarone"]): "Amiodarone doubles digoxin levels - risk of toxicity",
    frozenset(["heparin", "ibuprofen"]): "NSAID with anticoagulant - increased bleeding risk",
    frozenset(["heparin", "aspirin"]): "Dual anticoagulant/antiplatelet - major bleeding risk",
    frozenset(["warfarin", "clarithromycin"]): "Clarithromycin increases warfarin levels - bleeding risk",
    frozenset(["ramipril", "spironolactone"]): "Hyperkalemia risk - dual RAAS blockade",
}


def check_interactions_local(med_names: list[str]) -> list[dict]:
    """Check known drug-drug interactions using local rules.
    med_names should be lowercase base drug names (e.g. ['warfarin', 'aspirin']).
    """
    results = []
    names = [n.lower() for n in med_names]
    for i, a in enumerate(names):
        for b in names[i+1:]:
            key = frozenset([a, b])
            if key in KNOWN_INTERACTIONS:
                results.append({
                    "drug_a": a,
                    "drug_b": b,
                    "severity": "high",
                    "description": KNOWN_INTERACTIONS[key],
                })
    return results


async def check_interactions_rxnav(rxcuis: list[str]) -> list[dict]:
    """Check drug interactions via RxNav API using RxCUI codes."""
    if len(rxcuis) < 2:
        return []

    url = f"{RXNAV_BASE}/interaction/list.json"
    params = {"rxcuis": "+".join(str(r) for r in rxcuis)}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []
            data = resp.json()

        results = []
        for group in data.get("fullInteractionTypeGroup", []):
            for itype in group.get("fullInteractionType", []):
                for pair in itype.get("interactionPair", []):
                    desc = pair.get("description", "")
                    severity = pair.get("severity", "N/A")
                    concepts = pair.get("interactionConcept", [])
                    names = [c.get("minConceptItem", {}).get("name", "?")
                             for c in concepts]
                    results.append({
                        "drug_a": names[0] if names else "?",
                        "drug_b": names[1] if len(names) > 1 else "?",
                        "severity": severity,
                        "description": desc,
                    })
        return results
    except Exception:
        return []


def extract_base_name(med_name: str) -> str:
    """Extract base drug name from a medication string like 'Metformin 500mg'."""
    parts = med_name.lower().split()
    return parts[0] if parts else med_name.lower()


def check_polypharmacy(med_count: int) -> dict | None:
    """Flag polypharmacy if 10+ medications."""
    if med_count >= 10:
        return {
            "flag": "polypharmacy",
            "count": med_count,
            "description": f"Patient on {med_count} medications - increased risk of "
                           "adverse drug events, falls, and cognitive impairment",
        }
    return None
