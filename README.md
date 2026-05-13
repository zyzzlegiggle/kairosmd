# KairosMD: Multidisciplinary Ward Round Decision Support

KairosMD is an AI-powered clinical context engine built using the Model Context Protocol (MCP). It synthesizes fragmented patient data from FHIR servers, identifies clinical safety conflicts using real-world FDA evidence, and provides an actionable audit trail for hospital ward rounds.

## Features

- **Clinical Synthesis:** Natural language briefings for inpatient ward rounds.
- **NEWS2 Scoring:** Automated early warning scores for deteriorating patients.
- **Conflict Detection:** Identifies "silent contradictions" between nursing notes and vital signs.
- **FDA Safety Enrichment:** Real-world adverse event data from OpenFDA and RxNorm.
- **MDT Audit Trail:** Decision persistence back to FHIR (DocumentReference, Flag, Communication).

## Tech Stack

- **Backend:** Python, FastMCP, httpx
- **Frontend:** Next.js, React, Tailwind CSS
- **Data Standards:** FHIR R4, LOINC, RxNorm
- **LLM:** Gemini 3.1 Flash (via PromptOpinion)

## Getting Started

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation
```bash
uv sync
uv run python -m kairosmd.seed
```

### Running the Server
```bash
uv run kairosmd --sse
```

## Deployment
For detailed deployment instructions, see [deployment_guide.md](./deployment_guide.md).
