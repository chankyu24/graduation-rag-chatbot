"""Synthetic extra policy fixtures exercise routing, not new university facts."""
import fitz
import pytest
from langchain_core.documents import Document

from src.advisor import answer_advisor
from src.department_guide import guide_documents
from src.document_manager import save_pdf,load_corpus
from src.pdf_loader import load_directory
from src.utils import ROOT

D='AI·빅데이터학과'


@pytest.fixture
def docs():
    return load_directory(ROOT/'data')[0]


def policy(text,source='synthetic-extra-policy.pdf',page=1,**metadata):
    return Document(page_content=text,metadata={'source':source,'page':page,**metadata})


def test_uploaded_graduation_credit_evidence_is_not_overridden_by_missing_notice(docs):
    extra=policy('AI·빅데이터학과 2022학번 졸업학점은 130학점입니다.')
    text,hits=answer_advisor('졸업학점 몇 학점이야?',docs+[extra],D,2022)
    assert '130학점' in text and extra.metadata['source'] in text and 'p.1' in text
    assert hits==[extra] and '학점 기준이 없습니다' not in text
    assert '자동 진단 규칙을 변경하거나 개인의 최종 졸업을 확정하지 않습니다' in text


def test_extra_required_course_evidence_precedes_original_pdf_list_shortcut(docs):
    extra=policy('AI·빅데이터학과 2022학번 전공영어기초 필수 과목입니다.',page=2)
    text,hits=answer_advisor('전공영어기초 필수야?',docs+[extra]+guide_documents(),D,2022,include_guide=True)
    assert hits==[extra] and extra.metadata['source'] in text and 'p.2' in text
    assert '전공영어기초 필수 과목입니다' in text
    assert '목록에 명시되어 있지' not in text


def test_pdf_only_corpus_keeps_unknown_credits_and_original_course_scope(docs):
    # The same questions have no access to the extra-document fixtures in this corpus.
    text,hits=answer_advisor('졸업학점 몇 학점이야?',docs,D,2022,include_guide=True)
    assert not hits and '학점 기준이 없습니다' in text and '130' not in text
    text,hits=answer_advisor('전공영어기초 필수야?',docs,D,2022,include_guide=True)
    assert hits and '목록에 명시되어 있지' in text and '필수가 아니라는 뜻은 아니며' in text


@pytest.mark.parametrize('text',[
    'AI·빅데이터학과 2023학번 졸업학점은 130학점입니다.',
    '정보보호학과 2022학번 졸업학점은 130학점입니다.',
])
def test_added_credits_do_not_cross_department_or_cohort(docs,text):
    result,hits=answer_advisor('졸업학점 몇 학점이야?',docs+[policy(text)],D,2022)
    assert not hits and '학점 기준이 없습니다' in result and '130' not in result


def test_curriculum_snapshot_is_not_treated_as_added_credit_policy(docs):
    web=policy('AI·빅데이터학과 2022학번 졸업학점은 130학점입니다.',source='synthetic-website',kind='website')
    text,hits=answer_advisor('졸업학점 몇 학점이야?',docs+[web],D,2022,include_guide=True)
    assert not hits and '학점 기준이 없습니다' in text


def test_conflicting_added_credit_sources_are_both_retained(docs):
    first=policy('AI·빅데이터학과 2022학번 졸업학점은 130학점입니다.',source='synthetic-one.pdf')
    second=policy('AI·빅데이터학과 2022학번 졸업학점은 140학점입니다.',source='synthetic-two.pdf')
    text,hits=answer_advisor('졸업학점 몇 학점이야?',docs+[first,second],D,2022)
    assert {doc.metadata['source'] for doc in hits}=={'synthetic-one.pdf','synthetic-two.pdf'}
    assert '130학점' in text and '140학점' in text and '임의로 우선순위를 정하지 않습니다' in text


def test_real_pdf_upload_pipeline_reaches_added_credit_answer(tmp_path):
    # This PDF is generated strictly as a synthetic test file outside project data/.
    text='AI·빅데이터학과 2022학번 졸업학점은 130학점입니다.'
    with fitz.open() as pdf:
        pdf.new_page().insert_text((40,60),text,fontname='korea')
        raw=pdf.tobytes()
    uploaded=save_pdf(raw,'synthetic-upload-policy.pdf',tmp_path)
    docs,errors=load_corpus(ROOT/'data',tmp_path)
    assert not errors
    response,hits=answer_advisor('졸업학점 몇 학점이야?',docs,D,2022)
    assert hits and all(doc.metadata['source']==uploaded.name for doc in hits)
    assert '130' in response and uploaded.name in response
