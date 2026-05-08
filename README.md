# KairosMD Clinical Triage MCP Server

KairosMD is a clinical triage system that ranks patients by urgency using FHIR data, rule-based logic, and LLM-driven note analysis.

## Setup

### 1. Environment
Install dependencies:
```bash
uv sync
```

Create a `.env` file:
```bash
cp .env.example .env
```

### 2. LLM Configuration
Add your API credentials to `.env`. Note analysis is powered by NVIDIA Nemotron 3 Super 120B (Public Preview).

### 3. Seed Data
Populate the HAPI FHIR server with test data:
```bash
uv run python -m kairosmd.seed
```
Set the Practitioner ID in `.env` as `DEFAULT_PRACTITIONER_ID`.

### 4. Run Server
Standard mode (local stdio):
```bash
uv run mcp dev src/kairosmd/server.py
```

SSE mode (for ngrok/HTTPS):
```bash
uv run kairosmd --sse
```
Starts the server on the default port (8000).

### 5. Remote Access (ngrok)
To expose the server over HTTPS:
1. Start the server in SSE mode: `uv run kairosmd --sse`
2. Tunnel with ngrok: `ngrok http 8000`
3. Use the ngrok URL (e.g., `https://...ngrok-free.app/sse`) as your MCP endpoint.

## Tools

| Tool | Description |
| :--- | :--- |
| get_ward_patients | Fetch patients scheduled for a doctor. |
| get_patient_vitals | Pull vitals with clinical flags. |
| get_lab_results | Fetch lab values with clinical flagging. |
| get_clinical_notes | Pull clinical notes for context. |
| analyze_patient_risk | Score patient urgency (0-100). |
| generate_priority_list | Main orchestrator to rank patients by risk. |

## Scoring Logic
Composite score (0-100) based on:
- Vitals: Rule-based flags for abnormal readings.
- Labs: Rule-based flags for critical values.
- Notes: LLM analysis for deterioration keywords.
- Conditions: Base risk increase for chronic conditions.
- Staleness: Penalty for patients not reviewed in >8 hours.

## Data Sources
- FHIR: HAPI FHIR (R4) for clinical data.
- LLM: NVIDIA Nemotron 3 Super 120B (Public Preview) for note interpretation.
