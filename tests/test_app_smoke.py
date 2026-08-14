from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_streamlit_starts():
    app = AppTest.from_file(APP_PATH)
    app.run(timeout=30)
    assert not app.exception
