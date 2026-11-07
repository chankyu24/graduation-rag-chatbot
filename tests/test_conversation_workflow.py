"""Exercise actual chat turns and scope changes through the existing Streamlit UI."""
from streamlit.testing.v1 import AppTest
from src.utils import ROOT


def test_three_turn_cohort_context_then_clear_and_change_selection(tmp_path, monkeypatch):
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR', str(tmp_path/'accounts'))
    monkeypatch.setenv('RAG_VECTOR_DEFAULT', '0')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    next(b for b in app.button if b.key=='guest_review_entry').click().run(timeout=90)
    tech=next(e for e in app.sidebar.expander if e.label=='교수용 기술 검증 · 고급 설정')
    assert tech.proto.expanded is False
    assert any('Git:' in t.value for t in tech.text)
    app.sidebar.number_input[0].set_value(2023).run(timeout=90)
    next(b for b in app.button if b.key=='quick_PDF 단독 RAG').click().run(timeout=90)
    for question,expected in [
        ('나는 AI·빅데이터학과 2022학번인데 졸업하려면 뭐가 필요해?', '95점'),
        ('그럼 코딩역량인증은?', '코딩역량인증제'),
        ('그거 안 하면 졸업 못 해?', '대체'),
    ]:
        app.chat_input[0].set_value(question).run(timeout=90)
        assert not app.exception
        text=app.session_state.messages[-1][1]
        assert expected in text and 'p.5' in text
        assert '2022' in text
    # Original user text is displayed; only the private dialogue context is resolved.
    assert app.session_state.messages[-2][1]=='그거 안 하면 졸업 못 해?'
    next(b for b in app.button if b.label=='현재 대화 지우기').click().run(timeout=90)
    assert not app.session_state.messages and not app.session_state.chat_resolved_questions
    next(b for b in app.button if b.key=='chat_example_졸업인증 총점').click().run(timeout=90)
    assert not app.exception and '2023' in app.session_state.messages[-1][1]
    app.sidebar.number_input[0].set_value(2024).run(timeout=90)
    assert not app.session_state.messages
    app.chat_input[0].set_value('그거 안 하면 졸업 못 해?').run(timeout=90)
    assert not app.exception and '2022' not in app.session_state.messages[-1][1]
    next(b for b in app.sidebar.button if b.key=='leave_guest_review').click().run(timeout=90)
    assert 'chat_resolved_questions' not in app.session_state
