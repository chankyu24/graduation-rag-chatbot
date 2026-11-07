"""Localized presentation must leave Korean rule values and inputs untouched."""
from copy import deepcopy
import pytest

from src.i18n import LocalizedUI, MESSAGES, tr, table


class RecordingUI:
    def __init__(self): self.calls = []
    @property
    def sidebar(self): return self
    def __getattr__(self, name):
        def call(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            return args[1][0] if name in {'selectbox', 'radio'} else None
        return call


@pytest.mark.parametrize('lang', ['en', 'zh', 'ja'])
def test_guest_entry_modes_and_validation_are_translated(lang):
    texts = [
        '교수님: 가입 없이 실제 챗봇 확인',
        '교수·평가자 · 가입 없는 확인',
        '체험 종료',
        '업로드와 입력은 현재 세션 전용입니다. 체험 종료 시 파일을 정리합니다.',
        '체험 입력과 결과는 현재 세션에서만 유지됩니다.',
        '제공 PDF 다운로드',
        '다국어 벡터 인덱스 준비 중…',
        'PDF는 0바이트 초과 30MB 이하여야 합니다.',
        'CSV 열 이름은 비어 있거나 중복될 수 없습니다. 띄어쓰기만 다른 열도 중복입니다.',
        '다른 필수 교과와 동일 과목을 중복 배정할 수 없습니다. 공식 교과 영역 확인 필요',
    ]
    for text in texts:
        assert tr(text, lang) != text
    result=tr('현재 검색: 검수된 기준표·키워드 검색 / 생성형 답변: 사용 안 함',lang)
    assert '현재 검색' not in result and '사용 안 함' not in result
    assert tr('12행: CSV 열 수가 일치하지 않습니다.',lang).startswith('12')


@pytest.mark.parametrize('lang', ['en', 'zh', 'ja'])
def test_select_help_placeholder_and_custom_formatter_keep_values(lang):
    raw=RecordingUI(); ui=LocalizedUI(raw,lang)
    options=['예비창업설계','현대기본영어']
    returned=ui.selectbox('이수한 과목 선택',options,help='과목명은 원문을 확인하세요.',
                          placeholder='해당 영역에서 이수한 과목명',
                          format_func=lambda value:value, key='canonical_course')
    _,args,kwargs=raw.calls[-1]
    assert returned=='예비창업설계' and args[1] is options
    assert kwargs['key']=='canonical_course'
    assert kwargs['help']==tr('과목명은 원문을 확인하세요.',lang)
    assert kwargs['placeholder']==tr('해당 영역에서 이수한 과목명',lang)
    assert '예비창업설계' in kwargs['format_func']('예비창업설계')
    assert kwargs['format_func']('예비창업설계')!='예비창업설계'


@pytest.mark.parametrize('lang', ['en', 'zh', 'ja'])
def test_diagnostic_labels_and_table_keep_course_and_source(lang):
    raw=RecordingUI();ui=LocalizedUI(raw,lang)
    ui.checkbox('인간사랑 · 대학공통 · 5점 · 공식 이수/인증 완료',key='AI·빅데이터학과_2022인간사랑',value=True)
    _,args,kwargs=raw.calls[-1]
    assert '인간사랑' in args[0] and kwargs['value'] is True
    assert kwargs['key']=='AI·빅데이터학과_2022인간사랑'
    rows=[{'name':'예비창업설계','earned':0,'required':5,'status':'미충족',
           'detail':'공식 이수 내역 없음','source':'2026년도 학과기준 시안.pdf'}]
    before=deepcopy(rows);translated=table(rows,lang)[0]
    assert rows==before
    assert '예비창업설계' in next(value for value in translated.values() if isinstance(value,str) and '예비창업설계' in value)
    assert '2026년도 학과기준 시안.pdf' in translated.values()
    assert tr('공식 이수 내역 없음',lang) in translated.values()
    assert 5 in translated.values() and 0 in translated.values()


def test_spinner_progress_metric_and_keyword_labels_are_localized():
    raw=RecordingUI();ui=LocalizedUI(raw,'en')
    ui.spinner('다국어 벡터 인덱스 준비 중…')
    assert raw.calls[-1][1][0]=='Preparing multilingual vector index…'
    ui.metric('현재 인증점수 / 필요점수','95 / 95점')
    assert 'points' in raw.calls[-1][1][1]
    ui.text_input(label='이름',placeholder='해당 영역에서 이수한 과목명')
    assert raw.calls[-1][2]['label']=='Name'
    ui.progress(.5,text='교과: 5 / 10점 · 부족 5점')
    assert 'Curricular' in raw.calls[-1][2]['text']
    assert raw.calls[-1][1][0]==.5


def test_text_translates_notices_without_rewriting_names_or_original_evidence():
    raw=RecordingUI();ui=LocalizedUI(raw,'en')
    ui.sidebar.text('교수·평가자 · 가입 없는 확인')
    assert raw.calls[-1][1][0]=='Instructor / Evaluator · no registration'
    body='원본 근거: 예비창업설계 5점 · 2022학번'
    ui.text(body)
    assert raw.calls[-1][1][0]==body
    ui.text('Test Student · 20229991')
    assert raw.calls[-1][1][0]=='Test Student · 20229991'
    assert tr('학번','en')=='Student ID'
    assert tr('2022학번','en')=='2022 cohort'


@pytest.mark.parametrize('lang', ['en','zh','ja'])
def test_actual_guest_entry_and_diagnostic_controls_in_three_languages(tmp_path,monkeypatch,lang):
    from streamlit.testing.v1 import AppTest
    from src.utils import ROOT
    monkeypatch.setenv('GRADUATION_APP_DATA_DIR',str(tmp_path/'accounts'))
    monkeypatch.setenv('RAG_VECTOR_DEFAULT','0')
    app=AppTest.from_file(str(ROOT/'app.py')).run(timeout=90)
    next(s for s in app.selectbox if s.key=='ui_language').set_value(lang).run(timeout=90)
    entry=next(b for b in app.button if b.key=='guest_review_entry')
    assert entry.label==tr('교수님: 가입 없이 실제 챗봇 확인',lang)
    entry.click().run(timeout=90)
    assert not app.exception
    assert any(tr('교수·평가자 · 가입 없는 확인',lang)==text.value for text in app.sidebar.text)
    app.sidebar.radio[0].set_value('졸업요건 진단').run(timeout=90)
    assert not app.exception
    activity=next(n for n in app.number_input if n.key=='AI·빅데이터학과_2022학과활동')
    assert '학과활동' in activity.label
    assert app.sidebar.selectbox[1].value=='AI·빅데이터학과'
    next(b for b in app.button if b.label==tr('나의 졸업인증 진단',lang)).click().run(timeout=90)
    assert not app.exception and app.session_state.result['total_required']==95
    next(b for b in app.sidebar.button if b.key=='leave_guest_review').click().run(timeout=90)
    assert not app.exception
