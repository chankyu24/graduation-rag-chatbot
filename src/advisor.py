"""Source-grounded conversational layer; calculation remains outside the LLM."""
import re
from math import ceil
from .graduation_rules import get_rule,common_items,load_rules
from .utils import normalize
from .rag_chain import answer,normalize_question,admission_years
from .department_guide import guide_data,guide_documents
from .diagnosis_advisor import diagnostic_answer,personal_intent

TOPICS=[
    ('코딩역량인증제',r'코딩|코테|coding'),
    ('AI·SW전공역량졸업인증제',r'AI\s*[·ㆍ・&.]?\s*SW|전공\s*역량'),
    ('학과활동',r'학과\s*활동'),
    ('자격증',r'자격증|SQLD|ADsP|SQL\s*개발자|데이터분석'),
    ('TOPCIT',r'TOPCIT|탑\s*싯'),
    ('비교과자율활동',r'자율\s*활동|공감|창의|글로벌'),
    ('대학공통',r'대학\s*공통|공통\s*필수'),
    ('예비창업설계',r'예비\s*창업\s*설계'),
    ('졸업인증 기준',r'졸업\s*요건|졸업\s*인증|졸업\s*기준|총점'),
]


def topics(question):
    found=[name for name,pattern in TOPICS if re.search(pattern,question,flags=re.IGNORECASE)]
    if len(found)>1 and '졸업인증 기준' in found: found.remove('졸업인증 기준')
    return found


def resolve_question(question,department,year,previous_question=None):
    question=re.sub(r'(?<!\d)(\d{2})\s*학번',lambda m:'20'+m[1]+'학번',question)
    if previous_question: previous_question=re.sub(r'(?<!\d)(\d{2})\s*학번',lambda m:'20'+m[1]+'학번',previous_question)
    if re.search(r'AI\s*[·ㆍ・.]?\s*빅\s*데이터\s*학과',question,flags=re.IGNORECASE):
        department='AI·빅데이터학과'
        question=re.sub(r'AI\s*[·ㆍ・.]?\s*빅\s*데이터\s*학과',department,question,flags=re.IGNORECASE)
    explicit=[name for name in {r['department'] for r in load_rules()['profiles']} if normalize(name) in normalize(question)]
    if len(explicit)==1: department=explicit[0]
    current_years=admission_years(question)
    if not topics(question) and previous_question and re.search(r'그럼|그거|그건|그것|몇\s*점|몇\s*번|몇\s*회|어떻게',question):
        previous_topics=topics(previous_question)
        if len(previous_topics)==1:
            previous_departments=[name for name in {r['department'] for r in load_rules()['profiles']} if normalize(name) in normalize(previous_question)]
            if not explicit and len(previous_departments)==1: department=previous_departments[0]
            question=previous_topics[0]+' '+question
            if not current_years:
                old_years=admission_years(previous_question)
                if len(set(old_years))==1: question=old_years[0]+'학번 '+question
    final_years=admission_years(question)
    if len(set(final_years))==1: year=int(final_years[0])
    return question,department,year


def short_rule_answer(question,rule,year):
    q=normalize(question).lower()
    items=common_items(year)+rule['items']
    if '코딩' in q:
        item=next((i for i in items if '코딩' in i['name']),None)
        if item:
            if 'minimum' in item:
                return f"코딩역량인증제는 **Level {item['minimum']} 이상**이 필요하며, 졸업인증에서 **{item['points']}점**으로 인정됩니다. 상세 시험 방식·일정은 이 PDF에 없습니다."
            return f"이 학번의 PDF에는 코딩역량인증제 {item['points']}점으로 표시되어 있습니다. 구체적인 인증 레벨은 해당 항목에 명시되어 있지 않아 확인이 필요합니다."
    if re.search(r'ai[·ㆍ&.]?sw|전공역량',q):
        item=next((i for i in items if '전공역량졸업인증' in i['name']),None)
        if item:
            minimum=f" 최소 시험점수 {item['minimum']} 이상이 필요합니다." if 'minimum' in item else ' 최소 시험점수·세부 인증 방식은 이 PDF에 명시되어 있지 않습니다.'
            return f"AI·SW전공역량 졸업인증제는 {item['points']}점 항목입니다."+minimum
    if '학과활동' in q:
        item=next((i for i in items if i['name']=='학과활동'),None)
        if item and item['kind']=='count':
            return f"학과활동은 **회당 {item['per']}점**, 필요한 점수는 **{item['points']}점**입니다. 따라서 해당 항목을 채우려면 {ceil(item['points']/item['per'])}회가 필요합니다. 다른 영역의 부족 점수를 대신 채우는 방식으로 계산하지 않습니다."
    if '자격증' in q:
        item=next((i for i in items if i['kind']=='achievement'),None)
        if item:
            return f"PDF 권장 자격증 취득은 **{item['points']}점**입니다. 권장 목록: {', '.join(item['certificates'])}. 경진대회 참가는 3~10점, 수상은 10~30점 범위이며 개별 대회의 공식 인정 점수를 확인해야 합니다."
    if any(word in q for word in ['자율활동','공감','창의','글로벌']):
        relevant=[i for i in items if i['name'].startswith('비교과자율활동')]
        if relevant:
            return '비교과 자율활동은 '+', '.join(f"{i['name']} {i['points']}점" for i in relevant)+'이 필요합니다. 각 영역을 따로 채워야 하며, 활동별 배점은 공식 학사시스템의 인정 내역을 확인해야 합니다.'
    if '예비창업설계' in q:
        item=next((i for i in rule['items'] if i['name']=='예비창업설계'),None)
        if item: return f"예비창업설계는 이 학번의 교과 졸업인증 항목으로 **{item['points']}점**입니다. 이것은 과목의 실제 학점과 다른 졸업인증 점수입니다."
    if '대학공통' in q:
        common=common_items(year)
        if common: return '대학공통 필요 점수는 **45점**입니다. '+', '.join(f"{i['name']} {i['points']}점" for i in common)+'. 항목별 공식 이수 여부를 확인하세요.'
    if '총점' in q or '졸업요건' in q or '졸업인증기준' in q:
        header=f"{rule['department']} {year}학번의 다면적 졸업인증 필요 점수는 **총 {sum(rule['required'].values())}점**입니다. "+', '.join(f'{area} {points}점' for area,points in rule['required'].items())+'. 총점뿐 아니라 필수 과목·활동과 영역별 조건을 모두 충족해야 합니다. 전체 졸업학점 규정은 이 PDF와 별도로 확인해야 합니다.'
        if '총점' in q and not re.search(r'요약|정리|필수|조건',q): return header
        lines=[header,'\n준비할 필수 조건:']
        for area,required in rule['required'].items():
            lines.append(f'\n[{area} · 필요 {required}점]')
            for item in (i for i in items if i['area']==area):
                kind=item['kind'];detail='학교 공식 이수·인증 완료 필요'
                if kind=='course': detail='해당 과목 이수 필요'
                elif kind=='choice': detail=', '.join(item['options'])+f" 중 {item.get('count',1)}개 이수"
                elif kind=='count': detail=f"회/학기당 {item['per']}점, {ceil(item['points']/item['per'])}회/학기 필요"
                elif kind=='threshold': detail=f"최소 인증 수준/시험점수 {item['minimum']} 이상"
                elif kind=='official_course': detail='해당 영역 과목 이수와 학사시스템의 공식 교과 영역 확인 필요'
                elif kind=='official_points': detail='해당 인재상 영역의 학교 공식 인정 점수로 확인; 다른 영역 점수로 대신 채우지 않음'
                elif kind=='achievement': detail='권장 자격증('+', '.join(item['certificates'])+') 취득 또는 경진대회 공식 인정 점수 확인; 참가·수상 중복 가산 안 함'
                elif kind=='unknown': detail='PDF만으로 세부 인정 조건을 확정할 수 없어 확인 필요'
                lines.append(f"- {item['name']}: {item['points']}점 · {detail}")
        lines.append('\n나의 충족 여부를 확인하려면 졸업요건 진단 메뉴에서 실제 수강 목록과 활동을 입력하세요. 이 설명만으로 개인 졸업을 확정하지 않습니다.')
        return '\n'.join(lines)
    named=[item for item in items if normalize(item['name']).lower() in q]
    if named:
        lines=[]
        for item in named:
            condition=''
            if item['kind']=='choice': condition=f" ({', '.join(item['options'])} 중 {item.get('count',1)}개 이수)"
            elif item['kind']=='count': condition=f" (회 또는 학기당 {item['per']}점)"
            elif item['kind']=='threshold': condition=f" (최소 기준 {item['minimum']} 이상)"
            elif item['kind'] in {'official_course','official_points','unknown'}: condition=' (공식 인정 내역·세부 기준 확인 필요)'
            lines.append(f"{item['name']}: {item['area']}의 필수 인증 항목, {item['points']}점{condition}.")
        return '\n'.join(lines)
    return None


def website_answer(question,department):
    if department!='AI·빅데이터학과': return None
    data=guide_data(); q=normalize(question)
    docs=guide_documents()
    if re.search('사무실|전화|연락처|학과위치|학과어디',q):
        return f"학과사무실은 {data['office']['location']}, 전화번호는 {data['office']['telephone']}입니다.\n출처: {data['homepage']} (확인일 {data['checked_at']})",docs[:1]
    if not re.search('교육과정|배우|과목|수업|학점',q): return None
    if re.search('몇점|점수|졸업인증|인증점수',q) and '학점' not in q: return None
    if re.search('필수|졸업인증|인정점수',q) and not re.search('교육과정|학점|학년',q): return None
    if re.search('졸업학점|총학점|전공필수학점|교양필수학점',q): return None
    grade=re.search(r'([1-4])학년',q)
    selected=[grade[1]] if grade else []
    specific=[]
    for level,rows in data['curriculum'].items():
        for course,credits in rows:
            if normalize(course) in q: specific.append((level,course,credits))
    if specific:
        lines=[f'{course}: 홈페이지 {level}학년 교육과정에 {credits}학점으로 안내되어 있습니다.' for level,course,credits in specific]
        used={int(level) for level,_,_ in specific}
    elif selected or any(word in q for word in ['교육과정','뭐배워','무엇을배워']):
        selected=selected or list(data['curriculum'])
        lines=[f"{level}학년: "+', '.join(f'{course}({credits}학점)' for course,credits in data['curriculum'][level]) for level in selected]
        used=set(map(int,selected))
    else: return None
    return '\n'.join(lines)+'\n'+data['scope_note']+f"\n출처: {data['curriculum_url']} (확인일 {data['checked_at']})",[d for d in docs if d.metadata['page'] in used]


def personal_answer(question,personal_result,previous_question=None):
    return diagnostic_answer(question,personal_result,previous_question)


def additional_policy_answer(question,documents,department,year,store,use_llm):
    """Let uploaded PDF evidence answer questions beyond the supplied draft.

    The caller provides the active corpus, so this cannot reach documents that
    were excluded by PDF-only mode. Reviewed website snapshots are not added
    graduation policies and must not trigger this path.
    """
    original=load_rules()['source']
    additional=[doc for doc in documents if doc.metadata.get('source')!=original and doc.metadata.get('kind')!='website']
    if not additional:
        return None
    text,hits=answer(question,additional,department,year,store,use_llm)
    if not hits:
        return None
    notice=('추가 등록 PDF에서 찾은 근거입니다. 문서의 적용 학과·학번과 공식 확정 여부를 확인하세요. '
            '이 답변은 자동 진단 규칙을 변경하거나 개인의 최종 졸업을 확정하지 않습니다.\n')
    return notice+text,hits


def answer_advisor(question,documents,department,year,store=None,use_llm=False,include_guide=False,previous_question=None,personal_result=None):
    if previous_question and not topics(question) and len(topics(previous_question))>1 and re.search(r'그럼|그거|그건|몇\s*점|몇\s*회',question) and not personal_intent(question,previous_question,bool(personal_result)):
        return '앞서 여러 항목을 이야기했습니다. 어떤 항목의 조건이나 점수를 뜻하는지 알려주세요: '+', '.join(topics(previous_question)),[]
    question,department,year=resolve_question(question,department,year,previous_question)
    explicit_departments=[name for name in {r['department'] for r in load_rules()['profiles']} if normalize(name) in normalize(question)]
    if len(explicit_departments)>1:
        return '학과를 하나씩 선택하여 질문해 주세요.',[]
    # Explicit conjunctions are separate requests: requiring every subject to
    # occur on one page otherwise rejects valid questions spanning two PDFs.
    # Keep unknown clauses visible rather than silently dropping their subject.
    expanded=re.sub(r'(총점|조건|기준|점수|활동|확인코드|학점|요건)(?:과|와)(?=\s)',r'\1 그리고 ',question)
    parts=[re.sub(r'(?<![가-힣])(?:함께|같이)(?![가-힣])',' ',part).strip()
           for part in re.split(r'\s+(?:그리고|및|또한)\s+',expanded)]
    if 1<len(parts)<=3 and all(parts) and len(set(admission_years(question)))<=1:
        sections=[];combined=[];seen=set()
        for n,part in enumerate(parts,1):
            response,hits=answer_advisor(part,documents,department,year,store,use_llm,include_guide,None,personal_result)
            sections.append(f'### 요청 {n}: {part}\n'+response.partition('\n\n근거 원문:\n')[0])
            for hit in hits:
                key=(hit.metadata.get('source'),hit.metadata.get('page'),hit.page_content)
                if key not in seen:combined.append(hit);seen.add(key)
        evidence='\n\n'.join(f"[{n}] {hit.metadata['source']} p.{hit.metadata['page']}\n{hit.page_content}" for n,hit in enumerate(combined,1))
        return '\n\n'.join(sections)+('\n\n근거 원문:\n'+evidence if evidence else ''),combined
    # Academic credits must never be manufactured from certification points.
    if re.search(r'졸업\s*학점|총\s*학점|졸업.*학점|학점.*졸업',question):
        additional=additional_policy_answer(question,documents,department,year,store,use_llm)
        if additional is not None:
            return additional
        return '제공된 자료에는 적용 학번의 전체 졸업학점 기준이 없습니다. 졸업인증 점수와 졸업학점은 다릅니다. 학번별 교육과정 이수기준표 또는 학과의 공식 졸업학점 규정이 필요합니다.',[]
    if personal_result and (personal_result.get('year')!=year or personal_result.get('department')!=department): personal_result=None
    personal=personal_answer(question,personal_result,previous_question)
    if personal is not None: return personal
    rule=get_rule(department,year)
    if rule and re.search('필수|반드시',question):
        named=[course for rows in guide_data()['curriculum'].values() for course,_ in rows if normalize(course) in normalize(question)]
        named=sorted(set(named),key=len,reverse=True)
        if named and all(normalize(named[0])!=normalize(i['name']) for i in rule['items'] if i['kind']=='course') and any(d.metadata['source']==rule['source'] and d.metadata['page']==rule['page'] for d in documents):
            additional=additional_policy_answer(question,documents,department,year,store,use_llm)
            if additional is not None:
                return additional
            from .rag_chain import scoped_original
            target=[i for i in rule['items'] if i['area']=='교과']
            info=', '.join(f"{i['name']} {i['points']}점" for i in target)
            text=f"{named[0]}은 이 학번의 제공 PDF 교과 지정 목록에 명시되어 있지 않습니다. PDF에 표시된 교과 조건은 {info}입니다. 이 과목이 전체 교육과정에서도 필수가 아니라는 뜻은 아니며, 학번별 필수 교과목표를 별도로 확인해야 합니다.\n근거: {rule['source']} p.{rule['page']}"
            return text,[scoped_original(rule,year)]
    if include_guide:
        web=website_answer(question,department)
        if web is not None:
            if rule and '학점' in question:
                course=next((i for i in rule['items'] if i['kind']=='course' and normalize(i['name']) in normalize(question)),None)
                if course and any(d.metadata['source']==rule['source'] for d in documents):
                    web_text,web_hits=web
                    from .rag_chain import scoped_original
                    web_text+=f"\n한편 제공 PDF에서 {course['name']}은 졸업인증 {course['points']}점 항목입니다. 실제 교과 학점과 졸업인증 점수는 단위가 다릅니다. 해당 학번의 실제 취득 학점은 성적표로 확인하세요.\nPDF 근거: {rule['source']} p.{rule['page']}"
                    return web_text,web_hits+[scoped_original(rule,year)]
            return web
    # Website statements are handled by the explicit reviewed-guide path above.
    # A website disclaimer mentioning certification is not evidence for PDF point questions.
    retrieval_documents=[doc for doc in documents if doc.metadata.get('kind')!='website']
    text,hits=answer(question,retrieval_documents,department,year,store,use_llm)
    original=get_rule(department,year)
    detail_request=bool(re.search(r'시험|방식|어디|언제|신청|방법|일정|응시료|난이도',question))
    known_topics=topics(question)
    if not hits and detail_request and len(known_topics)==1 and not re.search(r'우주|기숙사|식당|날씨|계좌',question):
        partial,partial_hits=answer(known_topics[0],documents,department,year,store,False)
        if partial_hits and original:
            short=short_rule_answer(known_topics[0],original,year)
            if short:
                reference=f"{original['source']} p.{original['page']}"
                return '질문하신 세부 방법·일정은 제공 자료만으로 확인할 수 없습니다. 확인 가능한 기준은 다음과 같습니다.\n'+short+'\n근거: '+reference,partial_hits
    if hits and original and not use_llm and all(doc.metadata['source']==original['source'] for doc in hits):
        resolved_years=admission_years(question)
        actual_year=int(resolved_years[0]) if len(set(resolved_years))==1 else year
        actual_rule=get_rule(department,actual_year)
        if actual_rule and len(set(resolved_years))<=1:
            asked_topics=list(dict.fromkeys(topics(question)+[i['name'] for i in common_items(actual_year)+actual_rule['items'] if normalize(i['name']).lower() in normalize(question).lower()]))
            if len(asked_topics)>1:
                parts=[short_rule_answer(topic,actual_rule,actual_year) for topic in asked_topics]
                short='\n'.join(dict.fromkeys(part for part in parts if part))
            else: short=short_rule_answer(asked_topics[0] if asked_topics else normalize_question(question),actual_rule,actual_year)
            if short:
                citation=f"{actual_rule['source']} p.{actual_rule['page']}"
                return f"{department} · {actual_year}학번\n{short}\n근거: {citation}\n\n근거 원문:\n"+'\n\n'.join(doc.page_content for doc in hits),hits
    if not hits and use_llm:
        from .freeform import freeform_answer
        free=freeform_answer(question,retrieval_documents,department,year)
        if free is not None: return free
    return text,hits
