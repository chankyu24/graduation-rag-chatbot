from types import SimpleNamespace
import pytest
from src.utils import read_courses, ROOT
from src.response_guard import checked_response
from src.pdf_loader import load_directory
from src.rag_chain import answer


@pytest.mark.parametrize('csv', [
    '과목명,과목 명,이수여부\n미이수과목,예비창업설계,이수',
    '과목명,이수여부,성적\n예비창업설계,이수',
    '과목명,이수여부\n"예비창업설계,이수',
    '과목명,이수여부,\n예비창업설계,이수,P',
    '과목명,이수여부\n예비창업설계,이수,추가값',
])
def test_malformed_course_file_is_rejected(csv):
    with pytest.raises(ValueError): read_courses(csv.encode('utf-8'))


def test_csv_multiline_quoted_course_and_failure_filter():
    assert read_courses(('과목명,이수여부,성적\r\n"과목,이름",이수,P\r\n'
                         '미이수,미이수,A+\r\n실패,이수,NP\r\n'
                         '예비창업설계,이수,P\r\n예비창업설계,이수,P').encode()) == ['과목,이름','예비창업설계']


@pytest.mark.parametrize('content', ['총 130점입니다. [1]', '총 95점입니다. [9]', '총 95점입니다.', '', [{'text':'95점 [1]'}]])
def test_generation_guard_rejects_unsupported_claims(content):
    with pytest.raises(ValueError): checked_response(content, '총점 95점', 1)


def test_generation_guard_keeps_supported_citation():
    assert checked_response('총 95점입니다. [1]', '총점 95점', 1)=='총 95점입니다. [1]'


def test_actual_rag_generation_falls_back_on_invented_numbers(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key-not-real')
    import langchain_openai
    class FakeModel:
        def __init__(self,**kwargs): pass
        def invoke(self,messages): return SimpleNamespace(content='졸업하려면 999점이 필요합니다. [1]')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',FakeModel)
    docs,_=load_directory(ROOT/'data')
    text,hits=answer('졸업인증 총점',docs,'AI·빅데이터학과',2022,use_llm=True)
    assert hits and '999' not in text and '95점' in text and '원문 검색 결과로 전환' in text


def test_actual_rag_preserves_valid_generated_answer(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key-not-real')
    import langchain_openai
    class FakeModel:
        def __init__(self,**kwargs): pass
        def invoke(self,messages): return SimpleNamespace(content='필요 점수는 총 95점입니다. [1]')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',FakeModel)
    docs,_=load_directory(ROOT/'data')
    text,hits=answer('졸업인증 총점',docs,'AI·빅데이터학과',2022,use_llm=True)
    assert text.startswith('필요 점수는 총 95점입니다. [1]') and hits


def test_uploaded_documents_are_private_between_accounts(tmp_path,monkeypatch):
    import fitz
    from src.document_manager import private_document_directory,save_pdf,load_corpus
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR',str(tmp_path/'users'))
    a=private_document_directory('20220001'); b=private_document_directory('evaluator:teacher')
    assert a!=b and '20220001' not in str(a)
    with fitz.open() as pdf:
        pdf.new_page().insert_text((40,60),'PRIVATE_A_ONLY_POLICY')
        raw=pdf.tobytes()
    save_pdf(raw,'extra.pdf',a)
    base=tmp_path/'base';base.mkdir()
    assert 'PRIVATE_A_ONLY_POLICY' in load_corpus(base,a)[0][0].page_content
    assert load_corpus(base,b)[0]==[]
    assert load_corpus(base,a,False)[0]==[]
    with pytest.raises(ValueError): private_document_directory('')
