"""Real Streamlit workflow checks; mock embeddings are explicit in availability tests."""
from streamlit.testing.v1 import AppTest
import pytest
from src.utils import ROOT


@pytest.fixture(autouse=True)
def environment(monkeypatch,tmp_path):
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR',str(tmp_path/'accounts'))
    monkeypatch.setenv('RAG_VECTOR_DEFAULT','0')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)


def click(app,key):
    next(b for b in app.button if b.key==key).click().run(timeout=90)
    assert not app.exception


def guest():
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    click(app,'guest_review_entry')
    return app


def test_professor_real_input_diagnosis_to_personal_advice():
    app=guest();click(app,'demo_inputs')
    assert app.sidebar.radio[0].value=='졸업요건 진단'
    next(b for b in app.button if b.label=='나의 졸업인증 진단').click().run(timeout=90)
    assert not app.exception
    result=app.session_state.result
    assert result['total_earned']==93 and result['total_required']==95 and result['synthetic']
    assert result['input_snapshot']['courses'] and result['owner_scope']
    click(app,'consult_diagnosis')
    assert '93' in app.session_state.messages[-1][1] and '가상' in app.session_state.messages[-1][1]
    for question,expected in [('나는 어떤 활동이 부족해?','글로벌'),('이미 이수한 과목은 무엇이야?','예비창업설계'),('어떤 영역에서 점수가 가장 부족해?','비교과미지정')]:
        app.chat_input[0].set_value(question).run(timeout=90)
        assert not app.exception and expected in app.session_state.messages[-1][1]
    # Changing search scope does not change the calculation's source provenance.
    app.sidebar.radio[0].set_value('PDF 단독 RAG').run(timeout=90)
    app.chat_input[0].set_value('내 진단 결과를 쉽게 설명해 줘').run(timeout=90)
    assert '93' in app.session_state.messages[-1][1] and '다시 계산해' not in app.session_state.messages[-1][1]
    app.sidebar.number_input[0].set_value(2023).run(timeout=90)
    app.chat_input[0].set_value('내 점수 알려줘').run(timeout=90)
    assert '93' not in app.session_state.messages[-1][1]
    click(app,'leave_guest_review')


def test_default_vector_path_is_lazy_and_builds_real_faiss_with_mock_embeddings(monkeypatch):
    from langchain_core.embeddings import Embeddings
    import src.embedding
    class MockEmbeddings(Embeddings):
        def embed_documents(self,texts):return [[1.,float('코딩' in t),.5] for t in texts]
        def embed_query(self,text):return [1.,float('코딩' in text),.5]
    calls=[]
    def factory(name=None):calls.append(name);return MockEmbeddings()
    monkeypatch.setattr(src.embedding,'get_embeddings',factory)
    monkeypatch.delenv('RAG_VECTOR_DEFAULT')
    monkeypatch.setenv('EMBEDDING_MODEL','workflow-mock-embeddings')
    app=guest()
    assert app.sidebar.toggle[0].value is True and not calls
    click(app,'quick_PDF 단독 RAG')
    assert calls and app.session_state.guest_vector_store.index.ntotal>0
    app.chat_input[0].set_value('코딩 인증 조건이 뭐야?').run(timeout=90)
    assert not app.exception and 'p.5' in app.session_state.messages[-1][1]
    click(app,'leave_guest_review')


def test_vector_initialization_error_exposes_fallback_and_still_answers(monkeypatch):
    import src.embedding
    def unavailable(name=None):raise RuntimeError('simulated model initialization failure')
    monkeypatch.setattr(src.embedding,'get_embeddings',unavailable)
    monkeypatch.setenv('RAG_VECTOR_DEFAULT','1')
    monkeypatch.setenv('EMBEDDING_MODEL','workflow-unavailable')
    app=guest();click(app,'quick_PDF 단독 RAG')
    assert any('벡터 검색 준비 실패' in x.value for x in app.warning)
    app.chat_input[0].set_value('졸업인증 총점').run(timeout=90)
    assert not app.exception and '95점' in app.session_state.messages[-1][1]
    click(app,'leave_guest_review')


def test_source_page_stays_open_after_first_answer_rerender():
    app=guest();click(app,'quick_PDF 단독 RAG')
    app.chat_input[0].set_value('졸업인증 총점').run(timeout=90)
    next(b for b in app.button if b.label=='원문 p.5 열기').click().run(timeout=90)
    assert not app.exception
    source=next(e for e in app.expander if e.label=='출처 PDF 페이지 확인')
    assert source.proto.expanded is True
    assert any(b.label=='이 페이지 PDF 다운로드' for b in app.get('download_button'))
    assert any('p.5' in caption for image in app.get('image') for caption in image.captions)
    click(app,'leave_guest_review')
