"""
Project configuration.

Fresh clones work out of the box against the local `notes/` folder with no
curriculum-specific overrides. To point at a private note vault and/or a real
curriculum module, copy `.env.example` to `.env` (gitignored) and edit it.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

# Fresh-clone default: drop your own lesson notes in notes/ and it just works.
VAULT_DIR = Path(os.environ.get("VAULT_DIR", BASE_DIR / "notes"))
NOTES_DIR = BASE_DIR / "notes"

# Ships empty. See curriculum/blank.py vs curriculum/minna_no_nihongo.py.
CURRICULUM_MODULE = os.environ.get("CURRICULUM_MODULE", "curriculum.blank")
