import pytest
from src.graduation_checker import check
from src.diagnostic_state import input_signature, stamp_result, is_stale
from test_ai_2022 import full_input,D


def test_similar_course_requires_review_instead_of_failure():
    courses,activities,evidence=full_input()
    courses[0]='예비창업설계실습'
    result=check(D,2022,courses,activities,evidence=evidence)
    assert result['status']=='확인 필요'
    row=next(r for r in result['items'] if r['name']=='예비창업설계')
    assert row['earned']==0 and row['status']=='확인 필요'
    assert '동일 과목' in row['action']


def test_missing_course_remains_failure():
    courses,activities,evidence=full_input()
    result=check(D,2022,courses[1:],activities,evidence=evidence)
    assert result['status']=='미충족'
    assert any(r['action']=='예비창업설계: 필수 교과 이수 필요' for r in result['next_steps'])


def test_remaining_participation_count():
    result=check(D,2022,activities={'학과활동':3})
    row=next(r for r in result['items'] if r['name']=='학과활동')
    assert row['remaining_count']==2 and row['shortage']==2
    assert '2회' in row['action']

@pytest.mark.parametrize('flag',['false','true',1,0,None])
def test_confirmation_requires_actual_boolean(flag):
    c,a,e=full_input(); e['비교과자율활동(공감)']['confirmed']=flag
    with pytest.raises(ValueError,match='참/거짓'):
        check(D,2022,c,a,evidence=e)


def test_boolean_activity_cannot_take_arbitrary_score():
    with pytest.raises(ValueError,match='0·1'):
        check(D,2022,activities={'인간사랑':5})


def test_bad_evidence_shape_is_validation_error():
    with pytest.raises(ValueError): check(D,2022,evidence={'활동':[]})
    with pytest.raises(ValueError): check(D,2022,evidence=[])


def test_signature_and_staleness():
    c,a,e=full_input()
    signature=input_signature(D,2022,c,a,True,e,{})
    assert signature==input_signature(D,2022,list(reversed(c))+c,a,True,e,{})
    result=stamp_result({'status':'충족'},signature,'rules1','docs1')
    assert not is_stale(result,signature,'rules1','docs1')
    assert is_stale(result,'changed','rules1','docs1')
    assert is_stale(result,signature,'rules2','docs1')
    assert is_stale(result,signature,'rules1','docs2')
    assert result['generated_at'].endswith('+00:00')
