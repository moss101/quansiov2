"""Shared platform kernel package (db, context, migrations, service plumbing).

The generated canonical contract bindings under ``generated/contracts/python``
are part of every deployable payload; importing ``quansio`` makes them
importable without requiring every deployable to configure PYTHONPATH.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CONTRACTS = Path(__file__).resolve().parents[1] / "generated" / "contracts" / "python"
if _CONTRACTS.is_dir() and str(_CONTRACTS) not in sys.path:
    sys.path.insert(0, str(_CONTRACTS))
