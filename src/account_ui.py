"""Streamlit login forms; students and classroom evaluators have separate entry points."""
from .auth import register,authenticate,get_user,load_profiles,save_profile,change_password
from .i18n import tr
from .graduation_rules import load_rules
from .ui_theme import render_welcome
import secrets
import tempfile


def start_guest_review(state):
    clear_identity(state)
    account_id='review:'+secrets.token_hex(16)
    state['review_directory']=tempfile.TemporaryDirectory(prefix='sch-review-')
    state['guest_user']={'student_id':account_id,'account_id':account_id,
                         'name':'교수·평가자','department':'AI·빅데이터학과',
                         'admission_year':2022,'role':'evaluator','guest':True}
    state['main_menu']='교수용 과제 평가'
    return state['guest_user']


def clear_identity(state):
    directory=state.get('review_directory')
    if directory is not None:
        directory.cleanup()
    for key in list(state):
        if key!='ui_language': del state[key]


def require_login(st,lang):
    if st.session_state.get('guest_user'):
        return st.session_state.guest_user
    identifier=st.session_state.get('auth_user_id')
    user=get_user(identifier) if identifier else None
    if user:
        if 'account_loaded' not in st.session_state:
            saved=load_profiles(identifier)
            st.session_state.drafts={key:value.get('widgets',{}) for key,value in saved.items()}
            st.session_state.saved_courses={key:value.get('uploaded_courses',[]) for key,value in saved.items()}
            st.session_state.diagnostic_results={key:value['result'] for key,value in saved.items() if value.get('result')}
            st.session_state.diagnostic_inputs={key:value['signature'] for key,value in saved.items() if value.get('signature')}
            st.session_state.account_loaded=True
        return user
    render_welcome(st.ui,lang,part='hero')
    if st.button('가입 없이 챗봇 시작',key='guest_review_entry',type='primary',width='stretch'):
        start_guest_review(st.session_state)
        st.rerun()
    st.caption('교수님도 학생도 가입 없이 PDF 질문과 진단을 체험할 수 있습니다. 입력은 현재 세션에만 유지됩니다.')
    render_welcome(st.ui,lang,part='features')
    with st.expander('개인 기록을 저장하려면 로그인·회원가입'):
        account_forms(st,lang)
    st.stop()


def account_forms(st,lang):
    st.subheader('로그인')
    st.info('학교 학사시스템과 연결되지 않은 과제용 앱 계정입니다. 학교 비밀번호를 사용하지 마세요.')
    entry=st.radio('접속 유형',['학생','교수·평가자'],key='entry_role',horizontal=True)
    role='student' if entry=='학생' else 'evaluator'
    id_label='학번' if role=='student' else '평가용 아이디'
    if role=='evaluator':
        st.caption('학번 없이 평가용 아이디로 가입합니다. 교수 신분을 인증하거나 학생 기록을 열람하는 계정은 아닙니다.')
    # Use ordinary columns rather than a lazy tab container so both forms are emitted directly.
    login_column,register_column=st.columns(2)
    with login_column:
        st.markdown('**'+tr('로그인',lang)+'**')
        with st.form('login_form_'+role):
            identifier=st.text_input(id_label,key='login_id',max_chars=40)
            password=st.text_input('비밀번호',type='password',key='login_password',max_chars=128)
            submitted=st.form_submit_button('로그인')
        if submitted:
            try:
                user=authenticate(identifier,password,role)
                if not user: st.error('아이디 또는 비밀번호가 올바르지 않습니다.')
                else:
                    clear_identity(st.session_state)
                    st.session_state.auth_user_id=user['student_id']
                    st.rerun()
            except ValueError as exc: st.error(str(exc))
    with register_column:
        st.markdown('**'+tr('회원가입',lang)+'**')
        with st.form('register_form_'+role):
            identifier=st.text_input(id_label,key='register_id',max_chars=40)
            name=st.text_input('이름',key='register_name',max_chars=60)
            departments=list(dict.fromkeys(r['department'] for r in load_rules()['profiles']))
            department=st.selectbox('학과',departments,index=departments.index('AI·빅데이터학과'),key='register_department')
            year=st.number_input('입학연도' if role=='student' else '검토할 입학연도',min_value=2000,max_value=2100,value=2022,key='register_year')
            password=st.text_input('앱 전용 비밀번호',type='password',key='register_password',max_chars=128)
            repeat=st.text_input('비밀번호 확인',type='password',key='register_repeat',max_chars=128)
            st.caption('앱 전용 비밀번호는 10~128자여야 합니다.')
            st.caption('비밀번호에 영문과 숫자를 함께 넣어 주세요.')
            submitted=st.form_submit_button('앱 계정 만들기')
        if submitted:
            try:
                if password!=repeat: raise ValueError('비밀번호 확인이 일치하지 않습니다.')
                register(identifier,name,password,department,int(year),role)
                st.success('계정을 만들었습니다. 왼쪽 로그인 입력란에서 로그인해 주세요.')
            except ValueError as exc: st.error(str(exc))


def account_sidebar(st,user):
    if user.get('guest'):
        st.sidebar.text('교수·평가자 · 가입 없는 확인')
        st.sidebar.caption('업로드와 입력은 현재 세션 전용입니다. 체험 종료 시 파일을 정리합니다.')
        if st.sidebar.button('체험 종료',key='leave_guest_review'):
            clear_identity(st.session_state)
            st.rerun()
        return
    label=user['student_id'].removeprefix('evaluator:')
    st.sidebar.text(f"{user['name']} · {label}")
    st.sidebar.caption('학생' if user['role']=='student' else '교수·평가자 (과제 확인용)')
    if st.sidebar.button('로그아웃'):
        clear_identity(st.session_state)
        st.rerun()
    with st.sidebar.expander('비밀번호 변경'):
        with st.form('password_change'):
            current=st.text_input('현재 비밀번호',type='password',key='change_current')
            new=st.text_input('새 비밀번호',type='password',key='change_new')
            if st.form_submit_button('비밀번호 변경'):
                try:
                    change_password(user['student_id'],current,new)
                    st.success('비밀번호를 변경했습니다.')
                except ValueError as exc: st.error(str(exc))


def restore_draft(state,profile):
    for key,value in state.get('drafts',{}).get(profile,{}).items():
        if key not in state: state[key]=value


def remember_draft(state,profile):
    state.setdefault('drafts',{})[profile]={key:value for key,value in state.items()
        if key.startswith(profile) and isinstance(value,(str,int,float,bool,list)) and not key.endswith('csv')}


def persist(st,user,profile):
    if user.get('guest'): return
    save_profile(user['student_id'],profile,{
        'widgets':st.session_state.get('drafts',{}).get(profile,{}),
        'uploaded_courses':st.session_state.get('saved_courses',{}).get(profile,[]),
        'result':st.session_state.get('diagnostic_results',{}).get(profile),
        'signature':st.session_state.get('diagnostic_inputs',{}).get(profile),
    })
