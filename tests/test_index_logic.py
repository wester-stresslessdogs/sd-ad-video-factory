"""Unit-tests voor de pure logica van scripts/index_footage.py (geen I/O)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "index_footage", ROOT / "scripts" / "index_footage.py"
)
idx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(idx)


def test_module_imports():
    assert hasattr(idx, "SCHEMA_VERSION")
