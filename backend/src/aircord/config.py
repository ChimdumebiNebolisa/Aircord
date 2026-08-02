from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.getenv("AIRCORD_DATA_DIR", ROOT_DIR / "data"))
DB_PATH = Path(os.getenv("AIRCORD_DB_PATH", DATA_DIR / "aircord.sqlite3"))
MODE = os.getenv("AIRCORD_MODE", "fixture")
AIRNOW_API_KEY = os.getenv("AIRNOW_API_KEY")
PURPLEAIR_API_KEY = os.getenv("PURPLEAIR_API_KEY")
BEDROCK_MODEL_ID = os.getenv("AIRCORD_BEDROCK_MODEL_ID")

REFERENCE_CAVEAT = (
    "AirNow regulatory monitors are the evaluation reference for this demo, not absolute truth."
)
MEDICAL_DIRECTIVE_CAVEAT = (
    "Aircord is an air-quality estimate with confidence, not medical advice or a health directive."
)

