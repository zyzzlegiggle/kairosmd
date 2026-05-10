"""Quick smoke test for OpenFDA + RxNorm APIs."""
import asyncio
from kairosmd.external_apis import (
    get_drug_label, get_adverse_events,
    get_combo_adverse_events, get_drug_class,
)

async def main():
    print("=== OpenFDA Drug Label: Amiodarone ===")
    label = await get_drug_label("Amiodarone")
    if label:
        print(f"  Boxed warning: {bool(label.get('boxed_warning'))}")
        print(f"  Contraindications: {bool(label.get('contraindications'))}")
        print(f"  Drug interactions (excerpt): {(label.get('drug_interactions') or '')[:200]}")
    else:
        print("  No label found")

    print("\n=== OpenFDA Adverse Events: Digoxin + Amiodarone ===")
    combo = await get_combo_adverse_events("Digoxin", "Amiodarone")
    if combo:
        print(f"  Total FDA combo reports: {combo.get('total_combo_reports', 0)}")
        for r in combo.get("top_reactions_together", []):
            print(f"    - {r['reaction']}: {r['count']} reports")
    else:
        print("  No combo data found")

    print("\n=== RxNorm Drug Class: Flucloxacillin ===")
    classes = await get_drug_class("Flucloxacillin")
    print(f"  Classes: {classes or 'None found'}")

    print("\n=== OpenFDA Adverse Events: Heparin + Ibuprofen ===")
    combo2 = await get_combo_adverse_events("Heparin", "Ibuprofen")
    if combo2:
        print(f"  Total FDA combo reports: {combo2.get('total_combo_reports', 0)}")
        for r in combo2.get("top_reactions_together", []):
            print(f"    - {r['reaction']}: {r['count']} reports")
    else:
        print("  No combo data found")

asyncio.run(main())
