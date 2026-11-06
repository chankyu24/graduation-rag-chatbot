import json
from .utils import ROOT,normalize
def load_rules(): return json.loads((ROOT/'rules/graduation_rules.json').read_text(encoding='utf-8'))
def get_rule(department,year):
 return next((r for r in load_rules()['profiles'] if normalize(r['department'])==normalize(department) and r['years'][0]<=int(year)<=r['years'][1]),None)
def common_items(year):
 if not 2019<=year<=2026: return []
 pairs=[('인간사랑',5),('ASP(1,2학기)',5),('자기주도상담',5),('봉사학습',5)]
 if year<=2022: pairs += [('자기개발과전공탐색',5),('졸업필수활동',15),('현대기본영어',5)]
 elif year==2023: pairs += [('자기개발과전공탐색(M&M)',5),('졸업종합지도',15),('현대기본영어',5)]
 else: pairs += [('자기개발과전공탐색(M&M)',5),('졸업및취ㆍ창업지도',13),('학습윤리-기본',1),('학습윤리-심화',1),('현대실용영어',5)]
 return [dict(name=n,points=p,area='대학공통',kind='check') for n,p in pairs]
