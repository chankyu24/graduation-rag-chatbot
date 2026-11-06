import pytest
from src.graduation_rules import get_rule,load_rules,common_items
from src.graduation_checker import check
from src.utils import read_courses
D='컴퓨터소프트웨어공학과'
def test_cohorts():
 a=get_rule(D,2023); b=get_rule(D,2025)
 assert sum(a['required'].values())==104
 assert next(i for i in a['items'] if i['name']=='학술제발표')['points']==10
 assert next(i for i in b['items'] if i['name']=='학술제발표')['points']==6
 assert any(i['name']=='학과MT참여' for i in b['items'])
def test_department():
 assert sum(get_rule('정보보호학과',2023)['required'].values())==110
 assert sum(get_rule('의료IT공학과',2024)['required'].values())==89
 assert get_rule('없는학과',2023) is None
def test_repeat_cap():
 r=check(D,2025,activities={'전공상담':100,'학과MT참여':2,'TOPCIT 응시(자율)':3})
 values={i['name']:i['earned'] for i in r['items']}
 assert values['전공상담']==4 and values['학과MT참여']==4
 assert values['TOPCIT 응시(자율)']==3
 assert sum(i['earned'] for i in r['areas'])==11
def test_missing_required_even_with_excess():
 r=check(D,2023,activities={'전공상담':999,'TOPCIT 응시(자율)':999})
 assert r['status']=='미충족' and '캡스톤디자인' in r['missing']
def test_complete_and_uncertain():
 assert check(D,2023,complete=False)['status']=='확인 필요'
 assert check(D,2030)['status']=='확인 필요'
def test_common_45():
 for y in range(2019,2027): assert sum(i['points'] for i in common_items(y))==45
 assert common_items(2018)==[]
def test_threshold():
 r=check('의료IT공학과',2024,activities={'AI·SW전공역량졸업인증제':199})
 assert next(i for i in r['items'] if i['name']=='AI·SW전공역량졸업인증제')['earned']==0
def test_csv_credits_not_points():
 c=read_courses('과목명,이수여부,학점,성적\n캡스톤디자인,이수,99,A\n산학캡스톤디자인,이수,3,F\n'.encode())
 assert c==['캡스톤디자인']
 r=check(D,2023,c)
 assert next(a for a in r['areas'] if a['area']=='교과')['earned']==5
def test_no_fuzzy_credit():
 r=check(D,2023,['캡스톤디자인실습'])
 assert next(a for a in r['areas'] if a['area']=='교과')['earned']==0
 assert any('동일 과목' in s for s in r['issues'])
def test_duplicate_course():
 r=check(D,2023,['캡스톤디자인']*2)
 assert next(a for a in r['areas'] if a['area']=='교과')['earned']==5
@pytest.mark.parametrize('value',[-1,float('nan'),1.5])
def test_invalid_count(value):
 with pytest.raises(ValueError): check(D,2023,activities={'전공상담':value})
def test_profiles_nonoverlap():
 profiles=load_rules()['profiles']
 assert len(profiles)==21
 for a in profiles:
  for b in profiles:
   if a is not b and a['department']==b['department']: assert a['years'][1]<b['years'][0] or b['years'][1]<a['years'][0]
def test_all_pass_branch_with_verified_fixture(monkeypatch):
 import src.graduation_checker as module
 rule=dict(required={'교과':5},items=[dict(name='테스트 과목',points=5,area='교과',kind='course')],source='test',page=1,notes=[])
 monkeypatch.setattr(module,'get_rule',lambda *args:rule)
 monkeypatch.setattr(module,'common_items',lambda y:[] if y<2019 else [])
 # Real profiles intentionally preserve unresolved source conditions; fixture isolates status logic.
 monkeypatch.setattr(module,'common_items',lambda y:[dict(name='공통확인',points=0,area='대학공통',kind='check')])
 assert module.check('테스트',2023,['테스트 과목'])['status']=='충족'
