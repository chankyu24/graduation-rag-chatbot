"""Deterministic certification evaluation. No LLM participates in scoring."""
from difflib import get_close_matches
from math import isfinite, ceil
from .graduation_rules import get_rule, common_items
from .utils import normalize


def number(value, label, integer=False, allow_bool=False):
    if (isinstance(value, bool) and not allow_bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise ValueError(f'{label}: 0 이상의 유한한 숫자가 필요합니다.')
    if integer and int(value) != value:
        raise ValueError(f'{label}: 정수 횟수가 필요합니다.')
    return value


def check(department, year, courses=(), activities=None, complete=True, evidence=None, official_requirements=None):
    if type(year) is not int:
        raise ValueError('입학연도는 정수로 입력하세요.')
    if not isinstance(courses, (list, tuple, set, frozenset)) or any(not isinstance(course, str) for course in courses):
        raise ValueError('수강 과목은 과목명 문자열 목록으로 입력하세요.')
    if official_requirements is not None and not isinstance(official_requirements, dict):
        raise ValueError('학사시스템 필요 점수는 영역별 사전이어야 합니다.')
    rule = get_rule(department, year)
    if not rule:
        return dict(status='확인 필요', issues=['해당 학과·학번 기준 없음'], areas=[], items=[], missing=[])
    activities = {} if activities is None else activities
    evidence = {} if evidence is None else evidence
    if not isinstance(activities, dict) or not isinstance(evidence, dict):
        raise ValueError('활동과 증빙 정보는 이름별 사전이어야 합니다.')
    if type(complete) is not bool:
        raise ValueError('입력 완료 여부는 참/거짓이어야 합니다.')
    for label, record in evidence.items():
        if not isinstance(record, dict):
            raise ValueError(label+': 증빙 정보는 사전이어야 합니다.')
        for flag in ['confirmed', 'participation_confirmed', 'award_confirmed', 'complete']:
            if flag in record and type(record[flag]) is not bool:
                raise ValueError(label+': 확인 여부는 참/거짓이어야 합니다.')
        if 'certificates' in record and (not isinstance(record['certificates'], (list, tuple)) or any(not isinstance(c, str) for c in record['certificates'])):
            raise ValueError(label+': 자격증은 이름 목록이어야 합니다.')
        if 'course' in record and not isinstance(record['course'], str):
            raise ValueError(label+': 이수 과목명은 문자열이어야 합니다.')
    for label, value in activities.items():
        number(value, label, allow_bool=True)
    names = {normalize(n) for n in courses if normalize(n)}
    issues, results = list(rule.get('notes', [])), []
    items = common_items(year) + rule['items']
    if not common_items(year):
        issues.append('2019학번 이전 대학공통 세부 기준 없음')
    course_options = {normalize(i['name']) for i in items if i['kind']=='course'} | {normalize(n) for i in items for n in i.get('options', [])}
    pending_matches = {}
    for entered in sorted(names-course_options):
        suggestions = get_close_matches(entered, sorted(course_options-names), n=1, cutoff=.65)
        if suggestions:
            pending_matches.setdefault(suggestions[0], []).append(entered)
    for item in items:
        kind, name = item['kind'], item['name']
        value, earned, uncertain = activities.get(name, 0), 0, False
        detail = ''
        record = evidence.get(name, {})
        if kind == 'course':
            earned = item['points'] if normalize(name) in names else 0
        elif kind == 'choice':
            earned = item['points'] if len({normalize(n) for n in item['options']} & names) >= item.get('count', 1) else 0
        if kind=='course' and not earned and normalize(name) in pending_matches:
            uncertain=True
            detail='유사 과목명 '+', '.join(pending_matches[normalize(name)])+'의 동일 과목 여부 확인 필요; 자동 인정하지 않음'
        if kind=='choice' and not earned and any(normalize(option) in pending_matches for option in item['options']):
            uncertain=True
            detail='선택 필수 과목의 유사 명칭이 있습니다. 동일 과목 여부 확인 필요; 자동 인정하지 않음'
        if kind == 'count':
            earned = min(item['points'], number(value, name, True) * item['per'])
        elif kind == 'threshold':
            earned = item['points'] if number(value, name) >= item['minimum'] else 0
        elif kind == 'official_course':
            course = record.get('course', '')
            if normalize(course) in {normalize(entry['name']) for entry in rule['items'] if entry['kind']=='course'}:
                uncertain = True
                detail = '다른 필수 교과와 동일 과목을 중복 배정할 수 없습니다. 공식 교과 영역 확인 필요'
            elif record.get('confirmed') and normalize(course) in names:
                earned = item['points']
                detail = f'공식 영역 이수 확인: {course}'
            elif record.get('confirmed') and not course:
                detail = '공식 이수 내역 없음'
            else:
                uncertain = True
                detail = '중핵교양 영역 확인과 이수 과목명 필요'
        elif kind == 'official_points':
            if record.get('confirmed'):
                earned = min(item['points'], number(record.get('points', 0), name))
                detail = '학사시스템 인정 점수에 대한 사용자 확인 기준'
            else:
                uncertain = True
                detail = '자율활동의 인재상별 공식 인정 점수 미확인'
        elif kind == 'achievement':
            certificates = {normalize(s) for s in record.get('certificates', [])}
            allowed = {normalize(s) for s in item['certificates']}
            if certificates - allowed:
                uncertain = True
                detail = '목록 외 자격증은 자동 인정하지 않습니다.'
            if certificates & allowed:
                earned = item['points']  # Recommended certificate is explicitly 6 points in source.
                detail = 'PDF 권장 자격증 취득 6점'
            competition = 0
            for category, bounds in [('participation', item['participation_range']), ('award', item['award_range'])]:
                pts = number(record.get(category + '_points', 0), category)
                if pts and not bounds[0] <= pts <= bounds[1]:
                    raise ValueError(f'{name}: {category} 인정 점수는 {bounds[0]}~{bounds[1]} 범위여야 합니다.')
                if pts and not record.get(category + '_confirmed'):
                    uncertain = True
                    detail = '대회별 배점이 없으므로 공식 인정 점수 확인 필요'
                elif pts:
                    # Do not sum potentially duplicated participation and award evidence.
                    competition = max(competition, pts)
            earned = min(item['points'], max(earned, competition))
            if earned >= item['points']:
                uncertain = False
            elif not record.get('complete', complete):
                uncertain = True
        elif kind == 'unknown':
            uncertain = True
            detail = '원문만으로 세부 인정 기준 판단 불가'
        elif kind == 'check':
            if value not in (False, True, 0, 1):
                raise ValueError(name+': 이수/인증 여부는 참·거짓 또는 0·1이어야 합니다.')
            earned = item['points'] if value else 0
        elif kind not in {'course', 'choice'}:
            raise ValueError(name+': 지원하지 않는 규칙 종류 '+str(kind))
        status = '충족' if earned >= item['points'] else '확인 필요' if uncertain or not complete else '미충족'
        if status == '확인 필요':
            issues.append(f'{name}: {detail or "입력 정보 확인 필요"}')
        shortage=max(0,item['points']-earned)
        remaining_count=ceil(shortage/item['per']) if kind=='count' else None
        action=''
        if status=='확인 필요': action=detail or '입력 또는 공식 인정 내역을 확인하세요.'
        elif status=='미충족':
            if kind=='count': action=f'{name}: {remaining_count}회(학기) 추가 필요'
            elif kind=='threshold': action=f"{name}: 최소 기준 {item['minimum']} 이상 필요"
            elif kind in {'course','choice','official_course'}: action=name+': 필수 교과 이수 필요'
            else: action=f'{name}: {shortage:g}점 부족'
        results.append(dict(name=name, area=item['area'], required=item['points'], earned=earned,
                            status=status, detail=detail, shortage=shortage,
                            remaining_count=remaining_count, action=action))
    known = {normalize(i['name']) for i in items if i['kind'] == 'course'} | {normalize(n) for i in items for n in i.get('options', [])}
    known |= {normalize(r.get('course', '')) for r in evidence.values() if isinstance(r, dict)}
    for name in sorted(names - known):
        near = get_close_matches(name, known, n=1, cutoff=.65)
        if near:
            issues.append(f'{name}: {near[0]}와 동일 과목인지 확인 필요; 자동 인정하지 않음')
    differences = []
    for area, value in (official_requirements or {}).items():
        number(value, area)
        if area not in rule['required']:
            raise ValueError('알 수 없는 영역: '+area)
        if value != rule['required'][area]:
            message=f"{area}: PDF 필요 {rule['required'][area]}점 / 입력한 학사시스템 필요 {value}점 · 기준 차이 확인 필요"
            differences.append(message); issues.append(message)
    areas = []
    for area, required in rule['required'].items():
        rows = [i for i in results if i['area'] == area]
        current = min(required, sum(i['earned'] for i in rows))
        status = '미충족' if any(i['status'] == '미충족' for i in rows) else '확인 필요' if any(i['status'] == '확인 필요' for i in rows) else '충족' if current >= required else '확인 필요'
        if not rows or sum(i['required'] for i in rows) < required:
            status = '확인 필요'
            issues.append(area + ': 세부 규칙 합계가 영역 필요 점수보다 작음')
        areas.append(dict(area=area, required=required, earned=current, shortage=max(0, required-current), status=status))
    missing = [i['name'] for i in results if i['status'] == '미충족']
    status = '미충족' if missing or any(a['status'] == '미충족' for a in areas) else '확인 필요' if issues or not complete or any(a['status'] == '확인 필요' for a in areas) else '충족'
    return dict(status=status, next_steps=[dict(name=i['name'], area=i['area'], status=i['status'], action=i['action']) for i in results if i['action']], overall_graduation_status='확인 필요', system_discrepancies=differences, issues=list(dict.fromkeys(issues)), missing=missing, areas=areas, items=results,
                total_earned=sum(a['earned'] for a in areas), total_required=sum(rule['required'].values()),
                department=department, year=year, source=rule['source'], page=rule['page'],
                scope='제공 PDF의 다면적 졸업인증만 진단. 사용자 입력·공식 인정 확인을 전제로 하며 졸업학점과 최종 졸업 확정은 학사시스템에서 확인하세요.')
