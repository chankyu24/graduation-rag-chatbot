import pytest
from src.graduation_rules import get_rule, common_items
from src.graduation_checker import check
D='AI·빅데이터학과'

def full_input(year=2022):
    activities={i['name']:True for i in common_items(year)}
    activities.update({'학과활동':5,'코딩역량인증제 Level2 이상':2,'AI·SW전공역량졸업인증제':True})
    evidence={
        '중핵교양 국제사회언어영역 택1':{'course':'공식언어영역이수과목','confirmed':True},
        '자격증/경진대회참가/경진대회수상':{'certificates':['SQL개발자']},
        '비교과자율활동(공감)':{'points':5,'confirmed':True},
        '비교과자율활동(창의)':{'points':4,'confirmed':True},
        '비교과자율활동(글로벌)':{'points':10,'confirmed':True},
    }
    return ['예비창업설계','공식언어영역이수과목'],activities,evidence

def test_ai_2022_source_totals():
    rule=get_rule(D,2022)
    assert rule['page']==5
    assert list(rule['required'].values())==[45,10,21,19]
    assert sum(i['points'] for i in rule['items'] if i['area']=='비교과지정')==21
    assert sum(i['points'] for i in rule['items'] if i['area']=='비교과미지정')==19

def test_ai_all_satisfied_95():
    c,a,e=full_input(); r=check(D,2022,c,a,evidence=e)
    assert r['status']=='충족'
    assert r['total_earned']==r['total_required']==95
    assert [i['earned'] for i in r['areas']]==[45,10,21,19]
    assert not r['missing'] and not r['issues']

def test_ai_partial_courses():
    c,a,e=full_input(); r=check(D,2022,c[1:],a,evidence=e)
    assert r['status']=='미충족' and '예비창업설계' in r['missing']
    assert r['total_earned']==90

def test_ai_lacking_autonomous_cannot_offset():
    c,a,e=full_input(); e['비교과자율활동(공감)']['points']=4; e['비교과자율활동(글로벌)']['points']=999
    r=check(D,2022,c,a,evidence=e)
    assert r['status']=='미충족'
    assert next(i for i in r['areas'] if i['area']=='비교과미지정')['earned']==18
    assert '비교과자율활동(공감)' in r['missing']

def test_ai_unknown_autonomous():
    c,a,e=full_input(); e['비교과자율활동(공감)']['confirmed']=False
    assert check(D,2022,c,a,evidence=e)['status']=='확인 필요'

def test_ai_no_certificate_missing():
    c,a,e=full_input(); e['자격증/경진대회참가/경진대회수상']={}
    assert check(D,2022,c,a,evidence=e)['status']=='미충족'

@pytest.mark.parametrize('cert',get_rule(D,2022)['items'][3]['certificates'] if 'certificates' in get_rule(D,2022)['items'][3] else ['SQL개발자'])
def test_recommended_certificate(cert):
    c,a,e=full_input(); e['자격증/경진대회참가/경진대회수상']={'certificates':[cert]}
    assert check(D,2022,c,a,evidence=e)['status']=='충족'

def test_ai_competition_official_vs_unknown():
    c,a,e=full_input(); key='자격증/경진대회참가/경진대회수상'
    e[key]={'participation_points':6,'participation_confirmed':False}
    assert check(D,2022,c,a,evidence=e)['status']=='확인 필요'
    e[key]['participation_confirmed']=True
    assert check(D,2022,c,a,evidence=e)['status']=='충족'
    e[key]['participation_points']=3
    r=check(D,2022,c,a,evidence=e)
    assert r['status']=='미충족'
    assert next(i for i in r['items'] if i['name']==key)['earned']==3
    e[key]['participation_points']=11
    with pytest.raises(ValueError): check(D,2022,c,a,evidence=e)

def test_ai_2023_differs():
    c,a,e=full_input(2023); r=check(D,2023,c,a,evidence=e)
    assert 'TOPCIT 응시' in r['missing']
    assert next(i for i in r['areas'] if i['area']=='교과')['required']==5
    a['TOPCIT 응시']=5
    assert check(D,2023,c,a,evidence=e)['status']=='충족'

def test_ai_coding_level1_fails():
    c,a,e=full_input(); a['코딩역량인증제 Level2 이상']=1
    assert check(D,2022,c,a,evidence=e)['status']=='미충족'

def test_ai_official_course_unconfirmed():
    c,a,e=full_input(); e['중핵교양 국제사회언어영역 택1']['confirmed']=False
    assert check(D,2022,c,a,evidence=e)['status']=='확인 필요'


def test_school_discrepancy_does_not_overwrite_pdf():
    c,a,e=full_input()
    result=check(D,2022,c,a,evidence=e,official_requirements={'교과':15})
    assert result['status']=='확인 필요'
    assert result['total_required']==95 and result['total_earned']==95
    assert result['system_discrepancies'] and result['overall_graduation_status']=='확인 필요'


def test_same_course_cannot_fill_two_requirements():
    c,a,e=full_input()
    e['중핵교양 국제사회언어영역 택1']['course']='예비창업설계'
    result=check(D,2022,c,a,evidence=e)
    assert result['status']=='확인 필요'
    assert next(r for r in result['areas'] if r['area']=='교과')['earned']==5
