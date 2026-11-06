import pytest
from src.advisor import answer_advisor,resolve_question
from src.rag_chain import answer
from src.pdf_loader import load_directory
from src.utils import ROOT

@pytest.fixture
def docs(): return load_directory(ROOT/'data')[0]

@pytest.mark.parametrize('question',[
    '코딩역량 인증제 조건이 뭐야',
    '코딩 역량 인증제 조건이 뭔가요?',
    '코딩역량인증제조건이뭐야',
    '코딩 인증 조건 알려줄래?',
])
def test_real_user_coding_phrases(question,docs):
    text,hits=answer_advisor(question,docs,'AI·빅데이터학과',2022)
    assert hits and 'Level 2 이상' in text and '5점' in text and 'p.5' in text

@pytest.mark.parametrize('question',[
    '졸업하려면 뭘 해야해?',
    '22학번 졸업 요건 알려줘',
    '우리 학과 졸업 요건 뭐야',
])
def test_natural_general_requirements(question,docs):
    text,hits=answer_advisor(question,docs,'AI·빅데이터학과',2022)
    assert hits and '95점' in text


def test_followup_keeps_subject(docs):
    text,hits=answer_advisor('그럼 몇 점이야?',docs,'AI·빅데이터학과',2022,previous_question='코딩역량 인증제 조건이 뭐야')
    assert hits and 'Level 2 이상' in text and '5점' in text


def test_context_year_and_department(docs):
    text,hits=answer_advisor('2024학번 의료IT공학과 코딩역량 인증 조건 뭐야',docs,'AI·빅데이터학과',2022)
    assert hits and all(d.metadata['page']==4 for d in hits)
    assert '의료IT공학과' in text and '2024학번' in text


def test_contact_only_in_integrated_scope(docs):
    question='우리 학과 사무실 전화번호 뭐야'
    _,only=answer_advisor(question,docs,'AI·빅데이터학과',2022)
    text,integrated=answer_advisor(question,docs,'AI·빅데이터학과',2022,include_guide=True)
    assert not only and integrated and '041-530-1667' in text and 'https://' in text


def test_curriculum_and_credit_separation(docs):
    text,hits=answer_advisor('예비창업설계 몇 학점이야?',docs,'AI·빅데이터학과',2022,include_guide=True)
    assert hits and '2학점' in text and '졸업인증 점수는 다릅니다' in text
    text,hits=answer_advisor('예비창업설계 필수 과목이야?',docs,'AI·빅데이터학과',2022,include_guide=True)
    assert hits and '5점' in text and 'p.5' in text


def test_website_course_not_declared_unnecessary(docs):
    text,hits=answer_advisor('전공영어기초 필수야?',docs,'AI·빅데이터학과',2022,include_guide=True)
    assert hits and '목록에 명시되어 있지' in text and '필수가 아니라는 뜻은 아니며' in text


def test_grade_curriculum(docs):
    text,hits=answer_advisor('3학년에는 무슨 과목 배워?',docs,'AI·빅데이터학과',2022,include_guide=True)
    assert hits and '자연어처리' in text and '운영체제' in text and 'https://' in text


def test_details_unknown_but_partial_evidence(docs):
    text,hits=answer_advisor('코딩 시험 신청 방법 알려줘',docs,'AI·빅데이터학과',2022)
    assert hits and '세부 방법·일정' in text and 'Level 2 이상' in text


def test_unrelated_and_missing_credit_information(docs):
    for question in ['우주여행 자격증 몇 점인가요?','졸업학점 몇 학점이야?']:
        _,hits=answer_advisor(question,docs,'AI·빅데이터학과',2022,include_guide=True)
        assert not hits


def test_personal_result_missing_and_stale(docs):
    text,_=answer_advisor('나 졸업 가능해?',docs,'AI·빅데이터학과',2022)
    assert '개인 진단 내역이 없습니다' in text
    result={'department':'AI·빅데이터학과','year':2022,'status':'미충족','total_earned':5,'total_required':95,'next_steps':[]}
    text,_=answer_advisor('내 점수 알려줘',docs,'AI·빅데이터학과',2022,personal_result=result)
    assert '5 / 95점' in text
    text,_=answer_advisor('내 점수 알려줘',docs,'AI·빅데이터학과',2022,personal_result=dict(result,_stale=True))
    assert '다시 계산' in text


def test_multi_topic_question(docs):
    text,hits=answer_advisor('코딩이랑 학과활동 조건이 뭐야',docs,'AI·빅데이터학과',2022)
    assert hits and 'Level 2 이상' in text and '회당 1점' in text


def test_pdf_point_answer_not_polluted_by_curriculum(docs):
    from src.department_guide import guide_documents
    text,hits=answer_advisor('졸업인증 총점',docs+guide_documents(),'AI·빅데이터학과',2022,include_guide=True)
    assert '95점' in text and '홈페이지 3학년' not in text
    assert hits and all(doc.metadata.get('kind')!='website' for doc in hits)


def test_followup_preserves_shorthand_cohort(docs):
    text,hits=answer_advisor('그럼 몇 점이야?',docs,'AI·빅데이터학과',2022,previous_question='23학번 코딩 조건이 뭐야')
    assert hits and '2023학번' in text


def test_followup_preserves_explicit_department(docs):
    text,hits=answer_advisor('그럼 몇 점이야?',docs,'AI·빅데이터학과',2022,previous_question='정보보호학과 코딩 조건이 뭐야')
    assert hits and all(doc.metadata['page']==3 for doc in hits) and '정보보호학과' in text


def test_ambiguous_followup_asks_clarification(docs):
    text,hits=answer_advisor('그럼 몇 점이야?',docs,'AI·빅데이터학과',2022,previous_question='코딩이랑 학과활동 조건이 뭐야')
    assert not hits and '어떤 항목' in text


def test_personal_credit_question_not_certification_score(docs):
    personal={'department':'AI·빅데이터학과','year':2022,'status':'충족','total_earned':95,'total_required':95}
    text,hits=answer_advisor('나 졸업학점 몇 학점 필요해?',docs,'AI·빅데이터학과',2022,personal_result=personal)
    assert not hits and '95' not in text and '학점 기준이 없습니다' in text


def test_course_points_not_replaced_with_credit_value(docs):
    text,hits=answer_advisor('예비창업설계 수업은 몇 점이야?',docs,'AI·빅데이터학과',2022,include_guide=True)
    assert hits and '5점' in text and 'p.5' in text
    assert '홈페이지 2학년 교육과정에 2학점' not in text


def test_freeform_api_receives_original_question_with_scoped_evidence(docs,monkeypatch):
    import langchain_openai
    from types import SimpleNamespace
    requests=[]
    class MockModel:
        def __init__(self,**kwargs): pass
        def invoke(self,messages):
            requests.append(messages)
            return SimpleNamespace(content='제공 근거의 졸업인증 필요 점수는 95점입니다. [1]')
    monkeypatch.setenv('OPENAI_API_KEY','test-key-not-real')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',MockModel)
    question='학과 졸업 인증의 전반적인 체계를 설명해줄 수 있니?'
    text,hits=answer_advisor(question,docs,'AI·빅데이터학과',2022,use_llm=True)
    assert hits and '95점' in text and 'p.5' in text
    assert requests and any('전반적인 체계' in message[1] for message in requests[-1])


def test_freeform_rejects_numbers_missing_from_source(docs,monkeypatch):
    import langchain_openai
    from types import SimpleNamespace
    from src.freeform import freeform_answer
    class MockModel:
        def __init__(self,**kwargs): pass
        def invoke(self,messages): return SimpleNamespace(content='졸업인증은 9999점이 필요합니다.')
    monkeypatch.setenv('OPENAI_API_KEY','test-key-not-real')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',MockModel)
    text,hits=freeform_answer('졸업 요건 설명',docs,'AI·빅데이터학과',2022)
    assert not hits and '보류' in text and '9999' not in text
