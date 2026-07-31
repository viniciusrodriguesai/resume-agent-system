import pytest

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest


def test_streamlit_starts():
    app = AppTest.from_file("app.py")
    app.run(timeout=30)
    assert not app.exception
