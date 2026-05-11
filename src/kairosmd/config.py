"""KairosMD configuration - loads from environment / .env file."""

import os
from dotenv import load_dotenv

load_dotenv()

# -- FHIR --------------------------------------------------------------
# Defaults used when SHARP headers (X-FHIR-*) are not provided by the platform
FHIR_BASE_URL: str = os.getenv("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4")
FHIR_ACCESS_TOKEN: str = os.getenv("FHIR_ACCESS_TOKEN", "")

# -- LLM Configuration ------------------------------------------------
LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "nemotron-3-super-120b")

# -- Defaults ----------------------------------------------------------
DASHBOARD_BASE_URL: str = os.getenv("DASHBOARD_BASE_URL", "http://localhost:3000")
