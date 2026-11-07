"""Presentation helpers and explicitly synthetic, session-only demonstration inputs."""
from html import escape
from math import ceil
from .graduation_rules import common_items, get_rule
from .i18n import tr


def show_steps(ui, lang, current):
    labels=['학과·학번', '수강 과목', '활동·인정 정보', '진단 실행', '결과·상담']
    cells=[]
    for n,label in enumerate(labels,1):
        active=n==current
        cells.append(f'<span style="flex:1;min-width:110px;padding:10px 12px;border-radius:9px;'
                     f'background:{"#087f78" if active else "#edf3ed"};color:{"white" if active else "#334e61"};'
                     f'font-size:13px;font-weight:650"'+(' aria-current="step"' if active else '')+
                     f'>{n}. {escape(tr(label,lang))}</span>')
    ui.markdown('<nav aria-label="'+escape(tr('진단 진행 단계',lang))+'" style="display:flex;gap:7px;flex-wrap:wrap;margin:12px 0 22px">'+''.join(cells)+'</nav>',unsafe_allow_html=True)


def fill_demo_inputs(state, department, year):
    """Used only by an explicit evaluator action; never reads actual student data."""
    rule=get_rule(department,year)
    if not rule: return
    scope=f'{department}_{year}'
    courses=[]
    for item in common_items(year)+rule['items']:
        name,kind=item['name'],item['kind'];key=scope+name
        if kind=='course': courses.append(name)
        elif kind=='choice': courses+=item['options'][:item.get('count',1)]
        elif kind=='official_course':
            state[key+'course']='가상 시연 국제사회언어 과목'
            state[key+'confirmed']=True
        elif kind=='official_points':
            state[key+'points']=max(0,item['points']-(2 if '글로벌' in name else 0))
            state[key+'confirmed']=True
        elif kind=='achievement':
            state[key+'certs']=item['certificates'][:1]
            for category in ['participation','award']:
                state[key+category]=0;state[key+category+'confirmed']=False
        elif kind=='count': state[key]=ceil(item['points']/item['per'])
        elif kind=='threshold': state[key]=item['minimum']
        elif kind=='check': state[key]=True
    state[scope+'courses']=courses;state[scope+'manual']='';state[scope+'complete']=True
    state.setdefault('saved_courses',{})[scope]=[]
    state['synthetic_input_scope']=scope
    state['main_menu']='졸업요건 진단'


def result_csv(result):
    import csv,io
    stream=io.StringIO(newline='');writer=csv.writer(stream)
    writer.writerow(['학과','입학연도','항목','영역','필요점수','인정점수','상태','부족조건'])
    for item in result.get('items',[]):
        writer.writerow([result.get('department'),result.get('year'),item['name'],item['area'],item['required'],item['earned'],item['status'],item.get('action') or item.get('detail','')])
    return ('\ufeff'+stream.getvalue()).encode('utf8')
