# KairosMD: Multidisciplinary Ward Round Decision Support

## Inspiration
Clinicians in acute hospital environments operate under significant cognitive load. The "Ward Round Gap"—the period required for manual data aggregation from fragmented laboratory, pharmacy, and nursing records—contributes to clinician burnout and increases the risk of medical error. KairosMD was developed as a clinical context engine to collapse this information latency, providing a unified, actionable view of patient data to improve safety and efficiency.

## What it Does
KairosMD is a multidisciplinary decision support system designed to synthesize complex patient data into high-fidelity clinical briefings.
- **Clinical Synthesis:** Aggregates longitudinal vitals, laboratory trends, and active medications into natural language summaries.
- **Silent Contradiction Detection:** Cross-references subjective documentation against objective physiological data (e.g., NEWS2 scores) to identify deteriorating patients.
- **Evidence Enrichment:** Integrates OpenFDA and RxNorm data to provide weighted drug-safety alerts grounded in real-world adverse event frequency.
- **Governance & Audit:** Maintains a chronological audit trail of multidisciplinary team (MDT) decisions, persisted directly to the clinical record.

## Interaction Model
The system operates as a clinical context engine integrated into the PromptOpinion agent environment. Users interact via natural language through the **PromptOpinion Agent (Gemini 3.1 Flash)**, which orchestrates calls to the KairosMD MCP server to fetch, analyze, and persist clinical data.

## Technical Implementation

### Core Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Agent Platform** | PromptOpinion |
| **LLM Engine** | Gemini 3.1 Flash |
| **MCP Framework** | Python FastMCP (mcp-server-sdk) |
| **Backend Logic** | Python 3.11, HTTPX, Pydantic |
| **Frontend Framework** | Next.js 15 (App Router), React 19 |
| **Data Visualization** | Recharts (Vitals & Lab Trends) |
| **Styling** | Tailwind CSS / Vanilla CSS |
| **Clinical Backend** | HAPI FHIR R4 (Standardized Healthcare API) |
| **External APIs** | OpenFDA (FAERS/Labels), NLM RxNorm/RxClass |

### MCP Tool Suite
The KairosMD MCP server exposes nine specialized tools that provide the agent with deep access to clinical intelligence and record persistence:

1. **get_ward_round_summary**: Provides a prioritized overview of the entire ward census, including NEWS2 scores, active conflicts, and AI-generated summaries.
2. **get_patient_ward_detail**: Executes a deep dive into a specific patient record, returning longitudinal vitals, laboratory trends, and active medications.
3. **get_conflict_report**: Aggregates all detected clinical contradictions (e.g., Note vs. Vitals, Allergy vs. Medication) across the ward.
4. **get_discharge_candidates**: Evaluates the ward against discharge safety criteria and identifies patients ready for transfer.
5. **record_ward_action**: Persists clinical decisions (acknowledgments, notes, escalations) directly back to the FHIR audit trail.
6. **get_action_history**: Returns a chronological audit trail of all multidisciplinary decisions made for a patient.
7. **get_drug_safety_info**: Queries OpenFDA for real-world evidence, including boxed warnings and FAERS adverse event frequencies.
8. **get_dashboard_access**: Generates context-aware deep links to the visual Next.js dashboards.
9. **apply_suggested_plan**: A closed-loop tool that allows clinicians to approve and persist AI-generated care plan adjustments.

## Clinical Intelligence Layer
The system employs a multi-layered approach to clinical safety:
- **Physiological Deterioration:** Automated calculation of NEWS2 (National Early Warning Score) based on validated LOINC codes.
- **Medication Safety:** Identification of drug-drug interactions and contraindications, enriched with FAERS adverse event report counts to provide clinical weight.
- **Discharge Validation:** Automated assessment of patients against objective clinical criteria (e.g., apyrexial for 24 hours, stable NEWS2) to optimize bed management.

## Challenges Encountered
- **Interoperability:** Normalizing fragmented FHIR resources across public sandbox environments required robust data mapping and validation.
- **Safety Grounding:** Ensuring AI reasoning remained strictly grounded in verified medical evidence required a deterministic retrieval pipeline to prevent hallucination of patient facts.

## Accomplishments
- **Closed-Loop Governance:** Successfully implemented a system where clinical decisions made via the agent are persisted back to the FHIR audit trail.
- **High-Fidelity Simulation:** Developed a clinical seeder capable of generating 20 distinct, evidence-based inpatient scenarios to validate the system under realistic ward loads.

## Lessons Learned
- **MCP Utility:** The Model Context Protocol is an effective framework for securely bringing complex, private clinical data into generative AI workflows.
- **Evidence-Based Reasoning:** Grounding LLM output in physiological trends and FDA evidence significantly enhances the utility of decision support compared to generic summarization.

## Future Development
- **Diagnostic Integration:** Expansion to include diagnostic imaging summaries and pathology reports.
- **Specialty Support:** Development of specialized reasoning modules for intensive care (ICU) and cardiology environments.
- **Predictive Analytics:** Implementation of length-of-stay and readmission risk modeling.
