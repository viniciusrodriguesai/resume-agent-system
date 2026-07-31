from streamlit.testing.v1 import AppTest

def test_app_abre():
    app=AppTest.from_file('app.py',default_timeout=20).run()
    assert not app.exception
    assert len(app.title)>=1
