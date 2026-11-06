import pytest
from src.advisor import answer_advisor,resolve_question
from src.rag_chain import admission_years
from src.pdf_loader import load_directory
from src.utils import ROOT

D='AI·빅데이터학과'

@pytest.fixture(scope='module')
def docs(): return load_directory(ROOT/'data')[0]

@pytest.mark.parametrize('question,expected',[
    ('SQLD 따면 몇점이야?','SQL개발자'),
    ('ADsP 자격증 인정돼?','데이터분석준전문가'),
    ('sqld 따면 몇 점이야?','SQL개발자'),
])
def test_known_certificate_abbreviations_use_pdf_terms(question,expected,docs):
    text,hits=answer_advisor(question,docs,D,2022)
    summary=text.split('\n\n근거 원문:')[0]
    assert hits and expected in summary and '6점' in summary and 'p.5' in summary


def test_coding_colloquial_alias(docs):
    text,hits=answer_advisor('코테 레벨 몇이어야돼?',docs,D,2022)
    assert hits and 'Level 2 이상' in text and '5점' in text


def test_multiple_explicit_items_are_all_in_answer_summary(docs):
    text,hits=answer_advisor('인간사랑과 예비창업설계는 필수야?',docs,D,2022)
    summary=text.split('\n\n근거 원문:')[0]
    assert hits and '인간사랑' in summary and '예비창업설계' in summary


def test_explicit_cohort_is_not_calendar_year():
    assert admission_years('2023학번 코딩 시험 2026년 일정은?')==['2023']
    _,department,year=resolve_question('2023학번 코딩 시험 2026년 일정은?',D,2022)
    assert department==D and year==2023


def test_calendar_year_does_not_change_followup_cohort(docs):
    q,department,year=resolve_question('그럼 2026년 시험 일정은?',D,2022,previous_question='2023학번 코딩 조건 뭐야?')
    assert department==D and year==2023
    text,hits=answer_advisor('그럼 2026년 시험 일정은?',docs,D,2022,previous_question='2023학번 코딩 조건 뭐야?')
    assert hits and all(d.metadata.get('year')==2023 for d in hits) and '확인할 수 없' in text


def test_cross_department_question_does_not_use_selected_website(docs):
    text,hits=answer_advisor('정보보호학과와 AI·빅데이터학과 예비창업설계 몇 학점이야?',docs,D,2022,include_guide=True)
    assert not hits and '학과를 하나씩' in text


@pytest.mark.parametrize('question',['우주여행 SQLD 자격증 몇 점이야?','알수없는자격증 인정돼?'])
def test_aliases_never_drop_unsupported_subject(question,docs):
    _,hits=answer_advisor(question,docs,D,2022)
    assert not hits
