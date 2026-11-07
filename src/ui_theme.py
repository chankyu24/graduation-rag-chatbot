"""Presentation only: native Streamlit controls and graduation rules stay intact.

No external fonts, images, scripts, or network requests are required. Every
dynamic value placed in HTML is escaped, including saved diagnostic values.
"""
from html import escape
from math import isfinite

from .i18n import tr


_CSS = """
<style>
:root {
  --sch-navy: #142b43;
  --sch-navy-deep: #102236;
  --sch-teal: #087f78;
  --sch-teal-deep: #06645f;
  --sch-teal-soft: #e8f4f0;
  --sch-ivory: #f7f8f3;
  --sch-paper: #ffffff;
  --sch-ink: #1d3349;
  --sch-muted: #586c7b;
  --sch-line: #dce5df;
  --sch-focus: #1479b8;
  --sch-radius: 16px;
  --sch-font: 'Pretendard', 'Noto Sans KR', 'Apple SD Gothic Neo',
    'Malgun Gothic', 'Yu Gothic', 'Segoe UI', system-ui, sans-serif;
}
.stApp, [data-testid="stAppViewContainer"] {
  background: var(--sch-ivory);
  color: var(--sch-ink);
  font-family: var(--sch-font);
}
[data-testid="stHeader"] {
  background: rgba(247,248,243,.96);
  border-bottom: 1px solid rgba(220,229,223,.7);
}
[data-testid="stMainBlockContainer"] {
  max-width: 1210px;
  padding: 2.8rem 3.25rem 5rem;
}
.stApp h1, .stApp h2, .stApp h3 {
  color: var(--sch-navy);
  font-family: var(--sch-font);
  font-weight: 750;
  word-break: keep-all;
  overflow-wrap: anywhere;
}
.stApp h1 {font-size: clamp(2rem,3.3vw,3rem); letter-spacing: -.055em; line-height: 1.23; padding-top: .35rem; padding-bottom: .6rem;}
.stApp h2 {font-size: clamp(1.42rem,2.1vw,1.9rem); letter-spacing: -.035em; line-height: 1.35;}
.stApp h3 {font-size: 1.1rem; letter-spacing: -.02em;}
.stApp p, .stApp li {font-family: var(--sch-font); line-height: 1.75;}
.stApp a {color: var(--sch-teal-deep); text-underline-offset: .2em;}
[data-testid="stCaptionContainer"] {color: var(--sch-muted); line-height: 1.65;}
.stApp :is(a,button,input,textarea,select,summary,[role="combobox"],[role="radio"],[role="checkbox"]):focus-visible {
  outline: 3px solid var(--sch-focus) !important;
  outline-offset: 3px !important;
}
[data-testid="stWidgetLabel"] p {font-size: .875rem; font-weight: 650; letter-spacing: -.01em; color: var(--sch-ink);}
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-baseweb="select"] > div {
  background: var(--sch-paper);
  color: var(--sch-ink);
  border-color: var(--sch-line);
  font-family: var(--sch-font);
}
[data-testid="stTextInput"] > div,
[data-testid="stTextArea"] > div,
[data-testid="stNumberInput"] > div,
[data-baseweb="select"] > div {border-radius: 10px;}
[data-testid="stCheckbox"] label,
[data-testid="stRadio"] label {padding-top: .15rem; padding-bottom: .15rem;}
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button,
[data-testid="stLinkButton"] a,
[data-testid="stFormSubmitButton"] button {
  min-height: 2.8rem;
  border: 1px solid var(--sch-line);
  border-radius: 10px;
  background: var(--sch-paper);
  color: var(--sch-navy);
  font-family: var(--sch-font);
  font-weight: 650;
  box-shadow: 0 2px 3px rgba(20,43,67,.025);
  transition: border-color .16s ease, background .16s ease, box-shadow .16s ease;
}
[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover,
[data-testid="stFormSubmitButton"] button:hover {
  border-color: var(--sch-teal);
  background: #f2f9f6;
  color: var(--sch-teal-deep);
  box-shadow: 0 3px 10px rgba(8,127,120,.07);
}
.stApp [data-testid="stBaseButton-primary"] {
  background: var(--sch-teal);
  border-color: var(--sch-teal);
  color: white;
}
.stApp [data-testid="stBaseButton-primary"]:hover {
  background: var(--sch-teal-deep);
  border-color: var(--sch-teal-deep);
  color: white;
}
.stApp button:disabled {opacity: .55; cursor: not-allowed; box-shadow: none;}
[data-testid="stForm"] {
  padding: 1.45rem;
  border: 1px solid var(--sch-line);
  border-radius: var(--sch-radius);
  background: var(--sch-paper);
  box-shadow: 0 6px 24px rgba(20,43,67,.035);
}
[data-testid="stExpander"] {
  border-radius: 12px;
  border-color: var(--sch-line);
  background: rgba(255,255,255,.65);
}
[data-testid="stExpander"] summary {font-weight: 600; font-size: .85rem;}
[data-testid="stAlert"] {border-radius: 12px; border: 1px solid rgba(20,43,67,.07);}
[data-testid="stFileUploader"] {
  padding: .9rem;
  border: 1px dashed #a6bfb7;
  border-radius: 13px;
  background: rgba(255,255,255,.65);
}
[data-testid="stFileUploaderDropzone"] {background: #f0f6f1; border-radius: 9px;}
[data-testid="stMetric"] {
  background: var(--sch-paper);
  padding: 1.15rem 1.3rem;
  border: 1px solid var(--sch-line);
  border-radius: 13px;
}
[data-testid="stMetricValue"] {color: var(--sch-navy); font-weight: 750; letter-spacing: -.04em;}
[data-testid="stDataFrame"] {border: 1px solid var(--sch-line); border-radius: 12px; overflow: hidden;}
[data-testid="stProgress"] {margin-top: .5rem; margin-bottom: .9rem;}
[data-testid="stChatMessage"] {
  background: var(--sch-paper);
  border: 1px solid var(--sch-line);
  border-radius: 16px;
  padding: 1.3rem 1.35rem;
  margin-bottom: .8rem;
  box-shadow: 0 3px 14px rgba(20,43,67,.025);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
  background: #edf5f0;
  border-color: #d1e4d9;
}
[data-testid="stChatMessageAvatarAssistant"] {background: var(--sch-navy); color: white;}
[data-testid="stChatMessageAvatarUser"] {background: var(--sch-teal); color: white;}
[data-testid="stChatMessageContent"] {min-width: 0; overflow-wrap: anywhere;}
[data-testid="stChatMessageContent"] [data-testid="stText"] {
  font-family: var(--sch-font);
  font-size: .94rem;
  line-height: 1.9;
}
[data-testid="stChatMessageContent"] [data-testid="stExpander"] {background: #f8faf7;}
[data-testid="stChatInput"] {
  background: var(--sch-paper);
  border: 1.5px solid #a9c7ba;
  border-radius: 14px;
  box-shadow: 0 5px 22px rgba(20,43,67,.055);
}
[data-testid="stChatInput"]:focus-within {border-color: var(--sch-teal);}
[data-testid="stChatInput"] textarea {font-family: var(--sch-font); color: var(--sch-ink);}
[data-testid="stBottom"] {background: var(--sch-ivory);}
[data-testid="stSidebar"] {
  background: var(--sch-navy-deep);
  border-right: 1px solid #21384d;
}
[data-testid="stSidebarContent"] {padding-top: 1.25rem;}
[data-testid="stSidebar"] :is(h1,h2,h3,p,label,summary) {color: #eef4f5;}
[data-testid="stSidebar"] [data-testid="stText"],
[data-testid="stSidebar"] [data-testid="stText"] span {color: #eef4f5;}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color: #b7c9d3; font-size: .74rem;}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {color: #b7c9d3; font-size: .72rem; letter-spacing: .025em;}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  padding: .5rem .55rem;
  border-radius: 8px;
  border: 1px solid transparent;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background: #1a384d;}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {background: #214352; border-color: #3b6271;}
[data-testid="stSidebar"] [data-testid="stExpander"] {background: #172f43; border-color: #30495c;}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {color: #eef4f5;}
[data-testid="stSidebar"] :is([data-testid="stTextInput"],[data-testid="stNumberInput"],[data-baseweb="select"]) input {color: var(--sch-ink);}
[data-testid="stSidebar"] [data-baseweb="select"] {color: var(--sch-ink);}
[data-testid="stSidebar"] [data-baseweb="select"] p {color: var(--sch-ink);}
[data-testid="stSidebar"] [data-testid="stButton"] button,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button {background: #edf5f1; color: var(--sch-navy); border-color: #c9ddd3;}
[data-testid="stSidebar"] [data-testid="stButton"] button p,
[data-testid="stSidebar"] [data-testid="stDownloadButton"] button p,
[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button p,
[data-testid="stSidebar"] [data-testid="stLinkButton"] a p {color: var(--sch-navy);}
[data-testid="stSidebar"] a {color: #a5ded6;}
.sch-brandbar {display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin: .15rem 0 1rem;}
.sch-brand {display: flex; align-items: center; gap: .65rem; color: var(--sch-navy); font-size: .7rem; font-weight: 750; letter-spacing: .14em;}
.sch-mark {width: 34px; height: 34px; display: grid; place-items: center; background: var(--sch-navy); color: white; border-radius: 10px; flex-shrink: 0;}
.sch-mark svg {width: 19px; height: 19px;}
.sch-brand-note {color: var(--sch-muted); font-size: .7rem; line-height: 1.5; text-align: right;}
.sch-welcome {margin: .5rem 0 1.55rem; border: 1px solid #d5e3da; border-radius: 20px; overflow: hidden; background: var(--sch-paper); box-shadow: 0 10px 34px rgba(20,43,67,.035);}
.sch-welcome-top {padding: 1.75rem 1.9rem 1.65rem; display: grid; grid-template-columns: minmax(0,1fr) auto; gap: 1.5rem; align-items: center; background: linear-gradient(115deg,#eef5ee 0%,#f6f9f2 65%,#edf6f3 100%);}
.sch-eyebrow {font-size: .65rem; letter-spacing: .13em; font-weight: 800; text-transform: uppercase; color: var(--sch-teal-deep); margin: 0 0 .55rem; line-height: 1.7;}
.sch-welcome h2 {margin: 0 0 .65rem; padding: 0; font-size: clamp(1.6rem,2.4vw,2.15rem); line-height: 1.4; letter-spacing: -.04em;}
.sch-welcome-copy {font-size: .86rem; color: var(--sch-muted); line-height: 1.85; max-width: 620px; margin: 0; word-break: keep-all;}
.sch-proofmark {width: 92px; height: 112px; background: white; border: 1px solid #cfdfd4; border-radius: 13px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: .5rem; box-shadow: 8px 8px 0 #dcece1; color: var(--sch-teal-deep);}
.sch-proofmark svg {width: 35px; height: 35px;}
.sch-proofmark span {font-size: .62rem; letter-spacing: .1em; font-weight: 750;}
.sch-features {display: grid; grid-template-columns: repeat(3,minmax(0,1fr));}
.sch-feature {padding: 1.15rem 1.4rem; border-top: 1px solid var(--sch-line);}
.sch-feature + .sch-feature {border-left: 1px solid var(--sch-line);}
.sch-feature-head {display: flex; align-items: center; gap: .55rem; color: var(--sch-navy); font-size: .83rem; font-weight: 750; margin-bottom: .35rem;}
.sch-feature-num {font-family: 'Segoe UI',system-ui,sans-serif; color: var(--sch-teal); font-size: .7rem; letter-spacing: .03em;}
.sch-feature p {font-size: .82rem; color: var(--sch-muted); margin: 0; line-height: 1.8; word-break: keep-all;}
.sch-section-header {display: flex; justify-content: space-between; align-items: end; gap: 1.1rem; margin: .65rem 0 1.25rem; padding-bottom: 1.25rem; border-bottom: 1px solid var(--sch-line);}
.sch-section-header h2 {font-size: clamp(1.45rem,2vw,1.8rem); margin: 0 0 .4rem; padding: 0; letter-spacing: -.04em;}
.sch-section-header .sch-description {font-size: .875rem; color: var(--sch-muted); line-height: 1.8; margin: 0; max-width: 670px; word-break: keep-all;}
.sch-profile {display: flex; align-items: center; gap: .55rem; max-width: 330px; padding: .55rem .8rem; color: var(--sch-navy); background: white; border: 1px solid var(--sch-line); border-radius: 10px; font-size: .72rem; flex-shrink: 0; line-height: 1.6;}
.sch-profile-dot {width: 7px; height: 7px; background: var(--sch-teal); border-radius: 50%; flex-shrink: 0;}
.sch-result {border: 1px solid #ccdcd3; border-radius: 18px; background: white; overflow: hidden; margin: .75rem 0 1.4rem; box-shadow: 0 8px 25px rgba(20,43,67,.035);}
.sch-result-top {display: flex; justify-content: space-between; align-items: start; gap: 1.3rem; padding: 1.45rem 1.6rem; background: #eff5ef;}
.sch-result-value {color: var(--sch-navy); font-family: 'Segoe UI',var(--sch-font); font-size: 2.6rem; line-height: 1.2; font-weight: 750; letter-spacing: -.06em; margin-top: .2rem;}
.sch-result-value small {font-size: .92rem; color: var(--sch-muted); font-weight: 500; letter-spacing: 0; margin-left: .4rem;}
.sch-status {display: inline-flex; align-items: center; gap: .4rem; padding: .4rem .75rem; border-radius: 30px; font-size: .74rem; font-weight: 750; white-space: nowrap; border: 1px solid transparent;}
.sch-status::before {content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor;}
.sch-status-met {color: #146744; background: #def1e5; border-color: #c1e0cd;}
.sch-status-notmet {color: #8c4818; background: #fff0e0; border-color: #efdabf;}
.sch-status-review {color: #3b5d7b; background: #e6eff8; border-color: #ccdeef;}
.sch-result-areas {display: grid; grid-template-columns: repeat(auto-fit,minmax(160px,1fr)); padding: .4rem .8rem;}
.sch-area {padding: .8rem; min-width: 0;}
.sch-area-label {display: flex; justify-content: space-between; gap: .5rem; font-size: .71rem; color: var(--sch-muted); line-height: 1.7; margin-bottom: .55rem;}
.sch-area-label strong {color: var(--sch-navy); font-weight: 700; white-space: nowrap;}
.sch-meter {height: 5px; width: 100%; border-radius: 10px; background: #e8eeea; overflow: hidden;}
.sch-meter-fill {height: 100%; border-radius: 10px; background: var(--sch-teal);}
.sch-result-note {border-top: 1px solid #e7ede8; padding: .85rem 1.6rem; font-size: .7rem; color: var(--sch-muted); line-height: 1.8; overflow-wrap: anywhere;}
.sch-source-tag {display: block; color: #4b6471; margin-top: .3rem; font-size: .66rem;}
@media (max-width: 900px) {
  [data-testid="stMainBlockContainer"] {padding-left: 1.65rem; padding-right: 1.65rem;}
  .sch-section-header {align-items: start; flex-direction: column; gap: .8rem;}
  .sch-profile {max-width: 100%;}
  .sch-welcome-top {padding: 1.4rem;}
  .sch-feature {padding: 1rem;}
}
@media (max-width: 600px) {
  [data-testid="stMainBlockContainer"] {padding: 3rem 1rem 4rem;}
  .stApp h1 {font-size: 2rem; line-height: 1.3; letter-spacing: -.05em;}
  .stApp h2 {font-size: 1.4rem;}
  [data-testid="stForm"] {padding: 1rem; border-radius: 13px;}
  [data-testid="stChatMessage"] {padding: .95rem .8rem; gap: .7rem; border-radius: 13px;}
  [data-testid="stChatMessageContent"] [data-testid="stText"] {font-size: .87rem;}
  [data-testid="stWidgetLabel"] p {font-size: .78rem;}
  [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
  [data-testid="stNumberInput"] input {font-size: 16px;}
  .sch-brandbar {gap: .5rem; align-items: start; margin-bottom: .65rem; flex-wrap: wrap;}
  .sch-brand {font-size: .59rem; letter-spacing: .08em;}
  .sch-brand-note {font-size: .7rem; width: 100%; text-align: left; padding-left: 39px;}
  .sch-mark {width: 29px; height: 29px; border-radius: 8px;}
  .sch-welcome {border-radius: 15px;}
  .sch-welcome-top {grid-template-columns: minmax(0,1fr); padding: 1.2rem; gap: .6rem;}
  .sch-welcome h2 {font-size: 1.65rem;}
  .sch-welcome-copy {font-size: .8rem;}
  .sch-proofmark {display: none;}
  .sch-features {grid-template-columns: minmax(0,1fr);}
  .sch-feature {padding: .85rem 1.2rem;}
  .sch-feature + .sch-feature {border-left: none;}
  .sch-section-header {margin-top: .4rem; padding-bottom: 1rem;}
  .sch-result-top {padding: 1.15rem; gap: .5rem;}
  .sch-result-value {font-size: 2.2rem;}
  .sch-result-value small {font-size: .76rem;}
  .sch-status {font-size: .68rem; padding: .33rem .6rem;}
  .sch-result-areas {grid-template-columns: repeat(2,minmax(0,1fr)); padding: .3rem .35rem;}
  .sch-area {padding: .7rem;}
  .sch-area-label {flex-wrap: wrap; gap: .15rem;}
  .sch-result-note {padding: .8rem 1.05rem;}
}
@media (prefers-reduced-motion: reduce) {
  .stApp *, .stApp *::before, .stApp *::after {scroll-behavior: auto !important; transition: none !important; animation: none !important;}
}
</style>
"""

_BOOK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 6c-3-2-6-2-9-1v14c3-1 6-1 9 1 3-2 6-2 9-1V5c-3-1-6-1-9 1Z"/><path d="M12 6v14M6 8h3M6 11h3M15 8h3M15 11h3"/></svg>'
_DOCUMENT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9Z"/><path d="M14 3v6h6M8 13h8M8 17h5"/></svg>'


def _esc(value):
    return escape(str(value), quote=True)


def _text(lang, ko, en, zh, ja):
    return {'ko': ko, 'en': en, 'zh': zh, 'ja': ja}.get(lang, ko)


def _html(st, value):
    st.markdown(value, unsafe_allow_html=True)


def apply_theme(raw_st):
    """Apply style without changing native controls, widget keys, or behavior."""
    _html(raw_st, _CSS)


def render_header(raw_st, lang='ko'):
    """Small brand strip. Keep the existing native st.title as the page's h1."""
    note = _text(lang, '과제용 독립 앱 · 학교 공식 서비스 아님',
                 'Independent course project · Not an official university service',
                 '独立课程项目 · 非学校官方服务', '授業用の独立アプリ・大学の公式サービスではありません')
    _html(raw_st, f'<div class="sch-brandbar"><div class="sch-brand"><span class="sch-mark">{_BOOK}</span><span>SCH · GRADUATION GUIDE</span></div><div class="sch-brand-note">{_esc(note)}</div></div>')


def render_welcome(raw_st, lang='ko', part='all'):
    """A compact entry hero and three honest, noninteractive feature summaries."""
    kicker = _text(lang, '문서에서 시작하는 졸업 준비', 'A CLEARER PATH FROM DOCUMENT TO PLAN',
                   '从文档开始，规划毕业准备', '資料から始める、卒業への準備')
    title = _text(lang, '근거를 확인하고,<br>나의 다음 단계를 준비하세요.',
                  'Understand the requirements.<br>Plan your next step.',
                  '核对要求，<br>准备自己的下一步。', '根拠を確かめて、<br>次の一歩を準備しましょう。')
    description = _text(lang,
        '학과·학번에 맞는 PDF 근거를 찾아보고, 수강 과목과 활동을 입력해 다면적 졸업인증의 준비 상태를 확인합니다.',
        'Find PDF evidence for your department and admission year. Add your courses and activities to check your certification progress.',
        '查找对应院系与入学年份的PDF依据，输入课程与活动，核对多维毕业认证的准备情况。',
        '学科・入学年度に合うPDFの根拠を検索し、履修科目と活動から卒業認証の準備状況を確認します。')
    features = [
        (_text(lang, 'PDF 근거로 질문하기', 'Ask with PDF evidence', '依据PDF提问', 'PDFの根拠で質問'),
         _text(lang, '답변의 문서명과 페이지를 함께 확인합니다.', 'Check the document and page behind each sourced answer.', '核对有依据回答的文档名称与页码。', '根拠付き回答の文書名とページを確認します。')),
        (_text(lang, '추가 문서 함께 검색하기', 'Search additional documents', '整合追加文档检索', '追加資料もまとめて検索'),
         _text(lang, '제공 PDF와 업로드한 자료를 구분해 살펴봅니다.', 'Review the supplied PDF alongside your uploaded sources.', '结合所提供的PDF与上传资料，逐一核对来源。', '提供PDFとアップロード資料の出典を区別して確認します。')),
        (_text(lang, '과목·활동으로 진단하기', 'Check courses and activities', '依据课程与活动诊断', '科目・活動から診断'),
         _text(lang, '점수는 규칙으로 계산하고 부족한 항목을 확인합니다.', 'Rules calculate the points and highlight missing items.', '依照规则计算分数，查看未满足项目。', '点数はルールで計算し、不足項目を確認します。')),
    ]
    cards = ''.join(f'<div class="sch-feature"><div class="sch-feature-head"><span class="sch-feature-num">0{index}</span><span>{_esc(name)}</span></div><p>{_esc(copy)}</p></div>' for index, (name, copy) in enumerate(features, 1))
    # title is exclusively one of the reviewed constants above; user text is never inserted.
    hero=f'<div class="sch-welcome-top"><div><div class="sch-eyebrow">{_esc(kicker)}</div><h2>{title}</h2><p class="sch-welcome-copy">{_esc(description)}</p></div><div class="sch-proofmark" aria-hidden="true">{_DOCUMENT}<span>PDF · EVIDENCE</span></div></div>'
    content=(hero if part!='features' else '')+(f'<div class="sch-features">{cards}</div>' if part!='hero' else '')
    _html(raw_st, f'<section class="sch-welcome" aria-label="{_esc(kicker)}">{content}</section>')


_SECTIONS = {
    'chat': ('SOURCE-BASED CONVERSATION', ('학과·졸업 통합 상담', 'Department & graduation advisor', '院系与毕业综合咨询', '学科・卒業総合相談'),
             ('학과와 졸업인증에 대해 물어보세요. 확인 가능한 근거와 추가 확인이 필요한 내용을 구분해 안내합니다.', 'Ask about your department and certification. See what the sources support and what still needs confirmation.', '询问院系与毕业认证，区分已有依据和仍需确认的信息。', '学科や卒業認証について質問し、根拠のある内容と追加確認が必要な内容を確認します。')),
    'pdf': ('ONE DOCUMENT, TRACEABLE ANSWERS', ('PDF 단독 RAG', 'PDF-only chat', '单一PDF问答', 'PDF単独チャット'),
            ('제공된 졸업인증 PDF만 근거로 검색합니다. 원문과 페이지를 함께 확인하세요.', 'Search only the supplied certification PDF and review its original wording and page.', '仅检索所提供的毕业认证PDF，核对原文与页码。', '提供された卒業認証PDFだけを検索し、原文とページを確認します。')),
    'multi': ('YOUR DOCUMENT LIBRARY', ('다중 문서 RAG', 'Multiple-document chat', '多文档问答', '複数文書チャット'),
              ('추가 PDF를 등록하고 문서별 근거를 비교하세요. 새로운 문서를 올려도 진단 규칙은 자동 변경되지 않습니다.', 'Add PDFs and compare evidence across sources. Uploading a document does not automatically change diagnostic rules.', '追加PDF并比较各文档依据，上传新文档不会自动修改诊断规则。', 'PDFを追加して出典ごとの根拠を比較します。追加資料で診断ルールが自動変更されることはありません。')),
    'diagnosis': ('YOUR CERTIFICATION PLAN', ('졸업요건 진단', 'Certification check', '毕业认证诊断', '卒業認証チェック'),
                  ('이수 과목과 공식 인정 활동을 입력하세요. 총점과 필수 항목, 영역별 기준을 함께 계산합니다.', 'Enter completed courses and officially recognized activities. Check totals, mandatory items and category requirements together.', '输入已完成课程与正式认定活动，同时核对总分、必修项目及领域要求。', '修得科目と正式認定活動を入力し、合計点・必須項目・分野別基準を確認します。')),
    'results': ('A CLEAR VIEW OF YOUR PROGRESS', ('나의 진단 결과', 'My certification results', '我的诊断结果', '自分の診断結果'),
                ('저장한 진단의 기준과 부족한 항목을 확인하세요. 입력을 바꿨다면 다시 계산해야 합니다.', 'Review the basis and missing items in your saved check. Recalculate after changing your inputs.', '核对保存结果的依据与未满足项目，修改输入后请重新计算。', '保存した診断の基準と不足項目を確認します。入力変更後は再計算してください。')),
    'evaluation': ('INSTRUCTOR REVIEW DESK', ('교수용 과제 평가', 'Instructor review', '教师评审', '教員向け課題確認'),
                   ('실제 학생 기록 없이 가상 사례로 질문·검색·진단 흐름을 확인합니다.', 'Review questions, retrieval and certification checks with synthetic cases, without accessing student records.', '使用虚拟案例核对问答、检索与诊断流程，不访问学生记录。', '学生の個人記録にアクセスせず、仮想事例で質問・検索・診断を確認します。')),
    'guide': ('KNOW YOUR DEPARTMENT', ('학과 안내', 'Department guide', '院系指南', '学科ガイド'),
              ('학과의 교육과정과 연락처를 확인하고, 졸업인증 점수와 교과 학점을 구분해 살펴보세요.', 'Review curriculum and contact references while keeping certification points distinct from academic credits.', '查看课程与联系方式，注意区分认证分数与课程学分。', '教育課程と連絡先を確認し、認証点数と修得単位を区別してください。')),
}
_ALIASES = {'학과·졸업 통합 상담': 'chat', 'PDF 단독 RAG': 'pdf', '다중 문서 RAG': 'multi', '졸업요건 진단': 'diagnosis', '진단 결과': 'results', '교수용 과제 평가': 'evaluation', '학과 안내': 'guide'}


def render_section(raw_st, lang, kind, department, year):
    """Section intro. ``kind`` accepts either a short key or the Korean menu name."""
    kind = _ALIASES.get(kind, kind)
    kicker, titles, descriptions = _SECTIONS.get(kind, _SECTIONS['chat'])
    title = _text(lang, *titles)
    description = _text(lang, *descriptions)
    cohort = _text(lang, f'{year}학번', f'{year} cohort', f'{year}级', f'{year}年度入学')
    profile = f'{tr(str(department), lang)} · {cohort}'
    _html(raw_st, f'<section class="sch-section-header" aria-label="{_esc(title)}"><div><div class="sch-eyebrow">{_esc(kicker)}</div><h2>{_esc(title)}</h2><p class="sch-description">{_esc(description)}</p></div><div class="sch-profile"><span class="sch-profile-dot" aria-hidden="true"></span><span>{_esc(profile)}</span></div></section>')


def _numeric(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        if not isfinite(value): return None
    except OverflowError:
        return None
    return value


def _number_label(value):
    number = _numeric(value)
    return f'{number:g}' if number is not None else '—'


def render_result_summary(raw_st, lang, result):
    """Show computed values only; never determine eligibility or change scores."""
    status = str(result.get('status', '확인 필요'))
    status_class = {'충족': 'met', '미충족': 'notmet'}.get(status, 'review')
    label = _text(lang, '입력 기준 · 다면적 졸업인증', 'INPUT-BASED CERTIFICATION SNAPSHOT', '基于输入的毕业认证概览', '入力に基づく卒業認証の状況')
    point_unit = _text(lang, '점', 'points', '分', '点')
    earned = _number_label(result.get('total_earned'))
    required = _number_label(result.get('total_required'))
    rows = []
    for area in result.get('areas', []):
        current = _numeric(area.get('earned'))
        target = _numeric(area.get('required'))
        ratio = max(0, min(100, current / target * 100)) if current is not None and target is not None and target > 0 else 0
        name = tr(str(area.get('area', '')), lang)
        score = f"{_number_label(area.get('earned'))} / {_number_label(area.get('required'))}"
        rows.append(f'<div class="sch-area"><div class="sch-area-label"><span>{_esc(name)}</span><strong>{_esc(score)}</strong></div><div class="sch-meter" aria-hidden="true"><div class="sch-meter-fill" style="width:{ratio:.2f}%"></div></div></div>')
    note = _text(lang, '사용자가 입력·확인한 내역에 따른 결과입니다. 최종 졸업 확정과 졸업학점은 공식 학사시스템에서 확인하세요.',
                 'Based on the records you entered and confirmed. Check final graduation and academic-credit requirements in the official university system.',
                 '结果依据您输入并确认的记录，最终毕业资格与学分要求请在正式教务系统核对。',
                 '入力・確認した記録に基づく結果です。最終的な卒業可否と必要単位は正式な学務システムで確認してください。')
    source = ''
    if result.get('source'):
        source_label = _text(lang, '근거', 'Source', '依据', '出典')
        source = f'<span class="sch-source-tag">{_esc(source_label)} · {_esc(result["source"])} · p.{_esc(result.get("page", "—"))}</span>'
    _html(raw_st, f'<section class="sch-result" aria-label="{_esc(label)}"><div class="sch-result-top"><div><div class="sch-eyebrow">{_esc(label)}</div><div class="sch-result-value">{_esc(earned)}<small>/ {_esc(required)} {_esc(point_unit)}</small></div></div><span class="sch-status sch-status-{status_class}">{_esc(tr(status, lang))}</span></div><div class="sch-result-areas">{"".join(rows)}</div><div class="sch-result-note">{_esc(note)}{source}</div></section>')
