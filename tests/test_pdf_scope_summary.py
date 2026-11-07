"""Regress the exact public-app PDF-only preparation question in the live path."""
import pytest
from langchain_core.documents import Document

from src.graduation_rules import load_rules
from src.multilingual import answer_in_language
from src.pdf_loader import load_directory
from src.utils import ROOT

QUESTION='저 문서를 요약해서 졸업인증을 어떻게 준비하는지 알려줘'


@pytest.fixture
def docs():
    result,errors=load_directory(ROOT/'data')
    assert not errors
    return result


@pytest.mark.parametrize('question',[
    QUESTION,
    '제공된 PDF를 정리해서 졸업인증 준비 방법을 알려줘',
    '졸업요건은 어떻게 준비해야 해?',
])
def test_pdf_only_summary_without_website_sources(question,docs):
    text,hits=answer_in_language(question,docs,'AI·빅데이터학과',2022,None,False,'ko',False)
    main=text.partition('\n\n근거 원문:\n')[0]
    assert hits and all(d.metadata['source']==load_rules()['source'] and d.metadata['page']==5 for d in hits)
    for expected in ['95점','대학공통 45점','교과 10점','비교과지정 21점','비교과미지정 19점','예비창업설계','학과활동','자격증','코딩역량','국제사회언어','개인 졸업을 확정하지 않습니다']:
        assert expected in main
    assert 'TOPCIT 응시' not in main and '200점' not in main


def test_summary_keeps_selected_admission_year(docs):
    text,hits=answer_in_language(QUESTION,docs,'AI·빅데이터학과',2023,None,False,'ko',False)
    assert hits and '2023학번' in text and '교과 5점' in text and '비교과지정 26점' in text
    assert 'TOPCIT 응시' in text


def test_summary_in_multiple_document_scope_keeps_additional_evidence(docs):
    extra=Document(page_content='AI·빅데이터학과 2022학번 졸업인증 준비 지침: 학과 담당자의 공지를 확인하세요.',metadata={'source':'synthetic-preparation-guide.pdf','page':1})
    text,hits=answer_in_language(QUESTION,docs+[extra],'AI·빅데이터학과',2022,None,False,'ko',False)
    assert {d.metadata['source'] for d in hits}=={load_rules()['source'],extra.metadata['source']}
    assert extra.metadata['source'] in text and '학과 담당자의 공지' in text and '95점' in text


def test_preparation_verb_does_not_remove_unsupported_subjects(docs):
    text,hits=answer_in_language('저 문서를 요약해서 우주여행 졸업인증을 어떻게 준비하는지 알려줘',docs,'AI·빅데이터학과',2022,None,False,'ko',False)
    assert not hits and '근거를 확인할 수 없습니다' in text


def test_actual_guest_pdf_only_and_multi_document_menu_summary(monkeypatch,tmp_path):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR',str(tmp_path/'accounts'))
    monkeypatch.setenv('RAG_VECTOR_DEFAULT','0')
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    next(b for b in app.button if b.key=='guest_review_entry').click().run(timeout=90)
    for menu in ['PDF 단독 RAG','다중 문서 RAG']:
        app.sidebar.radio[0].set_value(menu).run(timeout=90)
        app.chat_input[0].set_value(QUESTION).run(timeout=90)
        assert not app.exception
        result=app.session_state.messages[-1][1]
        assert '95점' in result and 'p.5' in result and '예비창업설계' in result
        assert '등록된 문서에서 질문의 근거를 확인할 수 없습니다' not in result
    next(b for b in app.sidebar.button if b.key=='leave_guest_review').click().run(timeout=90)
