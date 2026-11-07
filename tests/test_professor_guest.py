from pathlib import Path
from streamlit.testing.v1 import AppTest
import pytest
from src.utils import ROOT
from src.account_ui import start_guest_review,clear_identity,persist


@pytest.fixture(autouse=True)
def guest_environment(tmp_path,monkeypatch):
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR',str(tmp_path/'accounts'))
    monkeypatch.setenv('RAG_VECTOR_DEFAULT','0')


def assistant_bodies(app):
    """Only the assistant body may satisfy an answer assertion."""
    return ['\n'.join(element.value for element in message.children.values()
                      if element.type in {'text','markdown'})
            for message in app.chat_message if message.name=='assistant']


def test_guest_sessions_are_separate_and_cleanup_uploads():
    a={};b={};user=start_guest_review(a);start_guest_review(b)
    assert user['account_id']!=b['guest_user']['account_id']
    folder=Path(a['review_directory'].name)
    (folder/'example.pdf').write_bytes(b'temporary-test')
    class Wrapper: session_state={}
    persist(Wrapper(),user,'AI2022')  # Must not write a database profile.
    clear_identity(a)
    assert not folder.exists() and not a
    clear_identity(b)


def test_cloud_entrypoint_uses_platform_port(monkeypatch):
    from deploy import server_arguments
    monkeypatch.setenv('PORT','10000')
    args=server_arguments()
    assert '--server.port=10000' in args and '--server.address=0.0.0.0' in args
    for value in ['bad','0','65536']:
        monkeypatch.setenv('PORT',value)
        with pytest.raises(ValueError): server_arguments()


def test_professor_can_enter_actual_app_without_account():
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    assert not app.exception
    next(b for b in app.button if b.key=='guest_review_entry').click().run(timeout=90)
    assert not app.exception and app.session_state.guest_user['guest']
    assert any(h.value=='교수용 과제 평가' for h in app.subheader)
    app.sidebar.radio[0].set_value('PDF 단독 RAG').run(timeout=90)
    app.chat_input[0].set_value('코딩역량 인증제 조건이 뭐야?').run(timeout=90)
    assert not app.exception and any('Level 2' in body and 'p.5' in body for body in assistant_bodies(app))
    app.sidebar.radio[0].set_value('다중 문서 RAG').run(timeout=90)
    assert any(u.label=='PDF 추가' for u in app.get('file_uploader'))
    app.sidebar.radio[0].set_value('졸업요건 진단').run(timeout=90)
    next(b for b in app.button if b.label=='나의 졸업인증 진단').click().run(timeout=90)
    assert not app.exception and app.session_state.result['total_required']==95
    app.sidebar.radio[0].set_value('진단 결과').run(timeout=90)
    assert not app.exception
    folder=Path(app.session_state.review_directory.name)
    next(b for b in app.sidebar.button if b.key=='leave_guest_review').click().run(timeout=90)
    assert not app.exception and not folder.exists()
    assert any(b.key=='guest_review_entry' for b in app.button)


def test_guest_vector_and_corpus_are_session_scoped(monkeypatch):
    from langchain_core.embeddings import Embeddings
    import langchain_huggingface
    from src.document_manager import save_pdf
    import fitz
    class TestEmbeddings(Embeddings):
        def __init__(self,**kwargs): pass
        def embed_documents(self,texts): return [self.embed_query(t) for t in texts]
        def embed_query(self,text): return [float('POLICY' in text),1.0,1.0]
    monkeypatch.setattr(langchain_huggingface,'HuggingFaceEmbeddings',TestEmbeddings)
    monkeypatch.setenv('EMBEDDING_MODEL','session-test-fixture')
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    next(b for b in app.button if b.key=='guest_review_entry').click().run(timeout=90)
    app.sidebar.radio[0].set_value('학과·졸업 통합 상담').run(timeout=90)
    count=len(app.session_state.guest_corpus[0])
    app.run(timeout=90)
    assert len(app.session_state.guest_corpus[0])==count==8
    app.sidebar.radio[0].set_value('다중 문서 RAG').run(timeout=90)
    next(t for t in app.sidebar.toggle if t.label=='다국어 임베딩 + FAISS').set_value(True).run(timeout=90)
    assert not app.exception and app.session_state.guest_vector_store.index.ntotal>0
    folder=Path(app.session_state.review_directory.name)
    with fitz.open() as pdf:
        pdf.new_page().insert_text((40,60),'PRIVATE_GUEST_POLICY 123')
        raw=pdf.tobytes()
    save_pdf(raw,'test.pdf',folder)
    app.run(timeout=90)
    assert not app.exception and len(app.session_state.guest_corpus[0])==9
    app.chat_input[0].set_value('PRIVATE_GUEST_POLICY').run(timeout=90)
    assert not app.exception and any('123' in body for body in assistant_bodies(app))
    next(b for b in app.sidebar.button if b.key=='leave_guest_review').click().run(timeout=90)
    assert not folder.exists() and 'guest_vector_store' not in app.session_state


def test_chat_renders_assistant_markdown_without_enabling_untrusted_html(monkeypatch):
    import src.multilingual
    main='**테스트 답변** <script>alert("assistant")</script>'
    source='[1] fixture.pdf p.1\n<svg onload="alert(1)">원문</svg>'
    monkeypatch.setattr(src.multilingual,'answer_in_language',
                        lambda *args,**kwargs:(main+'\n\n근거 원문:\n'+source,[]))
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    next(b for b in app.button if b.key=='guest_review_entry').click().run(timeout=90)
    app.sidebar.radio[0].set_value('PDF 단독 RAG').run(timeout=90)
    question='<img src=x onerror="alert(2)">를 설명해줘'
    app.chat_input[0].set_value(question).run(timeout=90)
    assert not app.exception
    user=next(message for message in app.chat_message if message.name=='user')
    assistant=next(message for message in app.chat_message if message.name=='assistant')
    assert [text.value for text in user.text]==[question]
    body=[element for element in assistant.children.values() if element.type=='markdown']
    assert len(body)==1 and body[0].value==main
    assert body[0].proto.allow_html is False
    assert [text.value for text in assistant.expander[0].text]==[source]
