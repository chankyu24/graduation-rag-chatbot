import re
from types import SimpleNamespace
import pytest
from langchain_core.documents import Document
from src.multilingual import answer_in_language,question_to_korean,_preserves_literals
from src.pdf_loader import load_directory
from src.utils import ROOT

D='AI·빅데이터학과'
DELIMITER='\n\n근거 원문:\n'
QUESTIONS={
 'en':['What are the graduation requirements for 2022?','What are coding certification requirements?','What are certificates?','What are department activities requirements?','What are the required courses?','What are autonomous activities?','What are university common requirements?'],
 'zh':['2022级毕业要求是什么？','编程能力认证要求是什么？','资格证书有哪些？','院系活动需要多少分？','必修课程有哪些？','自主课外活动需要多少分？','大学共同要求是什么？'],
 'ja':['2022年卒業要件を教えてください','コーディング認証要件を教えてください','推奨資格を教えてください','学科活動は何点ですか','必修科目を教えてください','自主課外活動は何点ですか','大学共通の要件を教えてください'],
}

@pytest.fixture(scope='module')
def docs(): return load_directory(ROOT/'data')[0]


@pytest.mark.parametrize('lang,index',[(lang,index) for lang in QUESTIONS for index in range(7)])
def test_complete_offline_topic_wording_and_single_original(lang,index,docs):
    text,hits=answer_in_language(QUESTIONS[lang][index],docs,D,2022,None,False,lang)
    assert hits and len(hits)==1
    summary,separator,original=text.partition(DELIMITER)
    assert separator and summary and 'p.5' in summary and '[1]' in summary
    assert text.count(hits[0].page_content)==1
    assert hits[0].metadata['source'] in original and '예비창업설계' in original
    assert not any(prose in summary for prose in ['입니다','필요합니다','인정됩니다','항목입니다','필요 점수는'])
    expected=[('95','45','10','21','19'),('2','5'),('6','3','10','30'),('1','5'),('5',),('5','4','10'),('45',)][index]
    assert all(value in summary for value in expected)
    if index==4: assert '예비창업설계' in summary and '중핵교양' in summary


@pytest.mark.parametrize('lang,first,followup',[
 ('en','2023 cohort coding certification requirements','Then how many points?'),
 ('zh','2023级编程能力认证要求','那需要多少分？'),
 ('ja','2023年度入学のコーディング認証要件','では何点ですか'),
])
def test_foreign_followup_keeps_original_topic_and_cohort(lang,first,followup,docs):
    text,hits=answer_in_language(followup,docs,D,2022,None,False,lang,previous_question=first)
    summary=text.partition(DELIMITER)[0]
    assert hits and all(d.metadata['year']==2023 for d in hits)
    assert '2023' in summary and '5' in summary and '2' in summary
    assert '95' not in summary  # Follow-up is coding, not total certification points.


@pytest.mark.parametrize('lang,question',[
 ('en','What are the space travel graduation requirements?'),
 ('zh','宇宙旅行毕业要求是什么？'),
 ('ja','宇宙旅行の卒業要件を教えてください'),
])
def test_unknown_foreign_subject_is_never_erased(lang,question,docs):
    assert question_to_korean(question,lang)==question
    text,hits=answer_in_language(question,docs,D,2022,None,False,lang)
    assert not hits and '95' not in text and not re.search('[가-힣]',text)


@pytest.mark.parametrize('lang,question',[
 ('en','2022 cohort coding certification in 2026'),
 ('zh','2022级编程能力认证2026年要求'),
 ('ja','2022年度入学のコーディング認証2026年要件'),
])
def test_cohort_does_not_become_calendar_year(lang,question,docs):
    korean=question_to_korean(question,lang)
    assert '2022학번' in korean and '2026년' in korean and '2026학번' not in korean
    text,hits=answer_in_language(question,docs,D,2023,None,False,lang)
    assert hits and all(d.metadata['year']==2022 for d in hits)


@pytest.mark.parametrize('lang',['en','zh','ja'])
def test_extra_source_evidence_is_not_replaced_or_duplicated(lang,docs):
    extra=Document(page_content='졸업인증 총점 100점',metadata={'source':'conflicting.pdf','page':1})
    text,hits=answer_in_language(QUESTIONS[lang][0],docs+[extra],D,2022,None,False,lang)
    assert len(hits)==2 and 'conflicting.pdf' in text and '100점' in text
    assert text.count(extra.page_content)==1


def test_api_translation_with_invented_number_falls_back(docs,monkeypatch):
    import langchain_openai
    class BadTranslator:
        def __init__(self,**kwargs): pass
        def invoke(self,messages): return SimpleNamespace(content='Required: 9999 points. [1]')
    monkeypatch.setenv('OPENAI_API_KEY','not-a-real-key')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',BadTranslator)
    text,hits=answer_in_language(QUESTIONS['en'][0],docs,D,2022,None,True,'en')
    assert hits and '9999' not in text and '95' in text.partition(DELIMITER)[0]


def test_api_translation_never_receives_source_body(docs,monkeypatch):
    import langchain_openai
    requests=[]
    class RecordingTranslator:
        def __init__(self,**kwargs): pass
        def invoke(self,messages):
            requests.append(messages)
            return SimpleNamespace(content='Required: 95 points. [1]')
    monkeypatch.setenv('OPENAI_API_KEY','not-a-real-key')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',RecordingTranslator)
    text,hits=answer_in_language(QUESTIONS['en'][0],docs,D,2022,None,True,'en')
    translation=[r for r in requests if r[0][1].startswith('Translate the following sourced summary')]
    assert translation and hits
    assert hits[0].page_content not in translation[-1][1][1]
    assert text.count(hits[0].page_content)==1


@pytest.mark.parametrize('lang',['en','zh','ja'])
def test_api_translation_changed_citation_falls_back(lang,docs,monkeypatch):
    import langchain_openai
    class InvalidCitation:
        def __init__(self,**kwargs): pass
        def invoke(self,messages):
            content='Required: 95 points. [9]' if messages[0][1].startswith('Translate the following sourced summary') else '총점은 95점입니다. [1]'
            return SimpleNamespace(content=content)
    monkeypatch.setenv('OPENAI_API_KEY','not-a-real-key')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',InvalidCitation)
    text,hits=answer_in_language(QUESTIONS[lang][0],docs,D,2022,None,True,lang)
    assert hits and '[9]' not in text and '[1]' in text and '95' in text


def test_verified_api_translation_path_remains_usable(docs,monkeypatch):
    import langchain_openai
    class ValidTranslation:
        def __init__(self,**kwargs): pass
        def invoke(self,messages):
            content='A verified total of 95 points. [1]' if messages[0][1].startswith('Translate the following sourced summary') else '총점은 95점입니다. [1]'
            return SimpleNamespace(content=content)
    monkeypatch.setenv('OPENAI_API_KEY','not-a-real-key')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',ValidTranslation)
    text,hits=answer_in_language(QUESTIONS['en'][0],docs,D,2022,None,True,'en')
    assert text.startswith('A verified total of 95 points. [1]') and hits


def test_translation_guard_preserves_page_references_not_just_numbers():
    assert not _preserves_literals('Total 95 points. [1] p.5','Total 95 points and 5. [1]')
    assert _preserves_literals('95 [1] p.5','95 points [1] p.5')
