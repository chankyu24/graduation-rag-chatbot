import pytest
from src.pdf_loader import load_directory
from src.utils import ROOT
from src.rag_chain import answer

@pytest.fixture
def docs(): return load_directory(ROOT/'data')[0]

def test_scoped_year_text(docs):
    text,hits=answer('졸업인증 총점',docs,'AI·빅데이터학과',2022)
    assert hits and '95점' in text and '교과 10점' in text
    assert 'TOPCIT 응시 5점' not in text

def test_unknown_topic(docs):
    text,hits=answer('졸업하려면 우주여행 자격증 몇 점인가요?',docs,'AI·빅데이터학과',2022)
    assert not hits and '확인할 수 없' in text

def test_credits_absent(docs):
    text,hits=answer('졸업학점은 몇 학점인가요?',docs,'AI·빅데이터학과',2022)
    assert not hits and '확인할 수 없' in text

def test_no_key(docs,monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    text,hits=answer('졸업인증 총점',docs,'AI·빅데이터학과',2022,use_llm=True)
    assert hits and 'API 키 없음' in text and 'p.5' in text

def test_api_failure(docs,monkeypatch):
    import langchain_openai
    monkeypatch.setenv('OPENAI_API_KEY','test-placeholder-not-real')
    def failure(**kwargs): raise RuntimeError('synthetic failure')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',failure)
    text,hits=answer('졸업인증 총점',docs,'AI·빅데이터학과',2022,use_llm=True)
    assert hits and 'LLM 연결 실패' in text and '95점' in text


def test_two_cohorts_comparison(docs):
    text,hits=answer('2022학번과 2023학번의 기준은 어떻게 다른가요?',docs,'AI·빅데이터학과',2022)
    assert hits and '교과 10점' in text and '교과 5점' in text and 'TOPCIT 응시 5점' in text

@pytest.mark.parametrize('question',[
    '학과활동은 몇 점으로 인정되나요?',
    '자격증을 취득하면 몇 점을 받을 수 있나요?',
    '졸업을 위해 어떤 과목을 들어야 하나요?',
    '비교과 활동은 어떤 것들이 인정되나요?',
    'TOPCIT 응시는 졸업인증에 포함되나요?',
])
def test_requested_questions(question,docs):
    text,hits=answer(question,docs,'AI·빅데이터학과',2022)
    assert hits and 'p.5' in text
