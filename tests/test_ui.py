from streamlit.testing.v1 import AppTest
from src.utils import ROOT
import pytest
from src.auth import register

@pytest.fixture(autouse=True)
def accounts(tmp_path,monkeypatch):
    monkeypatch.setenv("GRADUATION_APP_DATA_DIR",str(tmp_path/"users"))
    register("20229990","UI Test Student","UITestpass123","AI·빅데이터학과",2022)

def logged_app():
    app=AppTest.from_file(str(ROOT/"app.py"))
    app.session_state.auth_user_id="20229990"
    app.session_state.main_menu="PDF 단독 RAG"
    return app


def by_label(elements, label):
    return next(e for e in elements if e.label == label)


def test_all_menus():
    at=logged_app().run(timeout=90)
    assert not at.exception
    for menu in ['졸업요건 진단','다중 문서 RAG','진단 결과']:
        at.sidebar.radio[0].set_value(menu).run(timeout=90)
        assert not at.exception


def test_chat_and_diagnosis_ui():
    at=logged_app().run(timeout=90)
    assert at.sidebar.selectbox[1].value=='AI·빅데이터학과'
    at.chat_input[0].set_value('2022학번 AI·빅데이터학과 졸업인증 총점').run(timeout=90)
    assert not at.exception
    assert any('95점' in t.value and 'p.5' in t.value for t in at.text)
    at.sidebar.radio[0].set_value('졸업요건 진단').run(timeout=90)
    by_label(at.multiselect,'이수한 과목 선택').set_value(['예비창업설계'])
    by_label(at.text_input,'해당 영역에서 이수한 과목명').set_value('공식언어과목')
    for checkbox in at.checkbox:
        if '경진대회' not in checkbox.label:
            checkbox.check()
    for entry in at.number_input:
        if '학과활동' in entry.label: entry.set_value(5)
        elif '코딩역량' in entry.label: entry.set_value(2)
        elif '공감' in entry.label: entry.set_value(5)
        elif '창의' in entry.label: entry.set_value(4)
        elif '글로벌' in entry.label: entry.set_value(10)
    by_label(at.multiselect,'취득한 PDF 권장 자격증').set_value(['SQL개발자'])
    by_label(at.button,'나의 졸업인증 진단').click().run(timeout=90)
    assert not at.exception
    assert any(h.value=='충족' for h in at.subheader)
    assert at.session_state.result['total_earned']==95
    by_label(at.number_input,'비교과자율활동(공감) · 비교과미지정 · 5점 · 공식 인정 점수').set_value(3)
    by_label(at.button,'나의 졸업인증 진단').click().run(timeout=90)
    assert any(h.value=='미충족' for h in at.subheader)
    assert any('비교과자율활동(공감)' in error.value for error in at.error)
    at.sidebar.radio[0].set_value('진단 결과').run(timeout=90)
    assert at.session_state.result['total_earned']==93
    assert not at.exception


def test_result_scope_and_stale_input():
    at=logged_app().run(timeout=90)
    at.sidebar.radio[0].set_value('졸업요건 진단').run(timeout=90)
    by_label(at.button,'나의 졸업인증 진단').click().run(timeout=90)
    assert not at.exception and 'generated_at' in at.session_state.result
    by_label(at.multiselect,'이수한 과목 선택').set_value(['예비창업설계']).run(timeout=90)
    assert any('지난 진단 이후 변경' in w.value for w in at.warning)
    at.sidebar.radio[0].set_value('진단 결과').run(timeout=90)
    assert any('지난 진단 결과' in w.value for w in at.warning)
    at.sidebar.number_input[0].set_value(2023).run(timeout=90)
    assert any('2023학번의 진단 결과가 없습니다' in c.value for c in at.caption)
    assert not any(h.value=='확인 필요' for h in at.subheader)
    at.sidebar.number_input[0].set_value(2022).run(timeout=90)
    assert any('지난 진단 결과' in w.value for w in at.warning)
    assert not at.exception


def test_chat_history_survives_mode_switch_and_can_clear():
    at=logged_app().run(timeout=90)
    at.chat_input[0].set_value('졸업인증 총점').run(timeout=90)
    at.sidebar.radio[0].set_value('다중 문서 RAG').run(timeout=90)
    assert len(at.chat_message)==0
    at.sidebar.radio[0].set_value('PDF 단독 RAG').run(timeout=90)
    assert len(at.chat_message)==2
    by_label(at.button,'현재 대화 지우기').click().run(timeout=90)
    assert len(at.chat_message)==0
    assert not at.exception


def keyed(elements,key):
    return next(element for element in elements if element.key==key)


def test_real_signup_login_and_logout_gate():
    at=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    assert not at.chat_input
    assert any('학교 학사시스템과 연결되지 않은' in info.value for info in at.info)
    keyed(at.text_input,'register_id').set_value('20228888')
    keyed(at.text_input,'register_name').set_value('새 학생')
    keyed(at.text_input,'register_password').set_value('Studentpass123')
    keyed(at.text_input,'register_repeat').set_value('Studentpass123')
    by_label(at.button,'앱 계정 만들기').click().run(timeout=90)
    assert not at.exception and at.success
    keyed(at.text_input,'login_id').set_value('20228888')
    keyed(at.text_input,'login_password').set_value('Wrongpass123')
    by_label(at.button,'로그인').click().run(timeout=90)
    assert at.error and not at.chat_input
    keyed(at.text_input,'login_password').set_value('Studentpass123')
    by_label(at.button,'로그인').click().run(timeout=90)
    assert not at.exception and at.chat_input
    assert any('새 학생' in element.value and '20228888' in element.value for element in at.sidebar.text)
    at.chat_input[0].set_value('졸업인증 총점').run(timeout=90)
    by_label(at.sidebar.button,'로그아웃').click().run(timeout=90)
    assert not at.exception and not at.chat_input
    assert 'chat_histories' not in at.session_state


@pytest.mark.parametrize('lang,login_label,menu_label',[
    ('en','Sign in','Certification check'),
    ('zh','登录','毕业认证诊断'),
    ('ja','ログイン','卒業認証チェック'),
])
def test_localized_gate_and_main_form(lang,login_label,menu_label):
    at=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    keyed(at.selectbox,'ui_language').set_value(lang).run(timeout=90)
    assert by_label(at.button,login_label)
    at.session_state.auth_user_id='20229990'
    at.run(timeout=90)
    assert not at.exception
    at.sidebar.radio[0].set_value('졸업요건 진단').run(timeout=90)
    assert not at.exception
    assert any('Check my certification'==b.label or '诊断我的毕业认证'==b.label or '卒業認証をチェック'==b.label for b in at.button)
    # Canonical regulation keys and numeric standards remain unchanged.
    assert any(n.key=='AI·빅데이터학과_2022학과활동' for n in at.number_input)


def test_saved_courses_and_result_restore_on_new_login():
    at=logged_app().run(timeout=90)
    at.sidebar.radio[0].set_value('졸업요건 진단').run(timeout=90)
    by_label(at.multiselect,'이수한 과목 선택').set_value(['예비창업설계'])
    by_label(at.button,'나의 졸업인증 진단').click().run(timeout=90)
    assert not at.exception
    assert at.session_state.result['total_earned']==5
    other=logged_app().run(timeout=90)
    other.sidebar.radio[0].set_value('졸업요건 진단').run(timeout=90)
    assert by_label(other.multiselect,'이수한 과목 선택').value==['예비창업설계']
    other.sidebar.radio[0].set_value('진단 결과').run(timeout=90)
    assert not other.exception
    assert any('2022학번' in caption.value for caption in other.caption)
    assert other.session_state.diagnostic_results['AI·빅데이터학과_2022']['total_earned']==5


def test_evaluator_can_register_without_a_student_number():
    at=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    keyed(at.radio,'entry_role').set_value('교수·평가자').run(timeout=90)
    assert not at.exception
    assert keyed(at.text_input,'register_id').label=='평가용 아이디'
    keyed(at.text_input,'register_id').set_value('review.teacher')
    keyed(at.text_input,'register_name').set_value('평가자 테스트')
    keyed(at.text_input,'register_password').set_value('Reviewpass123')
    keyed(at.text_input,'register_repeat').set_value('Reviewpass123')
    by_label(at.button,'앱 계정 만들기').click().run(timeout=90)
    assert not at.exception and at.success
    keyed(at.text_input,'login_id').set_value('review.teacher')
    keyed(at.text_input,'login_password').set_value('Reviewpass123')
    by_label(at.button,'로그인').click().run(timeout=90)
    assert not at.exception
    assert at.sidebar.radio[0].value=='교수용 과제 평가'
    by_label(at.selectbox,'가상 평가 사례').set_value('확인 가능한 조건 충족')
    by_label(at.button,'가상 사례 실행').click().run(timeout=90)
    assert not at.exception and any(s.value=='충족' for s in at.subheader)
    assert not at.session_state.diagnostic_results
    at.sidebar.radio[0].set_value('PDF 단독 RAG').run(timeout=90)
    at.chat_input[0].set_value('졸업인증 총점').run(timeout=90)
    assert not at.exception and any('95점' in t.value for t in at.text)


def test_login_fields_emitted_without_tabs():
    at=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    assert not at.tabs
    assert keyed(at.text_input,'login_id').label=='학번'
    field=keyed(at.text_input,'login_password')
    expected=field.proto.DESCRIPTOR.fields_by_name['type'].enum_type.values_by_name['PASSWORD'].number
    assert field.proto.type==expected
    assert keyed(at.text_input,'register_name').label=='이름'


def test_conversational_coding_and_followup_in_ui():
    at=logged_app().run(timeout=90)
    at.chat_input[0].set_value('코딩역량 인증제 조건이 뭐야').run(timeout=90)
    assert not at.exception
    assert any('Level 2 이상' in t.value and '5점' in t.value for t in at.text)
    at.chat_input[0].set_value('그럼 몇 점이야?').run(timeout=90)
    assert not at.exception
    assert sum('Level 2 이상' in t.value for t in at.text)>=2


def test_integrated_chat_and_pdf_only_are_distinct():
    at=logged_app().run(timeout=90)
    at.chat_input[0].set_value('학과 사무실 전화번호 알려줘').run(timeout=90)
    assert not any('041-530-1667' in t.value for t in at.text)
    at.sidebar.radio[0].set_value('학과·졸업 통합 상담').run(timeout=90)
    at.chat_input[0].set_value('우리 학과 사무실 전화번호 뭐야').run(timeout=90)
    assert not at.exception and any('041-530-1667' in t.value for t in at.text)
    at.chat_input[0].set_value('3학년에는 무슨 과목 배워?').run(timeout=90)
    assert any('자연어처리' in t.value for t in at.text)
