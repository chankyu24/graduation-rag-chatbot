"""Regressions for the actual three-turn question sequence, without paid calls."""
from types import SimpleNamespace
import pytest
from src.advisor import answer_advisor,resolve_question
from src.pdf_loader import load_directory
from src.utils import ROOT
from src.graduation_rules import get_rule,load_rules
from src.rag_chain import scoped_original

D='AI·빅데이터학과'

@pytest.fixture(scope='module')
def docs(): return load_directory(ROOT/'data')[0]


def test_actual_three_turn_sequence_preserves_scope_and_explains_required_item(docs):
    previous=None;answers=[]
    for question in ['나는 AI·빅데이터학과 2022학번인데 졸업하려면 뭐가 필요해?','그럼 코딩역량인증은?','그거 안하면 졸업 못해?']:
        text,hits=answer_advisor(question,docs,'의료IT공학과',2024,previous_question=previous)
        assert hits and all(d.metadata['department']==D and d.metadata['year']==2022 and d.metadata['page']==5 for d in hits)
        answers.append(text.partition('\n\n근거 원문:\n')[0])
        resolved,department,year=resolve_question(question,'의료IT공학과',2024,previous)
        # The app stores canonical context separately from the original display.
        previous=f'{department} {year}학번 {resolved}'
    assert '95점' in answers[0] and '예비창업설계' in answers[0]
    assert 'Level 2 이상' in answers[1] and '5점' in answers[1]
    assert '필수 인증 항목' in answers[2] and '미충족' in answers[2]
    assert '최종 졸업 불가를 확정' in answers[2] and '200점' not in answers[2]


def test_new_topic_followup_inherits_explicit_cohort_instead_of_sidebar(docs):
    text,hits=answer_advisor('그럼 코딩역량인증은?',docs,'의료IT공학과',2024,previous_question='AI·빅데이터학과 2022학번 졸업요건 알려줘')
    assert hits and 'AI·빅데이터학과 · 2022학번' in text and all(d.metadata['page']==5 for d in hits)


def test_enabled_llm_without_key_stays_honest_and_conversational(docs,monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    text,hits=answer_advisor('그거 안 하면 졸업 못 해?',docs,D,2022,use_llm=True,previous_question='코딩역량인증제 조건')
    assert hits and 'API 키 없음' in text and '필수 인증 항목' in text and '확정하는 답변은 아닙니다' in text


def test_failed_api_uses_reviewed_rule_without_disclosing_exception_message(docs,monkeypatch):
    import langchain_openai
    monkeypatch.setenv('OPENAI_API_KEY','not-a-real-key')
    class Failed:
        def __init__(self,**kwargs): pass
        def invoke(self,messages): raise RuntimeError('do-not-expose-this-message')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',Failed)
    text,hits=answer_advisor('그거 안 하면 졸업 못 해?',docs,D,2022,use_llm=True,previous_question='코딩역량인증제 조건')
    assert hits and 'LLM 연결 실패' in text and '필수 인증 항목' in text
    assert 'do-not-expose' not in text


def test_certificate_consequence_preserves_alternative_competition_path(docs):
    text,hits=answer_advisor('그거 안 하면 졸업 못 해?',docs,D,2022,previous_question='자격증 인정 점수')
    assert hits and '유일한 충족 경로는 아닙니다' in text and '경진대회' in text and '6점' in text


def test_multi_cohort_followup_requires_clarification(docs):
    text,hits=answer_advisor('그럼 코딩은?',docs,D,2022,previous_question='2022학번과 2023학번의 차이')
    assert not hits and '어느 입학연도' in text


def test_llm_receives_resolved_followup_and_exact_cohort_evidence(docs,monkeypatch):
    import langchain_openai
    requests=[]
    class Recorder:
        def __init__(self,**kwargs): pass
        def invoke(self,messages):
            requests.append(messages)
            return SimpleNamespace(content='코딩역량인증제는 Level 2 이상, 5점 항목입니다. [1]')
    monkeypatch.setenv('OPENAI_API_KEY','not-a-real-key')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',Recorder)
    text,hits=answer_advisor('그거 안 하면 졸업 못 해?',docs,'의료IT공학과',2024,use_llm=True,previous_question='AI·빅데이터학과 2022학번 코딩역량인증제 조건')
    assert requests and hits and '[1]' in text
    payload=requests[-1][1][1]
    assert '코딩역량인증제' in payload and '안 하면' in payload
    assert 'AI·빅데이터학과 / 2022학번' in payload
    assert 'TOPCIT 응시 5점' not in payload and '200점' not in payload


@pytest.mark.parametrize('department,year,question',[
    (D,2022,'졸업인증 총점은?'),
    (D,2022,'코딩역량인증제 조건은?'),
    (D,2022,'학과활동 기준은?'),
    (D,2022,'자격증 인정 점수는?'),
    ('의료IT공학과',2024,'코딩역량인증제 조건은?'),
],ids=['ai2022-total','ai2022-coding','ai2022-activities','ai2022-certificate','medical2024-coding'])
def test_retrieved_scope_is_passed_to_mock_llm_without_foreign_cohort(department,year,question,docs,monkeypatch):
    """Inspect actual model input construction; this makes no API request."""
    import langchain_openai
    requests=[]
    class CaptureModel:
        def __init__(self,**kwargs): pass
        def invoke(self,messages):
            requests.append(messages)
            return SimpleNamespace(content='제공된 문서 근거를 확인했습니다. [1]')
    monkeypatch.setenv('OPENAI_API_KEY','test-placeholder-no-network-call')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',CaptureModel)
    text,hits=answer_advisor(question,docs,department,year,use_llm=True)
    assert len(requests)==1 and len(hits)==1 and '[1]' in text
    rule=get_rule(department,year)
    expected=scoped_original(rule,year)
    payload=requests[0][1][1]
    evidence=payload.partition('\n근거:\n')[2]
    assert f'{department} / {year}학번' in payload
    assert f"[1] {rule['source']} p.{rule['page']}" in evidence
    assert evidence==f"[1] {rule['source']} p.{rule['page']}\n{expected.page_content}"
    assert hits[0].metadata['department']==department
    assert hits[0].metadata['year']==year and hits[0].metadata['page']==rule['page']
    for other_department in {r['department'] for r in load_rules()['profiles']}-{department}:
        assert other_department+' / ' not in evidence
    for other_year in range(2016,2027):
        if other_year!=year: assert f'/ {other_year}학번 /' not in evidence
