import pytest
from streamlit.testing.v1 import AppTest
from src.utils import ROOT


@pytest.mark.parametrize('language',['en','zh','ja'])
def test_language_change_keeps_department_cohort_and_guest_session(tmp_path,monkeypatch,language):
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR',str(tmp_path/'users'))
    monkeypatch.setenv('RAG_VECTOR_DEFAULT','0')
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    next(b for b in app.button if b.key=='guest_review_entry').click().run(timeout=90)
    guest_id=app.session_state.guest_user['account_id']
    next(s for s in app.sidebar.selectbox if s.key=='selected_department').set_value('정보보호학과').run(timeout=90)
    next(n for n in app.sidebar.number_input if n.key=='selected_admission_year').set_value(2023).run(timeout=90)
    next(t for t in app.sidebar.toggle if t.key=='llm_enabled').set_value(True).run(timeout=90)
    next(s for s in app.selectbox if s.key=='ui_language').set_value(language).run(timeout=90)
    assert not app.exception
    assert app.session_state.selected_department=='정보보호학과'
    assert app.session_state.selected_admission_year==2023
    assert app.session_state.llm_enabled is True
    assert app.session_state.guest_user['account_id']==guest_id
    # Canonical values drive scoring even though the display options are translated.
    assert next(s for s in app.sidebar.selectbox if s.key=='selected_department').value=='정보보호학과'
    assert any(s.label=='언어 / Language / 语言 / 言語' for s in app.selectbox)
