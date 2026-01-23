import json
import pytest
from pathlib import Path

@pytest.fixture
def load_schema():
    def _load(name):
        schema_path = Path(__file__).parent / "schemas" / f"{name}.json"
        return json.loads(schema_path.read_text())
    return _load