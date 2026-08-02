from pathlib import Path

import pytest

from aircord.fixtures import seed_demo


@pytest.fixture
def demo_db(tmp_path: Path) -> Path:
    path = tmp_path / "aircord.sqlite3"
    seed_demo(path)
    return path

