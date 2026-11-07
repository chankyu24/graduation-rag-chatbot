"""Two-source questions keep each clause's scope and unsupported subjects."""
from src.advisor import answer_advisor
from src.pdf_loader import load_directory,load_pdf
from src.utils import ROOT


def test_original_and_uploaded_document_can_answer_one_composed_question():
    original,_=load_directory(ROOT/'data')
    extra=load_pdf(ROOT/'examples/synthetic_extra_document.pdf')
    text,hits=answer_advisor('졸업인증 총점과 시연자료 확인코드를 함께 알려줘',original+extra,'AI·빅데이터학과',2022)
    assert '95점' in text and 'SCH_DEMO8391' in text and '실제 학교 규정이 아닙니다' in text
    assert {d.metadata['source'] for d in hits}=={original[0].metadata['source'],extra[0].metadata['source']}
    assert 'p.5' in text and 'p.1' in text
    scoped,single_hits=answer_advisor('졸업인증 총점과 시연자료 확인코드를 함께 알려줘',original,'AI·빅데이터학과',2022)
    assert '95점' in scoped and 'SCH_DEMO8391' not in scoped
    assert '근거를 확인할 수 없습니다' in scoped
    assert all(d.metadata['source']==original[0].metadata['source'] for d in single_hits)


def test_composition_does_not_hide_unknown_subject_or_mix_cohorts():
    docs,_=load_directory(ROOT/'data')
    text,hits=answer_advisor('졸업인증 총점과 우주여행 자격 조건을 함께 알려줘',docs,'AI·빅데이터학과',2022)
    assert '95점' in text and '우주여행' in text and '근거를 확인할 수 없습니다' in text
    assert hits and all(d.metadata['year']==2022 for d in hits)


def test_professor_total_and_short_required_conditions_inherit_topic():
    docs,_=load_directory(ROOT/'data')
    text,hits=answer_advisor('AI·빅데이터학과 2022학번 졸업인증 총점과 필수 조건 알려줘',docs,'AI·빅데이터학과',2022)
    assert hits and '95점' in text and '예비창업설계' in text
    assert '근거를 확인할 수 없습니다' not in text
