"""Personal advice from the deterministic diagnosis, without LLM scoring."""
from copy import deepcopy
import re
from .graduation_rules import get_rule,common_items
from .graduation_checker import check
from .utils import normalize
from .i18n import item_label,tr


def say(lang,ko,en,zh,ja):
    return {'ko':ko,'en':en,'zh':zh,'ja':ja}.get(lang,ko)


def personal_intent(question,previous_question=None,has_result=False):
    q=normalize(question).lower()
    if re.search(r'졸업학점|총학점|학점.*졸업|졸업.*학점',q): return None
    if re.search(r'졸업(?:하려면|할려면)',q) and not re.search(r'더|남|부족|내(?:점수|진단|결과)',q): return None
    if previous_question:
        previous=personal_intent(previous_question,has_result=has_result)
        short=re.sub(r'^20\d{2}학번','',q)
        # advisor.resolve_question may prefix the inherited general topic.
        if previous=='certificate': short=re.sub(r'^자격증','',short)
        short=re.sub(r'^(?:그럼|그러면|그래서)','',short).rstrip('?.!')
        if previous and re.fullmatch(r'(?:몇점(?:이야|이예요|이부족해)?|얼마나|얼마나부족해)',short):
            return previous if previous in {'certificate','largest'} else 'points'
        if previous in {'completed','unrecognized'} and short in {'어떤과목','어느과목','그과목'}:
            return previous
    personal=bool(re.search(r'내(?:진단|점수|결과|부족|가이수|이수|수강)|나(?:는|의|도)?졸업|내가졸업|내가.*(?:부족|이수|수강)|얼마나남|뭐가부족|뭘더해야|이미이수|내활동|필수활동.*(?:하지않았|안했)|현재상태',q))
    relative=bool(re.search(r'부족|우선|먼저|무엇부터|뭐부터|이미.*(?:이수|수강)|가장.*영역|자격증.*(?:도움|취득|따면|충족|채울)|도움.*자격증|하지않|안했|안한|미이수|미완료|현재상태|과목.*(?:인정되지|미인정)',q))
    simplify=bool(re.search(r'쉽게|쉬운말|간단히.*설명',q))
    generic_simple=bool(re.fullmatch(r'(?:그럼|그러면|좀)?(?:쉽게|쉬운말로|간단히)(?:좀)?설명(?:해줘|해주세요|해|해줄래|해요)?[?!.]*',q))
    if simplify and (personal or generic_simple and ((not previous_question and has_result) or previous_question and personal_intent(previous_question,has_result=has_result))): return 'simple'
    if not personal and not (has_result and relative): return None
    if re.search(r'자격증|sqld|adsp|sql개발자|데이터분석준전문가',q) and re.search(r'도움|따면|취득|채우|채울|부족|인정',q): return 'certificate'
    if re.search(r'과목.*(?:인정되지|미인정|인정안|불인정)|(?:인정되지|미인정).*과목',q): return 'unrecognized'
    if re.search(r'이미.*(?:이수|수강)|이수한과목|수강한과목|내이수|내수강|내가이수',q): return 'completed'
    if re.search(r'가장|제일',q) and re.search(r'영역|부족',q): return 'largest'
    if re.search(r'부족.*점수|점수.*부족|몇점.*부족|부족.*몇점|몇점더|얼마나부족',q): return 'points'
    if re.search(r'우선|먼저|순서|무엇부터|뭐부터|현재상태.*(?:충족|방법)',q): return 'priority'
    if re.search(r'하지않|안했|안한|미이수|미완료',q): return 'uncompleted'
    if re.search(r'부족|더해야|얼마나남|남은',q): return 'missing'
    return 'overview'


def _actions(result,lang,limit=None):
    rows=[row for row in result.get('items',[]) if row['status']!='충족']
    # This is an explicit planning order, not an estimate of time or difficulty.
    rows.sort(key=lambda row:(row['area']!='교과',row['status']!='미충족',-row.get('shortage',0)))
    lines=[]
    for row in rows[:limit]:
        name=item_label(row['name'],lang)
        if row['status']=='확인 필요':
            detail=say(lang,'공식 이수·인정 내역 확인 필요','verify the official completion/recognition record','需确认正式修读或认定记录','正式な修得・認定記録の確認が必要')
        elif row.get('remaining_count') is not None:
            n=row['remaining_count'];detail=say(lang,f"{row.get('shortage',0):g}점 부족, {n}회/학기 추가 필요",f"{row.get('shortage',0):g} points short; {n} more participation(s)/semester(s)",f"差{row.get('shortage',0):g}分，还需{n}次／学期",f"{row.get('shortage',0):g}点不足、あと{n}回・学期が必要")
        else:
            n=row.get('shortage',0);detail=say(lang,f'{n:g}점 부족',f'{n:g} points short',f'差{n:g}分',f'{n:g}点不足')
        lines.append(f'- {name}: {detail}')
    return lines


def _certificate_advice(question,result,rule,lang):
    item=next((i for i in rule['items'] if i['kind']=='achievement'),None) if rule else None
    if not item:
        return say(lang,'이 학과·학번의 검수된 진단 규칙에는 자격증 점수 계산 경로가 없습니다. 임의로 가산하지 않습니다.','This cohort’s reviewed diagnosis has no certificate scoring path; no points are added.','该入学年份的已审核诊断规则没有资格证书计分路径，不会自行加分。','この入学年度の確認済み診断ルールには資格の加点経路がなく、任意に加点しません。')
    q=normalize(question).lower()
    cert=next((c for c in item['certificates'] if normalize(c).lower() in q),None)
    if cert is None:
        if 'sqld' in q: cert='SQL개발자'
        elif 'adsp' in q: cert='데이터분석준전문가'
    qualifier=re.search(r'([가-힣A-Za-z0-9]+)\s*자격증',question)
    if cert is None and qualifier and qualifier[1] not in {'권장','추천','어떤','내','그','이'}:
        return say(lang,'질문하신 자격증은 PDF 권장 목록에서 확인하지 못했습니다. 임의로 점수를 주지 않습니다. 권장 목록: ','The named certificate was not identified in the PDF list; no points are assumed. Recommended list: ','未在PDF推荐列表中确认该证书，不推定加分。推荐列表：','質問の資格はPDFの推奨一覧で確認できず、加点を推定しません。推奨一覧：')+', '.join(item['certificates'])
    cert=cert or item['certificates'][0]
    snapshot=result.get('input_snapshot')
    if not snapshot:
        return say(lang,'이전 진단에 원래 입력 스냅샷이 없어 자격증 취득 전후를 다시 계산할 수 없습니다. 진단을 다시 실행해 주세요.','This older diagnosis has no input snapshot for a certificate comparison. Run the check again.','旧诊断没有输入快照，无法比较取得证书前后的结果，请重新诊断。','以前の診断には入力スナップショットがないため資格取得前後を比較できません。再診断してください。')
    changed=deepcopy(snapshot);record=changed['evidence'].setdefault(item['name'],{})
    record['certificates']=list(dict.fromkeys(list(record.get('certificates',[]))+[cert]))
    predicted=check(**changed)
    before=next((r for r in result.get('items',[]) if r['name']==item['name']),{})
    after=next(r for r in predicted['items'] if r['name']==item['name'])
    gain=predicted['total_earned']-result.get('total_earned',0)
    return say(lang,
        f"가정 계산: {cert} 취득을 입력하면 자격증/경진대회 항목은 {before.get('earned',0):g} → {after['earned']:g}점, 인증 총점은 {result.get('total_earned',0):g} → {predicted['total_earned']:g}점(변화 {gain:+g}점)입니다. 기존 점수가 상한에 도달했다면 추가점수는 없습니다. 실제 취득을 확인한 결과가 아니며, 다른 영역의 부족을 대신 채우지 않습니다.",
        f"What-if only: entering {cert} changes the certificate/competition item from {before.get('earned',0):g} to {after['earned']:g} points and the certification total from {result.get('total_earned',0):g} to {predicted['total_earned']:g} ({gain:+g}). No extra points are added past the cap. This does not verify acquisition or offset shortages in other categories.",
        f"仅为假设计算：输入取得{cert}后，资格／竞赛项目由{before.get('earned',0):g}变为{after['earned']:g}分，认证总分由{result.get('total_earned',0):g}变为{predicted['total_earned']:g}分（变化{gain:+g}分）。达到上限后不再加分。这不代表已核实取得证书，也不能抵扣其他领域不足。",
        f"仮定の計算です。{cert}の取得を入力すると資格・競技会項目は{before.get('earned',0):g}→{after['earned']:g}点、認証合計は{result.get('total_earned',0):g}→{predicted['total_earned']:g}点（変化{gain:+g}点）です。上限を超えて加点しません。実際の取得確認や他分野の不足補填ではありません。")


def _unrecognized_courses(result,rule,lang):
    snapshot=result.get('input_snapshot')
    if not snapshot or not rule:
        return [say(lang,'이전 진단에 이수 과목 입력 상세가 없습니다. 진단을 다시 실행해 주세요.','This older diagnosis has no entered course details. Run the check again.','旧诊断没有已修课程输入详情，请重新诊断。','以前の診断には修得科目の入力詳細がありません。再診断してください。')]
    rows={row['name']:row for row in result.get('items',[])}
    records=snapshot.get('evidence',{});lines=[]
    courses={normalize(c):c.strip() for c in snapshot.get('courses',[]) if normalize(c)}
    for canonical,course in courses.items():
        candidates=[]
        for item in common_items(result['year'])+rule['items']:
            matched=(item['kind']=='course' and canonical==normalize(item['name']))
            matched|=item['area']=='대학공통' and item['kind']=='check' and canonical==normalize(item['name'])
            matched|=item['kind']=='choice' and canonical in {normalize(name) for name in item['options']}
            matched|=item['kind']=='official_course' and canonical==normalize(records.get(item['name'],{}).get('course',''))
            if matched: candidates.append(item)
        if any(rows.get(item['name'],{}).get('earned',0)>=item['points'] for item in candidates):
            continue
        if any(item['area']=='대학공통' for item in candidates):
            reason=say(lang,'과목명은 대학공통 항목과 일치하지만 공식 이수·인증 확인이 입력되지 않았습니다. 수강 목록만으로 자동 체크하지 않습니다.','the name matches a university-common item, but official completion/certification has not been confirmed; the course list does not automatically check it off.','课程名与大学共同项目一致，但尚未输入正式修读或认证确认，不能仅凭课程列表自动勾选。','科目名は大学共通項目と一致しますが、正式な修得・認証確認が未入力です。履修一覧だけで自動確認はしません。')
        elif any(item['kind']=='official_course' for item in candidates):
            reason=say(lang,'공식 교과 영역의 인정이 미확인 또는 중복 배정으로 제한되었습니다.','official category recognition is unconfirmed or limited by duplicate assignment.','正式课程领域认定未确认，或受重复分配限制。','正式な教科分野の認定が未確認、または重複割当の制限があります。')
        elif any(item['kind']=='choice' for item in candidates):
            reason=say(lang,'선택 필수 목록에는 있으나 필요한 조합 전체가 아직 충족되지 않았습니다. 과목 자체의 불인정을 뜻하지 않습니다.','listed as a choice, but the full required combination is not met; the course itself is not being declared invalid.','属于选择必修列表，但所需组合尚未全部满足，并非认定课程本身无效。','選択必修の一覧にはありますが、必要な組み合わせ全体が未充足です。科目自体の不認定ではありません。')
        elif any(canonical in normalize(row.get('detail','')) and row.get('status')=='확인 필요' for row in result.get('items',[])):
            reason=say(lang,'유사 과목명으로 확인되어 동일 과목인지 검토가 필요합니다. 자동 인정하지 않았습니다.','a similar course name requires an equivalence check; it was not automatically accepted.','课程名称相似，需确认是否为同一课程，未自动认定。','類似する科目名のため同一科目か確認が必要です。自動認定していません。')
        else:
            reason=say(lang,'이 PDF의 해당 학번 인증 필수 교과·확인된 영역과 매칭되지 않았습니다.','not matched to this PDF’s certification courses or confirmed categories for the selected cohort.','未匹配到本PDF中该入学年份的认证必修课程或已确认领域。','このPDFの該当入学年度の認証必修科目・確認済み分野に一致しません。')
        lines.append(f'- {course}: {reason}')
    if not lines:
        lines.append(say(lang,'저장된 이수 입력 목록에서 별도로 확인할 미매칭 과목은 없습니다.','No unmatched course was found in the saved completed-course input.','保存的已修课程输入中没有发现需另行核对的未匹配课程。','保存された修得済み入力一覧に、別途確認する未一致科目はありません。'))
    lines.append(say(lang,'이는 이 PDF의 졸업인증 점수 반영 범위이며, 과목의 취득 학점이나 전체 졸업학점 불인정을 뜻하지 않습니다. 원본 파일에서 미이수·낙제로 제외된 행은 이 저장된 이수 목록에 없으므로 여기서 확인하지 않습니다.','This describes this PDF’s certification scoring only, not invalid academic credits. Rows excluded as incomplete or failed are absent from the saved completed-course list and cannot be reviewed here.','这仅说明本PDF认证计分范围，不代表课程学分或整体毕业学分不被认可。原文件中因未修完或不及格而排除的行不在此已修列表中，无法在这里查看。','このPDFの認証点数への反映範囲であり、修得単位や卒業単位の不認定ではありません。元ファイルで未修得・不合格として除外された行は保存済み修得一覧にないため、ここでは確認できません。'))
    return lines


def diagnostic_answer(question,result,previous_question=None,lang='ko'):
    intent=personal_intent(question,previous_question,has_result=bool(result))
    if intent is None: return None
    if not result:
        return say(lang,'아직 이 학과·학번의 개인 진단 내역이 없습니다. 졸업요건 진단 메뉴에서 수강 목록과 활동을 입력하고 진단을 실행해 주세요.','There is no personal diagnosis for this department/cohort. Enter courses and activities and run the check first.','该院系及入学年份尚无个人诊断，请先输入课程及活动并进行诊断。','この学科・入学年度の個人診断はありません。先に履修科目と活動を入力して診断してください。'),[]
    if result.get('_stale'):
        return say(lang,'입력이나 기준이 바뀌어 저장된 진단 결과가 최신 상태가 아닙니다. 졸업요건 진단에서 다시 계산해 주세요.','Inputs or rules changed; the saved diagnosis is out of date. Run the check again.','输入或基准已变更，保存的诊断结果已过期，请重新诊断。','入力や基準が変わり、保存済みの診断結果は最新ではありません。再診断してください。'),[]
    rule=get_rule(result.get('department'),result.get('year')) if result.get('department') and result.get('year') else None
    current=result.get('total_earned',0);total=result.get('total_required',0)
    status=tr(result.get('status','확인 필요'),lang)
    header=say(lang,f"입력 내역에 따른 다면적 졸업인증 판정은 **{status}**입니다. 확인된 점수는 {current:g} / {total:g}점입니다.",f'Your input-based certification result is **{status}**, {current:g} / {total:g} points.',f'根据输入记录的认证结果为**{status}**，已确认{current:g} / {total:g}分。',f'入力記録に基づく認証結果は**{status}**、確認済み点数は{current:g} / {total:g}点です。')
    lines=[header]
    if result.get('synthetic'):
        lines.insert(0,say(lang,'**가상 시연 입력 결과**입니다. 실제 개인의 이수 기록이 아닙니다.','**Synthetic demonstration result** — not a real person’s completion record.','这是**虚拟演示输入结果**，并非真实个人修读记录。','**架空のデモ入力による結果**で、実際の個人の修得記録ではありません。'))
    if intent=='certificate':
        numeric_followup=bool(re.fullmatch(r'(?:20\d{2}학번)?(?:자격증)?(?:그럼|그러면|그래서)?(?:몇점(?:이야|이예요|이부족해)?|얼마나|얼마나부족해)[?.!]*',normalize(question)))
        certificate_question=(previous_question+' '+question) if previous_question and numeric_followup and personal_intent(previous_question,has_result=True)=='certificate' else question
        lines.append(_certificate_advice(certificate_question,result,rule,lang))
    elif intent=='points':
        gap=max(0,total-current)
        lines.append(say(lang,f'입력·인정된 점수 기준으로 총 {gap:g}점이 부족합니다. 영역별 부족 점수와 필수 항목을 각각 확인해야 하며, 미확인 이수 내역이 포함되었을 수 있습니다.',f'The recognized input is {gap:g} points below the required total. Check every category and mandatory item separately; unconfirmed records may be included.',f'按输入及已认定分数计算，总计差{gap:g}分。仍需逐一核对各领域及必修项目，可能包括尚未确认的记录。',f'入力・認定済み点数では合計{gap:g}点不足しています。各分野と必須項目を個別に確認してください。未確認の記録を含む場合があります。'))
    elif intent=='unrecognized': lines.extend(_unrecognized_courses(result,rule,lang))
    elif intent=='completed':
        snapshot=result.get('input_snapshot')
        if not snapshot: lines.append(say(lang,'이전 결과에는 과목 입력 상세가 없습니다. 진단을 다시 실행하면 입력한 이수 과목을 확인할 수 있습니다.','This older result has no course details. Run the check again to review entered courses.','旧结果没有课程输入详情，请重新诊断后查看。','以前の結果には科目の入力詳細がありません。再診断すると確認できます。'))
        else:
            courses=list(dict.fromkeys(c.strip() for c in snapshot['courses'] if c.strip()))
            lines.append(say(lang,'본인이 이수했다고 입력한 과목: ','Courses you entered as completed: ','您输入为已修完的课程：','修得済みとして入力した科目：')+(', '.join(courses) if courses else say(lang,'없음','none','无','なし')))
            lines.append(say(lang,'이 목록은 입력·업로드 기준이며 학교의 공식 성적 조회 결과가 아닙니다.','This list comes from your inputs/uploads, not an official transcript lookup.','此列表来自输入或上传，并非学校正式成绩查询。','入力・アップロードに基づく一覧で、大学の正式な成績照会ではありません。'))
    elif intent=='largest':
        areas=result.get('areas',[]);maximum=max((a.get('shortage',0) for a in areas),default=0)
        if not areas:
            lines.append(say(lang,'이전 진단에는 영역별 상세 내역이 없습니다. 다시 진단해 주세요.','This older diagnosis has no category details. Run the check again.','旧诊断没有领域详情，请重新诊断。','以前の診断には分野別の詳細がありません。再診断してください。'))
        elif maximum:
            names=', '.join(item_label(a['area'],lang) for a in areas if a.get('shortage',0)==maximum)
            lines.append(say(lang,f'부족 점수 기준으로 가장 큰 영역: {names} ({maximum:g}점). 공식 인정 미확인 항목도 포함될 수 있습니다.',f'Largest shortage by points: {names} ({maximum:g} points). This may include unconfirmed official recognition.',f'按缺少分数最多的领域：{names}（{maximum:g}分），可能包括尚未确认的正式认定项目。',f'不足点数が最も大きい分野：{names}（{maximum:g}点）。正式認定が未確認の項目を含む場合があります。'))
        else: lines.append(say(lang,'영역별 부족 점수는 0점입니다. 확인 필요 표시가 있다면 공식 기준을 확인하세요.','Every category has zero point shortage. Review any remaining uncertain conditions.','各领域缺少分数均为0，如仍有待确认项目，请核实正式标准。','各分野の不足点数は0点です。要確認の条件が残っていれば確認してください。'))
    else:
        actions=_actions(result,lang,3 if intent=='simple' else None)
        if intent=='uncompleted': lines.append(say(lang,'아래는 입력상 미충족 또는 인정 미확인인 항목입니다. 실제로 활동을 하지 않았다고 단정하지 않습니다.','The following items are unmet or unconfirmed in the entered record; this does not prove that you did not participate.','以下为输入记录中未满足或尚未确认的项目，并不证明您实际没有参加活动。','次の項目は入力上の未充足または認定未確認です。実際に活動をしなかったと断定するものではありません。'))
        if intent=='priority': lines.append(say(lang,'준비 순서: 필수 교과 → 확정된 미충족 항목 → 공식 인정 확인 항목입니다. 소요 시간이나 난이도를 추정한 순위는 아닙니다.','Planning order: required courses, definite unmet items, then official-recognition checks. This is not a ranking by estimated time or difficulty.','准备顺序：必修课程→明确未满足项目→正式认定确认项目，并非按耗时或难度推测的排名。','準備順序：必修科目→確定した未充足項目→正式認定の確認項目です。所要時間や難易度の推定順位ではありません。'))
        if intent=='simple': lines.append(say(lang,'쉽게 말하면, 아래 조건을 채우거나 공식 인정 여부를 확인하면 됩니다. 총점만 채우면 끝나는 제도는 아닙니다.','In simple terms, complete or verify the conditions below. Reaching the total alone is not enough.','简单来说，需要补足或确认以下条件，仅达到总分并不足够。','簡単に言えば、次の条件を満たすか正式認定を確認します。合計点だけを満たしても完了ではありません。'))
        if not result.get('items'):
            lines.append(say(lang,'이전 진단에는 항목별 상세 내역이 없습니다. 준비할 항목을 확인하려면 다시 진단해 주세요.','This older result has no item details. Run the check again to review next steps.','旧诊断没有逐项详情，请重新诊断以查看下一步。','以前の診断には項目別の詳細がありません。次の準備を確認するには再診断してください。'))
        else:
            lines.extend(actions or [say(lang,'입력 기준 부족한 필수 항목은 없습니다.','No required item is missing based on the entered record.','根据输入记录，没有缺少的必修项目。','入力記録上、不足している必須項目はありません。')])
            omitted=sum(row['status']!='충족' for row in result['items'])-len(actions)
            if intent=='simple' and omitted>0:
                lines.append(say(lang,f'이외에도 {omitted}개 항목이 남아 있습니다. 진단 결과에서 전체 목록을 확인하세요.',f'{omitted} more item(s) remain. Check the full list in the diagnostic results.',f'此外还有{omitted}个项目未完成，请在诊断结果中查看完整列表。',f'このほかに{omitted}項目が残っています。診断結果で全一覧を確認してください。'))
    lines.append(say(lang,'이것은 본인이 입력한 내역에 따른 계산이며, 전체 졸업 확정은 공식 학사시스템에서 확인해야 합니다.','This uses your entered record; confirm final graduation eligibility in the official university system.','结果基于本人输入，最终毕业资格须在学校正式教务系统确认。','本人が入力した記録に基づきます。最終的な卒業可否は大学の正式な学務システムで確認してください。'))
    hits=[]
    if rule and result.get('source')==rule['source'] and result.get('page')==rule['page']:
        from .rag_chain import scoped_original
        hits=[scoped_original(rule,result['year'])]
        lines.append(say(lang,'근거: ','Source: ','依据：','出典：')+f"{rule['source']} p.{rule['page']}")
    return '\n'.join(lines),hits
