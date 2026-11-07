from copy import deepcopy
import pytest

from src.diagnostic_state import input_payload,input_signature,stamp_result,consultation_context
from src.graduation_checker import check
from src.multilingual import answer_in_language
from src.pdf_loader import load_directory
from src.utils import ROOT,read_courses
from test_ai_2022 import D,full_input


def context_for(payload,owner='synthetic-user-a',synthetic=False):
    signature=input_signature(**payload)
    result=stamp_result(check(**payload),signature,'rules','original-pdf',inputs=payload,owner_id=owner)
    if synthetic: result['synthetic']=True
    return consultation_context(result,D,2022,signature,'rules','original-pdf',owner)


@pytest.fixture
def docs(): return load_directory(ROOT/'data')[0]


@pytest.fixture
def partial():
    courses,activities,evidence=full_input()
    activities['학과활동']=3
    activities['코딩역량인증제 Level2 이상']=1
    evidence['자격증/경진대회참가/경진대회수상']={}
    evidence['비교과자율활동(글로벌)']['points']=8
    return context_for(input_payload(D,2022,courses,activities,True,evidence,{}))


def ask(question,docs,result,**kwargs):
    return answer_in_language(question,docs,D,2022,None,kwargs.pop('use_llm',False),kwargs.pop('lang','ko'),personal_result=result,**kwargs)


@pytest.mark.parametrize('question,intent',[
 ('나는 어떤 활동이 부족해?','missing'),
 ('졸업인증을 충족하려면 무엇부터 준비해야 해?','priority'),
 ('이미 이수한 과목은 무엇이야?','completed'),
 ('어떤 영역에서 점수가 가장 부족해?','largest'),
 ('자격증을 취득하면 어떤 항목을 충족할 수 있어?','certificate'),
 ('내 진단 결과를 쉽게 설명해 줘.','simple'),
])
def test_exact_requested_personal_questions(question,intent,docs,partial):
    from src.diagnosis_advisor import personal_intent
    assert personal_intent(question,has_result=True)==intent
    text,hits=ask(question,docs,partial)
    assert hits and 'p.5' in text and '80' in text


def test_missing_activities_and_largest_shortage_use_computed_rows(docs,partial):
    text,hits=ask('내 진단에서 부족한 활동은?',docs,partial)
    assert '80 / 95점' in text and '학과활동: 2점 부족, 2회/학기 추가 필요' in text
    assert '비교과자율활동(글로벌): 2점 부족' in text
    assert hits and hits[0].metadata['page']==5
    largest,_=ask('내 진단에서 가장 부족한 영역은?',docs,partial)
    assert '비교과지정 (13점)' in largest and '부족 점수 기준' in largest


def test_priority_puts_missing_required_course_before_larger_certificate_gap(docs,partial):
    payload=deepcopy(partial['input_snapshot']);payload['courses']=payload['courses'][1:]
    result=context_for(payload)
    text,_=ask('내 진단의 준비 우선순위를 알려줘',docs,result)
    assert text.index('- 예비창업설계:')<text.index('- 자격증/경진대회')
    assert '소요 시간이나 난이도를 추정한 순위는 아닙니다' in text


def test_completed_courses_come_from_upload_snapshot_not_every_required_course(docs,partial):
    payload=deepcopy(partial['input_snapshot'])
    payload['courses']=read_courses('과목명,이수여부,성적\n예비창업설계,이수,P\n다른이수과목,이수,B+\n미이수과목,미이수,A+\n낙제과목,이수,F'.encode())
    result=context_for(payload)
    text,_=ask('내가 이미 이수한 과목을 알려줘',docs,result)
    main=text.partition('\n근거: ')[0]
    assert '예비창업설계, 다른이수과목' in main and '미이수과목' not in main and '낙제과목' not in main
    assert '공식 성적 조회 결과가 아닙니다' in main


def test_certificate_what_if_reuses_checker_and_does_not_mutate_record(docs,partial,monkeypatch):
    import langchain_openai
    def forbidden(**kwargs): raise AssertionError('Personal scoring must not call an LLM')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',forbidden)
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-not-real')
    original=deepcopy(partial)
    text,_=ask('SQLD를 따면 내 진단에 도움이 돼?',docs,partial,use_llm=True)
    assert '80 → 86점' in text and '변화 +6점' in text and '가정 계산' in text
    assert '다른 영역의 부족을 대신 채우지 않습니다' in text
    assert partial==original


def test_certificate_gain_respects_existing_competition_points_and_cap(docs,partial):
    payload=deepcopy(partial['input_snapshot']);key='자격증/경진대회참가/경진대회수상'
    payload['evidence'][key]={'participation_points':3,'participation_confirmed':True}
    result=context_for(payload)
    text,_=ask('ADsP를 따면 내 진단에 도움이 돼?',docs,result)
    assert '83 → 86점' in text and '변화 +3점' in text
    payload['evidence'][key]={'certificates':['SQL개발자']}
    result=context_for(payload)
    text,_=ask('SQLD를 따면 내 진단에 도움이 돼?',docs,result)
    assert '86 → 86점' in text and '변화 +0점' in text


def test_unlisted_certificate_never_gets_hypothetical_points(docs,partial):
    text,_=ask('내 진단에서 우주여행 자격증을 따면 도움이 돼?',docs,partial)
    assert '권장 목록에서 확인하지 못했습니다' in text and '가정 계산' not in text


def test_easy_followup_explains_diagnosis_without_hijacking_document_questions(docs,partial):
    text,_=ask('쉽게 설명해줘',docs,partial,previous_question='내 진단에서 부족한 활동은?')
    assert '쉽게 말하면' in text and '80 / 95점' in text and '이외에도 1개 항목' in text
    text,_=ask('졸업인증 총점',docs,partial)
    assert '총 95점' in text and '80 / 95점' not in text


@pytest.mark.parametrize('change',['input','rules','pdf','snapshot'])
def test_changed_provenance_rejects_old_personal_advice(docs,partial,change):
    result=deepcopy(partial)
    args=[result,D,2022,result['input_signature'],'rules','original-pdf','synthetic-user-a']
    if change=='input': args[3]='changed-input'
    elif change=='rules': args[4]='changed-rules'
    elif change=='pdf': args[5]='changed-pdf'
    else: result['input_snapshot']['courses'].append('changed-course')
    context=consultation_context(*args)
    text,hits=ask('내 진단에서 부족한 활동은?',docs,context)
    assert '최신 상태가 아닙니다' in text and '80 / 95점' not in text and not hits


def test_other_owner_profile_and_guest_session_cannot_receive_result(docs,partial):
    signature=partial['input_signature']
    assert consultation_context(partial,D,2022,signature,'rules','original-pdf','synthetic-user-b') is None
    assert consultation_context(partial,D,2023,signature,'rules','original-pdf','synthetic-user-a') is None
    assert consultation_context(partial,'정보보호학과',2022,signature,'rules','original-pdf','synthetic-user-a') is None
    text,hits=answer_in_language('2023학번 내 진단 결과 알려줘',docs,D,2022,None,False,'ko',personal_result=partial)
    assert '개인 진단 내역이 없습니다' in text and '80 / 95점' not in text and not hits


def test_snapshots_are_owned_and_legacy_results_do_not_invent_course_details(docs):
    courses,activities,evidence=full_input()
    payload=input_payload(D,2022,courses,activities,True,evidence,{})
    result=context_for(payload)
    courses.append('later-change');evidence['비교과자율활동(공감)']['points']=0
    assert result['input_snapshot']['evidence']['비교과자율활동(공감)']['points']==5
    legacy={'department':D,'year':2022,'status':'충족','total_earned':95,'total_required':95}
    text,_=ask('내가 이미 이수한 과목은?',docs,legacy)
    assert '과목 입력 상세가 없습니다' in text and '본인이 이수했다고 입력한 과목:' not in text


@pytest.mark.parametrize('lang,question,expected',[
    ('en','What should I prepare first?','Planning order'),
    ('zh','我应该先准备什么？','准备顺序'),
    ('ja','何から準備すればよいですか？','準備順序'),
])
def test_personal_foreign_advice_is_deterministic_and_retains_pdf_evidence(docs,partial,monkeypatch,lang,question,expected):
    import langchain_openai
    def forbidden(**kwargs): raise AssertionError('Personal advice uses offline templates')
    monkeypatch.setattr(langchain_openai,'ChatOpenAI',forbidden)
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-not-real')
    text,hits=ask(question,docs,partial,use_llm=True,lang=lang)
    assert expected in text and '80 / 95' in text
    assert hits and 'p.5' in text and '학과활동' in text


def test_synthetic_demo_result_is_labeled_in_all_languages(docs,partial):
    result=deepcopy(partial);result['synthetic']=True
    for lang,expected in [('ko','가상 시연 입력 결과'),('en','Synthetic demonstration result'),('zh','虚拟演示输入结果'),('ja','架空のデモ入力による結果')]:
        text,_=ask('내 진단 결과를 쉽게 설명해줘',docs,result,lang=lang)
        assert expected in text
