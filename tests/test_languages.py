import pytest
from src.i18n import tr,item_label,table,LANGUAGES
from src.multilingual import question_to_korean,answer_in_language
from src.pdf_loader import load_directory
from src.utils import ROOT

@pytest.mark.parametrize('lang',['en','zh','ja'])
def test_labels_and_canonical_names(lang):
    assert tr('로그인',lang)!='로그인'
    assert tr('졸업요건 진단',lang)!='졸업요건 진단'
    assert '예비창업설계' in item_label('예비창업설계',lang)
    assert '95' in tr('합계 95점',lang)
    assert list(table([{'status':'충족'}],lang)[0].values())[0]!='충족'

@pytest.mark.parametrize('lang,question',[
    ('en','What are the graduation requirements for 2022?'),
    ('zh','2022级毕业要求是什么？'),
    ('ja','2022年卒業要件を教えてください'),
])
def test_offline_multilingual_question_and_evidence(lang,question):
    docs,_=load_directory(ROOT/'data')
    text,hits=answer_in_language(question,docs,'AI·빅데이터학과',2022,None,False,lang)
    assert hits and '95' in text and 'p.5' in text
    assert '예비창업설계' in text  # Korean original is always retained.


def test_unknown_foreign_topic_not_removed():
    q='What are the space travel graduation requirements?'
    assert question_to_korean(q,'en')==q
    docs,_=load_directory(ROOT/'data')
    assert not answer_in_language(q,docs,'AI·빅데이터학과',2022,None,False,'en')[1]
