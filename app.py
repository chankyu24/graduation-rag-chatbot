import hashlib,json,os
from pathlib import Path
import streamlit as raw_st
from src.i18n import LocalizedUI,LANGUAGES,tr,table
from src.account_ui import require_login,account_sidebar,restore_draft,remember_draft,persist
from src.multilingual import answer_in_language
from src.evaluation import CASES,evaluate_case
from src.department_guide import guide_documents
from dotenv import load_dotenv
from src.utils import ROOT,read_course_file
from src.diagnostic_state import input_signature,stamp_result,is_stale
from datetime import datetime,timezone,timedelta
from src.pdf_loader import load_directory,load_pdf
from src.document_manager import save_pdf,private_document_directory,load_corpus
from src.graduation_rules import load_rules,get_rule,common_items
from src.graduation_checker import check
from src.rag_chain import answer
from src.text_splitter import split_documents
from src.vector_store import fingerprint,build_store,load_store
load_dotenv(ROOT/'.env')
raw_st.set_page_config(page_title='순천향대 졸업 길잡이',page_icon='🎓',layout='wide')
lang=raw_st.selectbox('언어 / Language',list(LANGUAGES),format_func=lambda code:LANGUAGES[code],key='ui_language')
st=LocalizedUI(raw_st,lang)
st.markdown('<style>.stApp{background:#f5f7fc} h1,h2,h3{color:#183769} div.stButton>button{border-radius:10px} [data-testid=stForm]{background:white;border-radius:16px;padding:24px} [data-testid=stMetric]{background:white;border-radius:12px;padding:14px}</style>',unsafe_allow_html=True)
st.title('🎓 순천향대 졸업 길잡이')
st.caption('PDF 근거로 알아보고, 영역별 조건으로 준비하는 나의 졸업인증')
user=require_login(st,lang)
account_sidebar(st,user)
if lang!='ko': st.caption('원문 과목명과 근거는 한국어로 함께 표시됩니다. 자유로운 답변 번역은 API 연결이 필요할 수 있습니다.')
DATA=ROOT/'data'
UPLOAD_DATA=Path(st.session_state.review_directory.name) if user.get('guest') else private_document_directory(user['account_id'])
profiles=load_rules()['profiles']; departments=list(dict.fromkeys(r['department'] for r in profiles))
menus=['학과·졸업 통합 상담','PDF 단독 RAG','다중 문서 RAG','졸업요건 진단','진단 결과','학과 안내']
if user['role']=='evaluator': menus.insert(0,'교수용 과제 평가')
menu=st.sidebar.radio('메뉴',menus,key='main_menu')
st.sidebar.selectbox('대학교',['순천향대학교'])
st.sidebar.caption('교육과정: 제공된 2026년도 학과기준 시안')
department=st.sidebar.selectbox('학과',departments,index=departments.index(user['department']))
year=st.sidebar.number_input('입학연도 (학번 앞 4자리)' if user['role']=='student' else '검토할 입학연도',2000,2100,user['admission_year'])
st.sidebar.caption('인증점수 ≠ 교과 이수학점')
original_pdf=DATA/load_rules()['source']
if original_pdf.is_file():
 st.sidebar.download_button('제공 PDF 다운로드',original_pdf.read_bytes(),original_pdf.name,mime='application/pdf',key='download_original_pdf')
mode='제공 PDF 한 개' if menu=='PDF 단독 RAG' else '학과·졸업 통합' if menu=='학과·졸업 통합 상담' else '여러 PDF 통합'
st.sidebar.caption('검색 범위: '+mode)
vector=st.sidebar.toggle('다국어 임베딩 + FAISS',value=os.getenv('RAG_VECTOR_DEFAULT','0')=='1',help='처음에는 무료 모델 다운로드가 필요합니다. 끄면 인터넷 없는 원문 검색을 사용합니다.')
llm=st.sidebar.toggle('LLM 답변 사용',value=False)
@st.cache_data
def read_all(sig,private_path,include_uploads): return load_corpus(DATA,private_path,include_uploads)
include_uploads=mode!='제공 PDF 한 개'
sig=fingerprint(DATA)+(fingerprint(UPLOAD_DATA)+hashlib.sha256(str(UPLOAD_DATA).encode()).hexdigest() if include_uploads else '')
if user.get('guest'):
 # Guest documents live only in this session, never in Streamlit's global data cache.
 if st.session_state.get('guest_corpus_signature')!=sig:
  st.session_state.guest_corpus=load_corpus(DATA,str(UPLOAD_DATA),include_uploads)
  st.session_state.guest_corpus_signature=sig
 docs,errors=st.session_state.guest_corpus
else:
 docs,errors=read_all(sig,str(UPLOAD_DATA),include_uploads)
docs=list(docs)  # Guide references must not accumulate in the session's cached PDF list.
criteria_sig=hashlib.sha256((ROOT/'rules/graduation_rules.json').read_bytes()).hexdigest()
profile_key=f'{department}_{year}'
guide_sig=hashlib.sha256((ROOT/'references/department_guide.json').read_bytes()).hexdigest() if mode=='학과·졸업 통합' else ''
for filename,error in errors.items(): st.warning(f'문서 읽기 오류 · {filename}: {error}')
if mode=='제공 PDF 한 개': docs=[d for d in docs if d.metadata['source']==load_rules()['source']]
if mode=='학과·졸업 통합': docs+=guide_documents()
store=None
if vector and docs:
 try:
  @st.cache_resource(max_entries=2)
  def shared_embeddings(model_name):
   from langchain_huggingface import HuggingFaceEmbeddings
   return HuggingFaceEmbeddings(model_name=model_name,model_kwargs={'device':'cpu'},encode_kwargs={'normalize_embeddings':True})
  @st.cache_resource
  def index(sig,scope,private_path):
   from src.embedding import get_embeddings
   selected,_=load_corpus(DATA,private_path,scope!='제공 PDF 한 개')
   if scope=='제공 PDF 한 개': selected=[d for d in selected if d.metadata['source']==load_rules()['source']]
   if scope=='학과·졸업 통합': selected+=guide_documents()
   rule_sig=hashlib.sha256((ROOT/'rules/graduation_rules.json').read_bytes()).hexdigest()
   directory=Path(private_path)/'.index'/hashlib.sha256((sig+scope+rule_sig+os.getenv('EMBEDDING_MODEL','default')).encode()).hexdigest()[:16]
   embeddings=shared_embeddings(os.getenv('EMBEDDING_MODEL','sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'))
   if (directory/'index.faiss').exists():
    try: return load_store(embeddings,directory)
    except Exception: pass
   return build_store(split_documents(selected),embeddings,directory)
  with st.spinner('다국어 벡터 인덱스 준비 중…'):
   index_signature=sig+criteria_sig+os.getenv('EMBEDDING_MODEL','default')+guide_sig+mode
   if user.get('guest'):
    if st.session_state.get('guest_index_signature')!=index_signature:
     embeddings=shared_embeddings(os.getenv('EMBEDDING_MODEL','sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'))
     st.session_state.guest_vector_store=build_store(split_documents(docs),embeddings,UPLOAD_DATA/'.index')
     st.session_state.guest_index_signature=index_signature
    store=st.session_state.guest_vector_store
   else:
    store=index(index_signature,mode,str(UPLOAD_DATA))
 except Exception as e: st.warning('벡터 검색 준비 실패. 원문 검색 사용: '+str(e))
st.info('이 서비스는 다면적 졸업인증을 진단합니다. 최종 졸업 확정과 졸업학점은 학교 공식 학사시스템에서 확인하세요.')
st.caption('현재 검색: '+('다국어 임베딩·FAISS' if store is not None else '검수된 기준표·키워드 검색')+' / 생성형 답변: '+('요청됨 (API 키·응답 검증 필요)' if llm else '사용 안 함'))
def render_result(result):
 current_input=st.session_state.get('diagnostic_inputs',{}).get(profile_key)
 if is_stale(result,current_input,criteria_sig,sig):
  st.warning('입력 내역 또는 기준 문서가 변경되었습니다. 아래는 지난 진단 결과입니다. 진단 메뉴에서 다시 계산해 주세요.')
 if result.get('generated_at'):
  timestamp=datetime.fromisoformat(result['generated_at']).astimezone(timezone(timedelta(hours=9)))
  st.caption('진단 시각: '+timestamp.strftime('%Y-%m-%d %H:%M:%S KST'))
 st.subheader(result['status'])
 st.write('다면적 졸업인증 충족 예상' if result['status']=='충족' else '다면적 졸업인증: '+result['status'])
 st.write('전체 졸업 가능 여부: 확인 필요 (졸업학점·기타 졸업요건 문서 미제공)')
 st.caption(f"{result.get('department', '')} · {result.get('year', '')}학번")
 if 'total_earned' in result: st.metric('현재 인증점수 / 필요점수', f"{result['total_earned']} / {result['total_required']}점")
 st.caption(result.get('scope', ''))
 if result['areas']:
  st.dataframe(table(result['areas'],lang),width='stretch')
  for area in result['areas']:
   st.progress(min(1.0,area['earned']/area['required']) if area['required'] else 1.0,text=f"{area['area']}: {area['earned']} / {area['required']}점 · 부족 {area['shortage']}점")
  st.dataframe(table(result['items'],lang),width='stretch')
 if result.get('missing'): st.error('부족한 필수 항목: '+', '.join(result['missing']))
 if result.get('next_steps'):
  st.markdown('**다음에 준비할 항목**')
  st.dataframe(table(result['next_steps'],lang),width='stretch')
 for issue in result['issues']: st.warning(issue)
 if result.get('source'): raw_st.caption(f"{tr('근거: ',lang)}{result['source']} p.{result['page']}")
 st.download_button('진단 결과 JSON 다운로드',json.dumps(result,ensure_ascii=False,indent=2),'graduation_result.json',mime='application/json')
def upload_panel():
 st.subheader('졸업기준 자료실')
 st.caption('제공 PDF는 공통 자료입니다. 추가 업로드는 현재 앱 계정에만 저장되며 다른 계정 검색에 포함되지 않습니다.')
 for p in list(DATA.glob('*.pdf'))+list(UPLOAD_DATA.glob('*.pdf')):
  count=sum(d.metadata['source']==p.name for d in docs)
  raw_st.write(p.name); st.caption(errors.get(p.name,f'{count}페이지 검색 가능'))
 uploads=st.file_uploader('PDF 추가',type=['pdf'],accept_multiple_files=True)
 if st.button('선택한 문서 등록'):
  notices=[]
  for upload in uploads or []:
   try:
    target=save_pdf(upload.getvalue(),upload.name,UPLOAD_DATA)
    notices.append(('success',f'{upload.name}: 등록 완료 ({target.name})'))
   except Exception as exc: notices.append(('error',f'{upload.name}: {exc}'))
  st.session_state.upload_notices=notices or [('warning','등록할 PDF를 선택해 주세요.')]
  st.cache_data.clear(); st.rerun()
 for level,message in st.session_state.get('upload_notices',[]): getattr(st,level)(message)
 st.caption('새 PDF는 검색에 반영됩니다. 진단 규칙은 원문 검수 후 JSON에 반영해야 합니다.')

if menu=='교수용 과제 평가':
 if user['role']!='evaluator': st.error('평가자 계정으로 로그인해 주세요.'); st.stop()
 st.subheader('교수용 과제 평가')
 st.info('이 화면은 가상 사례를 이용한 과제 확인용입니다. 실제 학생의 개인 기록을 불러오거나 저장하지 않습니다.')
 st.markdown('**1. PDF 질문·답변 / 2. 수강 목록과 활동 입력 / 3. 규칙 기반 진단**')
 st.caption('PDF 단독 RAG 메뉴에서 직접 질문하거나 아래 가상 사례로 영역별 판정을 확인하세요.')
 st.markdown('**교수님 확인 순서**\n1. 왼쪽에서 PDF 단독 RAG를 선택해 질문하고 출처를 확인합니다.\n2. 다국어 임베딩 + FAISS를 켜 실제 벡터 검색을 확인합니다.\n3. 다중 문서 RAG에서 별도 PDF를 등록한 뒤 새 문서 내용으로 질문합니다.\n4. 졸업요건 진단에서 수강 CSV/XLSX와 활동을 입력하고 부족한 항목을 확인합니다.')
 st.caption('이 화면은 간편 HTML이 아니라 원본 Python 프로그램입니다. API 키 없이 검색·계산을 사용할 수 있으며, 생성형 답변은 별도 API 설정이 필요합니다.')
 case=st.selectbox('가상 평가 사례',CASES,key='evaluation_case')
 if st.button('가상 사례 실행',type='primary'):
  evaluation=evaluate_case(department,year,case)
  st.subheader(evaluation['status'])
  if evaluation.get('total_required') is not None:
   st.metric('현재 인증점수 / 필요점수',f"{evaluation['total_earned']} / {evaluation['total_required']}점")
  st.dataframe(table(evaluation['areas'],lang),width='stretch')
  st.dataframe(table(evaluation['items'],lang),width='stretch')
  for issue in evaluation['issues']: st.warning(issue)
  st.caption('가상 결과는 학생별 저장 기록이나 실제 졸업 판정에 반영되지 않습니다.')
elif menu in ['학과·졸업 통합 상담','PDF 단독 RAG','다중 문서 RAG']:
 if menu=='다중 문서 RAG':
  with st.expander('문서 등록 및 검색 상태',expanded=True): upload_panel()
 st.subheader('문서에 물어보세요')
 st.caption('자유롭게 질문하세요. 학과·학번에 맞는 근거를 찾고, 자료에 없는 내용은 필요한 확인 자료를 안내합니다.')
 if mode=='학과·졸업 통합': st.caption('현재 근거: 졸업인증 PDF + 확인한 학과 홈페이지 교육과정·연락처. 전체 졸업학점 확정 규정은 미제공입니다.')
 context=hashlib.sha256(json.dumps([department,year,mode,sig,criteria_sig,lang,guide_sig],ensure_ascii=False).encode()).hexdigest()
 histories=st.session_state.setdefault('chat_histories',{})
 st.session_state.messages=histories.setdefault(context,[])
 if st.button('현재 대화 지우기'):
  histories[context]=[]; st.session_state.messages=[]
 def render_message(role,content):
  with st.chat_message(role):
   main,separator,source=content.partition('\n\n근거 원문:\n')
   st.text(main)
   if separator:
    with st.expander('근거 원문 보기'): raw_st.text(source)
 for role,content in st.session_state.get('messages',[]): render_message(role,content)
 sample=st.selectbox('추천 질문',['졸업인증 총점','학과활동 기준','코딩역량인증제 조건','자격증 인정 점수'],key='sample_question')
 ask_sample=st.button('선택한 질문 보내기')
 q=st.chat_input('예: AI·빅데이터학과 2022학번 졸업인증 총점은?')
 if ask_sample: q=sample
 if q:
  with st.chat_message('user'): st.text(q)
  previous_question=next((content for role,content in reversed(st.session_state.messages) if role=='user'),None)
  personal=st.session_state.get('diagnostic_results',{}).get(profile_key)
  if personal: personal=dict(personal,_stale=is_stale(personal,st.session_state.get('diagnostic_inputs',{}).get(profile_key),criteria_sig,sig))
  result,hits=answer_in_language(q,docs,department,year,store,llm,lang,mode=='학과·졸업 통합',previous_question,personal)
  render_message('assistant',result)
  st.session_state.messages.extend([('user',q),('assistant',result)])
elif menu=='졸업요건 진단':
 rule=get_rule(department,year)
 if not rule: st.warning('해당 학과·학번 기준이 없습니다. 문서를 추가해 주세요.'); st.stop()
 st.caption(f"원본 p.{rule['page']} · 필요 합계 {sum(rule['required'].values())}점")
 items=common_items(year)+rule['items']
 scope=f'{department}_{year}'
 restore_draft(st.session_state,scope)
 course_names=list(dict.fromkeys([i['name'] for i in items if i['kind']=='course']+[n for i in items for n in i.get('options',[])]))
 selected=list(st.multiselect('이수한 과목 선택',course_names,key=scope+'courses'))
 manual=st.text_area('직접 입력 (한 줄에 한 과목)',key=scope+'manual')
 csv=st.file_uploader('수강 과목 CSV / XLSX',type=['csv','xlsx'],key=scope+'csv')
 upload_error=False
 if csv:
  try: st.session_state.setdefault('saved_courses',{})[scope]=read_course_file(csv.getvalue(),csv.name)
  except Exception as exc:
   st.error(str(exc)); upload_error=True
 if not csv and st.session_state.get('saved_courses',{}).get(scope):
  st.caption('저장된 수강 파일의 이수 과목을 사용합니다.')
  if st.button('저장된 업로드 과목 비우기'):
   st.session_state.saved_courses[scope]=[]
 selected+=st.session_state.get('saved_courses',{}).get(scope,[])
 selected+=manual.splitlines()
 st.caption('띄어쓰기와 유니코드 정규화만 적용합니다. 다른 이름은 자동 인정하지 않습니다. 대학공통 항목은 공식 이수 여부로 체크하세요.')
 activities={}
 evidence={}
 for i in items:
  if i['kind'] in ['course','choice']: continue
  label=f"{i['name']} · {i['area']} · {i['points']}점"
  key=scope+i['name']
  if i['kind']=='official_course':
   st.markdown('**'+label+'**')
   course=st.text_input('해당 영역에서 이수한 과목명',key=key+'course')
   confirmed=st.checkbox('학사시스템에서 중핵교양 국제사회언어영역 이수 여부를 확인함',key=key+'confirmed')
   evidence[i['name']]={'course':course,'confirmed':confirmed}
   if course: selected.append(course)
   st.caption(i['help'])
   continue
  if i['kind']=='official_points':
   points=st.number_input(label+' · 공식 인정 점수',min_value=0,step=1,key=key+'points')
   confirmed=st.checkbox('해당 인재상의 공식 인정 점수를 확인함',key=key+'confirmed')
   evidence[i['name']]={'points':points,'confirmed':confirmed}
   st.caption(i['help'])
   continue
  if i['kind']=='achievement':
   st.markdown('**'+label+'**')
   certs=st.multiselect('취득한 PDF 권장 자격증',i['certificates'],key=key+'certs')
   record={'certificates':certs}
   for category,title,bounds in [('participation','경진대회 참가',i['participation_range']),('award','경진대회 수상',i['award_range'])]:
    record[category+'_points']=st.number_input(title+f' 공식 인정 점수 (없으면 0, 범위 {bounds[0]}~{bounds[1]})',min_value=0,step=1,key=key+category)
    record[category+'_confirmed']=st.checkbox(title+'의 학교 공식 인정 점수를 확인함',key=key+category+'confirmed')
   evidence[i['name']]=record
   st.caption('권장 자격증은 6점. 대회별 배점은 PDF에 없어 공식 인정 점수가 필요합니다. 참가·수상 중복 합산은 하지 않습니다.')
   continue
  if i['kind']=='unknown': st.caption(label+' — 세부 기준 확인 필요'); continue
  if i['kind']=='count': activities[i['name']]=st.number_input(label+f" (회/학기당 {i['per']}점)",min_value=0,step=1,key=key)
  elif i['kind']=='threshold': activities[i['name']]=st.number_input(label+f" (최소 {i['minimum']}: 레벨 또는 시험점수)",min_value=0,step=1,key=key)
  else: activities[i['name']]=st.checkbox(label+' · 공식 이수/인증 완료',key=key)
 official_requirements={}
 with st.expander('학사시스템의 필요 점수와 비교 (선택)'):
  st.caption('다른 값이 보이면 입력하세요. PDF 규칙을 덮어쓰지 않고 차이를 표시합니다.')
  for area in rule['required']:
   text=st.text_input(area+' · 학사시스템 필요 점수',key=scope+area+'official')
   if text.strip():
    try:
     value=float(text)
     if value<0 or not __import__('math').isfinite(value): raise ValueError()
     official_requirements[area]=value
    except ValueError:
     st.error(area+': 0 이상의 점수를 입력하세요.'); upload_error=True
 complete=st.checkbox('이수 내역을 모두 입력했습니다. 미선택 항목은 미이수입니다.',key=scope+'complete')
 signature=input_signature(department,year,selected,activities,complete,evidence,official_requirements)
 st.session_state.setdefault('diagnostic_inputs',{})[profile_key]=signature
 remember_draft(st.session_state,scope)
 if st.button('입력 저장',disabled=upload_error):
  try:
   persist(st,user,scope); st.success('체험 입력과 진단 결과는 현재 세션에서만 유지됩니다.' if user.get('guest') else '내 입력과 진단 결과를 저장했습니다.')
  except ValueError as exc: st.error(str(exc))
 st.caption('체험 입력과 결과는 현재 세션에서만 유지됩니다.' if user.get('guest') else '진단 실행 시 입력과 결과를 내 앱 계정에 저장합니다.')
 previous=st.session_state.get('diagnostic_results',{}).get(profile_key)
 if previous and is_stale(previous,signature,criteria_sig,sig):
  st.warning('입력 내용이 지난 진단 이후 변경되었습니다. 결과를 다시 계산해 주세요.')
 if st.button('나의 졸업인증 진단',type='primary',disabled=upload_error):
  try:
   result=check(department,year,selected,activities,complete,evidence,official_requirements)
   result=stamp_result(result,signature,criteria_sig,sig)
   st.session_state.result=result
   st.session_state.setdefault('diagnostic_results',{})[profile_key]=result
   persist(st,user,scope)
   render_result(result)
  except ValueError as exc: st.error(str(exc))
elif menu=='학과 안내':
 st.subheader('학과 안내')
 st.link_button('학과 홈페이지','https://home.sch.ac.kr/aibigdata/index.jsp')
 st.link_button('교육과정 안내','https://home.sch.ac.kr/aibigdata/02/0101.jsp')
 st.caption('학과사무실: 041-530-1667 · 미디어랩스관 ML202')
 st.caption('홈페이지 교육과정의 교과 학점은 PDF의 졸업인증 점수와 별개입니다. 적용 학번과 최신 확정 기준은 학과에 확인하세요.')
 with st.expander('PDF와 제공 학사화면의 차이',expanded=True):
  st.write('2022학번 참고: 제공 PDF는 졸업필수활동 15점을 대학공통에, 제공된 개인 학사화면은 학과 졸업필수활동에 표시합니다. 자율활동 분류도 다릅니다. 이는 제공된 화면의 대조이며 모든 학생에게 적용되는 공식 변경 규정은 아닙니다.')
  st.write('이 앱은 PDF 기준으로 계산합니다. 화면의 점수나 이수 이력은 자동 입력하지 않습니다. 차이가 있으면 진단 메뉴의 학사시스템 비교에 입력하고 학과에 확인하세요.')
 st.caption('공식 홈페이지 확인일: 2026-11-05. 홈페이지 내용은 참고 링크이며 PDF 단독 검색 근거에는 포함하지 않습니다.')
else:
 st.subheader('나의 진단 결과')
 result=st.session_state.get('diagnostic_results',{}).get(profile_key)
 if result: render_result(result)
 else: st.caption(f'{department} {year}학번의 진단 결과가 없습니다. 진단 메뉴에서 내역을 입력해 주세요.')
 st.caption('체험 결과는 현재 세션에서만 유지됩니다.' if user.get('guest') else '저장한 입력과 결과는 내 앱 계정으로 다시 불러옵니다. 채팅은 현재 로그인 세션에서만 유지됩니다.')
