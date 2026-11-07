"""Exact personal-counseling questions and saved-course recognition boundaries."""
from copy import deepcopy
import pytest

from src.diagnosis_advisor import personal_intent
from src.diagnostic_state import consultation_context
from src.multilingual import answer_in_language
from src.pdf_loader import load_directory
from src.utils import ROOT,read_courses
from test_diagnosis_advisor import context_for
from test_ai_2022 import D,full_input
from src.diagnostic_state import input_payload


@pytest.fixture
def docs(): return load_directory(ROOT/'data')[0]


@pytest.fixture
def partial():
    courses,activities,evidence=full_input()
    activities['학과활동']=3
    evidence['자격증/경진대회참가/경진대회수상']={}
    evidence['비교과자율활동(글로벌)']['confirmed']=False
    courses.append('규정목록밖과목')
    return context_for(input_payload(D,2022,courses,activities,True,evidence,{}))


def ask(question,docs,result,previous=None,lang='ko'):
    return answer_in_language(question,docs,D,2022,None,False,lang,previous_question=previous,personal_result=result)


@pytest.mark.parametrize('question,intent,expected',[
    ('내가 부족한 점수는 몇 점이야?','points','총 18점이 부족'),
    ('어떤 필수 활동을 하지 않았어?','uncompleted','실제로 활동을 하지 않았다고 단정하지 않습니다'),
    ('무엇부터 준비하면 좋을까?','priority','준비 순서'),
    ('자격증을 취득하면 부족한 점수를 채울 수 있어?','certificate','가정 계산'),
    ('현재 상태에서 졸업인증을 충족할 수 있는 방법은?','priority','준비 순서'),
    ('내가 이수한 과목 중 인정되지 않은 과목은?','unrecognized','규정목록밖과목'),
])
def test_exact_final_personal_questions(question,intent,expected,docs,partial):
    assert personal_intent(question,has_result=True)==intent
    text,hits=ask(question,docs,partial)
    assert expected in text and '77 / 95점' in text
    assert hits and 'p.5' in text and '전체 졸업 확정' in text


def test_uncompleted_question_keeps_unconfirmed_evidence_uncertain(docs,partial):
    text,_=ask('어떤 필수 활동을 하지 않았어?',docs,partial)
    assert '학과활동: 2점 부족, 2회/학기 추가 필요' in text
    assert '비교과자율활동(글로벌): 공식 이수·인정 내역 확인 필요' in text
    assert '글로벌 활동을 하지 않았습니다' not in text
    text,hits=ask('어떤 필수 활동을 하지 않았어?',docs,None)
    assert not hits and '개인 진단 내역이 없습니다' in text


def test_unrecognized_courses_distinguish_unknown_similar_and_unconfirmed(docs,partial):
    payload=deepcopy(partial['input_snapshot'])
    payload['courses']=['예비창업설계실습','확인전언어과목','규정목록밖과목']
    payload['evidence']['중핵교양 국제사회언어영역 택1']={'course':'확인전언어과목','confirmed':False}
    result=context_for(payload)
    text,_=ask('내가 이수한 과목 중 인정되지 않은 과목은?',docs,result)
    assert '예비창업설계실습: 유사 과목명' in text
    assert '확인전언어과목: 공식 교과 영역의 인정이 미확인' in text
    assert '규정목록밖과목: 이 PDF의 해당 학번 인증' in text
    assert '전체 졸업학점 불인정을 뜻하지 않습니다' in text


def test_failed_and_incomplete_original_rows_are_not_claimed_as_visible(docs,partial):
    payload=deepcopy(partial['input_snapshot'])
    payload['courses']=read_courses('과목명,이수여부,성적\n원본제외낙제행,이수,F\n원본제외미이수행,미이수,A+\n예비창업설계,이수,P\n목록외이수과목,이수,A+'.encode())
    result=context_for(payload)
    text,_=ask('내가 이수한 과목 중 인정되지 않은 과목은?',docs,result)
    assert '목록외이수과목:' in text
    assert '원본제외낙제행' not in text and '원본제외미이수행' not in text
    assert '- 예비창업설계:' not in text
    assert '이 저장된 이수 목록에 없으므로 여기서 확인하지 않습니다' in text


def test_common_course_requires_separate_official_completion_confirmation(docs,partial):
    payload=deepcopy(partial['input_snapshot']);payload['courses'].append('인간사랑')
    payload['activities']['인간사랑']=False
    text,_=ask('내가 이수한 과목 중 인정되지 않은 과목은?',docs,context_for(payload))
    assert '인간사랑: 과목명은 대학공통 항목과 일치하지만' in text
    payload['activities']['인간사랑']=True
    text,_=ask('내가 이수한 과목 중 인정되지 않은 과목은?',docs,context_for(payload))
    assert '- 인간사랑:' not in text


def test_choice_course_is_not_declared_invalid_when_combination_is_incomplete(docs):
    from src.graduation_checker import check
    from src.diagnostic_state import input_signature,stamp_result
    department='컴퓨터소프트웨어공학과'
    payload=input_payload(department,2021,['전공영어1'],{},True,{},{});signature=input_signature(**payload)
    result=stamp_result(check(**payload),signature,'rules','original-pdf',inputs=payload,owner_id='synthetic-user-a')
    result=consultation_context(result,department,2021,signature,'rules','original-pdf','synthetic-user-a')
    text,hits=answer_in_language('내가 이수한 과목 중 인정되지 않은 과목은?',docs,department,2021,None,False,'ko',personal_result=result)
    assert '전공영어1: 선택 필수 목록에는 있으나 필요한 조합 전체가 아직 충족되지 않았습니다' in text
    assert '과목 자체의 불인정을 뜻하지 않습니다' in text and hits[0].metadata['page']==1


def test_short_followups_keep_personal_scope_and_certificate_subject(docs,partial):
    text,_=ask('그럼 몇 점?',docs,partial,previous='내가 부족한 점수는 몇 점이야?')
    assert '총 18점이 부족' in text
    text,_=ask('그럼 몇 점?',docs,partial,previous='SQLD를 취득하면 내 진단에 도움이 돼?')
    assert 'SQL개발자 취득' in text and '변화 +6점' in text
    text,_=ask('그럼 어떤 과목?',docs,partial,previous='내가 이수한 과목 중 인정되지 않은 과목은?')
    assert '규정목록밖과목:' in text
    text,hits=ask('그럼 몇 점?',docs,None,previous='내가 부족한 점수는 몇 점이야?')
    assert not hits and '개인 진단 내역이 없습니다' in text


def test_new_intents_preserve_stale_and_owner_isolation(docs,partial):
    stale=consultation_context(partial,D,2022,'changed-input','rules','original-pdf','synthetic-user-a')
    text,hits=ask('내가 이수한 과목 중 인정되지 않은 과목은?',docs,stale)
    assert not hits and '최신 상태가 아닙니다' in text and '규정목록밖과목' not in text
    assert consultation_context(partial,D,2022,partial['input_signature'],'rules','original-pdf','synthetic-user-b') is None
