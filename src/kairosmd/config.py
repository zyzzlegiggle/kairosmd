"""KairosMD configuration - loads from environment / .env file."""

import os
from dotenv import load_dotenv

load_dotenv()

# -- FHIR --------------------------------------------------------------
FHIR_BASE_URL: str = os.getenv("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4")

# -- LLM Configuration ------------------------------------------------
LLM_ENDPOINT: str = os.getenv("LLM_ENDPOINT", "")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "nemotron-3-super-120b")

# -- Defaults ----------------------------------------------------------
DEFAULT_PRACTITIONER_ID: str = os.getenv("DEFAULT_PRACTITIONER_ID", "")
