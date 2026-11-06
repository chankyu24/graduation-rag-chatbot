"""Synthetic, unsaved evaluation cases; never load another user's student records."""
from math import ceil
from .graduation_rules import get_rule,common_items
from .graduation_checker import check

CASES=['빈 기록','일부 과목만 이수','확인 가능한 조건 충족','필수 과목 누락','자율활동 점수 부족','이수 정보 미확인']


def evaluate_case(department,year,case):
    if case not in CASES: raise ValueError('지원하지 않는 평가 사례입니다.')
    rule=get_rule(department,year)
    if not rule: return check(department,year)
    courses=[]; activities={}; evidence={}
    if case not in {'빈 기록','이수 정보 미확인'}:
        for item in common_items(year)+rule['items']:
            name,kind=item['name'],item['kind']
            if kind=='course': courses.append(name)
            elif kind=='choice': courses.extend(item['options'][:item.get('count',1)])
            elif kind=='count': activities[name]=ceil(item['points']/item['per'])
            elif kind=='threshold': activities[name]=item['minimum']
            elif kind=='check': activities[name]=True
            elif kind=='official_course':
                synthetic='평가용 국제사회언어영역 과목'
                courses.append(synthetic); evidence[name]={'course':synthetic,'confirmed':True}
            elif kind=='official_points': evidence[name]={'points':item['points'],'confirmed':True}
            elif kind=='achievement': evidence[name]={'certificates':item['certificates'][:1]}
        if case=='일부 과목만 이수':
            courses=courses[:1]; activities={}; evidence={}
        elif case=='필수 과목 누락':
            courses=courses[1:]
        elif case=='자율활동 점수 부족':
            entry=next((value for name,value in evidence.items() if name.startswith('비교과자율활동') and 'points' in value),None)
            if entry: entry['points']=max(0,entry['points']-1)
            else:
                name=next((item['name'] for item in rule['items'] if item['area']=='비교과미지정'),None)
                if name: activities[name]=0
    result=check(department,year,courses,activities,complete=case!='이수 정보 미확인',evidence=evidence)
    return dict(result,synthetic=True,evaluation_case=case)
