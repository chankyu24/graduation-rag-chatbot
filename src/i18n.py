"""Offline interface glossary. Korean regulation names stay canonical in saved data."""
import re

LANGUAGES={'ko':'한국어','en':'English','zh':'简体中文','ja':'日本語'}
# Each value is English, Simplified Chinese, Japanese; Korean is the lookup key.
MESSAGES={
'교수용 기술 검증 · 고급 설정':('Instructor verification / advanced settings','教师技术验证／高级设置','教員向け技術検証・詳細設定'),
'답변 방식: 문서 근거 검색 · 생성형 AI 사용 안 함':('Answer mode: document search; generative AI is off','回答模式：文档依据检索，未使用生成式AI','回答モード：文書根拠検索・生成AIは未使用'),
'답변 방식: 생성형 AI · 문서 근거 확인 후 제공':('Answer mode: generative AI with source checks','回答模式：生成式AI，并核对文档依据','回答モード：文書根拠を確認した生成AI'),
'현재 학과·학번의 내 진단 결과를 기준으로 상담합니다. 입력하지 않은 활동을 완료로 가정하지 않습니다.':('Advice uses your results for this department and cohort. Unreported activities are not assumed complete.','咨询依据当前院系及入学年份的个人诊断，未输入的活动不会视为已完成。','現在の学科・入学年度の診断に基づく相談です。未入力の活動は完了と見なしません。'),
'진단 후 입력 또는 적용 기준이 변경되었습니다. 진단 메뉴에서 다시 계산해 주세요.':('Inputs or requirements changed after your check. Recalculate in Certification check.','诊断后输入或适用标准已变更，请重新诊断。','診断後に入力または適用基準が変わりました。診断メニューで再計算してください。'),
'졸업인증 기준':('Certification requirements','毕业认证标准','卒業認証の基準'),
'코딩인증 조건':('Coding certification','编程认证条件','コーディング認証の条件'),
'내 부족 항목':('My unmet requirements','我的不足项目','自分の不足項目'),
'자격증 인정':('Certificate recognition','资格证书认定','資格の認定'),
'내가 이수한 과목 중 인정되지 않은 과목은?':('Which of my entered courses were not recognized?','我输入的已修课程中哪些未获认定？','入力した履修科目のうち認定されていない科目は？'),
'순천향대 졸업 길잡이':('SCH Graduation Guide','顺天乡大学毕业指南','順天郷大学 卒業ガイド'),
'PDF 근거로 알아보고, 영역별 조건으로 준비하는 나의 졸업인증':('Check source-backed certification requirements and plan your next steps.','依据PDF核对毕业认证要求，规划下一步。','PDFの根拠で卒業認証要件を確認し、次の準備を進めましょう。'),
'로그인':('Sign in','登录','ログイン'),'회원가입':('Create account','注册','アカウント登録'),
'학번':('Student ID','学号','学籍番号'),'이름':('Name','姓名','氏名'),
'비밀번호':('Password','密码','パスワード'),'비밀번호 확인':('Confirm password','确认密码','パスワードの確認'),
'앱 전용 비밀번호':('App-only password','本应用专用密码','このアプリ専用パスワード'),
'학교 학사시스템과 연결되지 않은 과제용 앱 계정입니다. 학교 비밀번호를 사용하지 마세요.':('This classroom app uses independent accounts. Use a new password, not your university password.','本课程应用使用独立账户，未连接学校教务系统。请使用新密码，不要使用学校密码。','授業用アプリの独立アカウントです。大学のパスワードは使わず、新しいものを設定してください。'),
'앱 계정 만들기':('Create app account','创建应用账户','アプリ用アカウント作成'),
'계정을 만들었습니다. 로그인 탭에서 로그인해 주세요.':('Account created. Sign in using the Sign in tab.','账户已创建，请在登录页登录。','アカウントを作成しました。ログインタブからログインしてください。'),
'학번 또는 비밀번호가 올바르지 않습니다.':('Incorrect student ID or password.','学号或密码不正确。','学籍番号またはパスワードが正しくありません。'),
'비밀번호 확인이 일치하지 않습니다.':('Passwords do not match.','两次输入的密码不一致。','パスワードが一致しません。'),
'학번은 8~12자리 숫자로 입력하세요.':('Enter an 8–12 digit student ID.','学号须为8至12位数字。','学籍番号は8～12桁の数字で入力してください。'),
'앱 전용 비밀번호는 10~128자여야 합니다.':('Use an app-only password of 10–128 characters.','专用密码须为10至128个字符。','専用パスワードは10～128文字で入力してください。'),
'비밀번호에 영문과 숫자를 함께 넣어 주세요.':('Include both letters and numbers.','密码需包含英文字母和数字。','英字と数字の両方を含めてください。'),
'이미 등록된 학번입니다.':('This student ID is already registered.','该学号已注册。','この学籍番号は登録済みです。'),
'로그인 시도가 많습니다. 5분 후 다시 시도하세요.':('Too many attempts. Try again in five minutes.','尝试次数过多，请5分钟后重试。','試行回数が多すぎます。5分後に再試行してください。'),
'이름은 1~60자로 입력하세요.':('Enter a name of 1–60 characters.','姓名须为1至60个字符。','氏名は1～60文字で入力してください。'),
'로그아웃':('Sign out','退出登录','ログアウト'),'메뉴':('Menu','菜单','メニュー'),
'현재 비밀번호':('Current password','当前密码','現在のパスワード'),'새 비밀번호':('New password','新密码','新しいパスワード'),
'비밀번호 변경':('Change password','修改密码','パスワード変更'),
'현재 비밀번호가 올바르지 않습니다.':('Incorrect current password.','当前密码不正确。','現在のパスワードが正しくありません。'),
'비밀번호를 변경했습니다.':('Password changed.','密码已修改。','パスワードを変更しました。'),
'PDF 단독 RAG':('PDF-only chat','单一PDF问答','PDF単独チャット'),
'다중 문서 RAG':('Multiple-document chat','多文档问答','複数文書チャット'),
'졸업요건 진단':('Certification check','毕业认证诊断','卒業認証チェック'),
'진단 결과':('My results','诊断结果','診断結果'),'학과 안내':('Department guide','院系指南','学科ガイド'),
'대학교':('University','大学','大学'),'순천향대학교':('Soonchunhyang University','顺天乡大学','順天郷大学'),
'학과':('Department','院系','学科'),'입학연도 (학번 앞 4자리)':('Admission year (first four ID digits)','入学年份（学号前四位）','入学年度（学籍番号の先頭4桁）'),
'입학연도':('Admission year','入学年份','入学年度'),
'교육과정: 제공된 2026년도 학과기준 시안':('Curriculum: supplied 2026 department draft','依据：提供的2026年院系标准草案','基準：提供された2026年度学科基準案'),
'인증점수 ≠ 교과 이수학점':('Certification points ≠ academic credits','认证分数 ≠ 课程学分','認証点数 ≠ 修得単位'),
'검색 범위: ':('Search scope: ','检索范围：','検索範囲：'),
'제공 PDF 한 개':('Supplied PDF only','仅提供的PDF','提供PDFのみ'),'여러 PDF 통합':('All registered PDFs','全部已登记PDF','登録済みPDF全体'),
'다국어 임베딩 + FAISS':('Multilingual embeddings + FAISS','多语言嵌入 + FAISS','多言語埋め込み + FAISS'),
'LLM 답변 사용':('Use LLM answers','使用大模型回答','LLM回答を使用'),
'문서에 물어보세요':('Ask about the requirements','询问毕业要求','卒業要件を質問する'),
'현재 대화 지우기':('Clear this conversation','清除此对话','この会話を消去'),
'문서 등록 및 검색 상태':('Document registration and search status','文档登记及检索状态','文書登録・検索状況'),
'졸업기준 자료실':('Requirements library','毕业要求资料库','卒業要件ライブラリ'),
'PDF 추가':('Add PDF','添加PDF','PDFを追加'),'선택한 문서 등록':('Register selected files','登记所选文档','選択した文書を登録'),
'등록할 PDF를 선택해 주세요.':('Choose a PDF to register.','请选择需要登记的PDF。','登録するPDFを選択してください。'),
'이수한 과목 선택':('Select completed courses','选择已完成课程','修得済み科目を選択'),
'직접 입력 (한 줄에 한 과목)':('Enter courses (one per line)','手动输入（每行一门课程）','手入力（1行に1科目）'),
'수강 과목 CSV / XLSX':('Upload course list: CSV / XLSX','上传课程列表：CSV / XLSX','履修一覧：CSV / XLSX'),
'해당 영역에서 이수한 과목명':('Completed course in this category','该领域已完成课程名称','該当分野の修得済み科目名'),
'학사시스템에서 중핵교양 국제사회언어영역 이수 여부를 확인함':('I checked completion of the international-language core category in the university system.','已在教务系统确认核心通识国际社会语言领域的修读情况。','学務システムで中核教養・国際社会言語分野の修得状況を確認した。'),
'해당 인재상의 공식 인정 점수를 확인함':('I checked the official points in this competency category.','已确认该能力领域的正式认定分数。','この能力分野の正式な認定点数を確認した。'),
'취득한 PDF 권장 자격증':('Recommended certificates obtained (PDF list)','已取得的PDF推荐资格证书','取得済みのPDF推奨資格'),
'학사시스템의 필요 점수와 비교 (선택)':('Compare with university system requirements (optional)','与教务系统要求分数比较（可选）','学務システムの必要点数と比較（任意）'),
'이수 내역을 모두 입력했습니다. 미선택 항목은 미이수입니다.':('My record is complete. Unselected items are not completed.','已完整输入修读记录，未选择的项目视为未完成。','履修記録をすべて入力した。未選択の項目は未修得とする。'),
'나의 졸업인증 진단':('Check my certification','诊断我的毕业认证','卒業認証をチェック'),
'입력 저장':('Save my inputs','保存输入','入力を保存'),
'내 입력과 진단 결과를 저장했습니다.':('Inputs and results saved to your app account.','输入和诊断结果已保存至您的应用账户。','入力と診断結果をアプリアカウントに保存しました。'),
'저장한 입력을 불러왔습니다.':('Saved inputs restored.','已恢复保存的输入。','保存した入力を復元しました。'),
'다면적 졸업인증 충족 예상':('Certification requirements appear met','预计满足多维毕业认证要求','多面的卒業認証の要件を満たす見込み'),
'전체 졸업 가능 여부: 확인 필요 (졸업학점·기타 졸업요건 문서 미제공)':('Overall graduation eligibility: needs review (credit and other official rules not supplied).','总体毕业资格：需确认（尚缺毕业学分及其他正式规定）。','卒業全体の可否：要確認（卒業単位・その他の規程が未提供）。'),
'다음에 준비할 항목':('Next steps','接下来需要准备的项目','次に準備する項目'),
'나의 진단 결과':('My certification results','我的毕业认证结果','自分の認証結果'),
'진단 결과 JSON 다운로드':('Download results as JSON','下载JSON诊断结果','診断結果をJSONで保存'),
'현재 인증점수 / 필요점수':('Verified certification points / required','已确认认证分数 / 要求分数','確認済み認証点数 / 必要点数'),
'이 서비스는 다면적 졸업인증을 진단합니다. 최종 졸업 확정과 졸업학점은 학교 공식 학사시스템에서 확인하세요.':('This app checks certification requirements. Confirm final graduation and academic credits in the official university system.','本应用检查毕业认证要求。最终毕业资格与学分请在学校正式教务系统确认。','本アプリは卒業認証要件を確認します。最終的な卒業可否と単位は大学の正式な学務システムで確認してください。'),
'입력 내역 또는 기준 문서가 변경되었습니다. 아래는 지난 진단 결과입니다. 진단 메뉴에서 다시 계산해 주세요.':('Inputs or documents have changed. This is a previous result; run the check again.','输入或标准文档已变更。下方为旧结果，请重新诊断。','入力または基準文書が変更されました。以前の結果のため再計算してください。'),
'입력 내용이 지난 진단 이후 변경되었습니다. 결과를 다시 계산해 주세요.':('Inputs changed since the last check. Please recalculate.','上次诊断后输入已变更，请重新计算。','前回の診断後に入力が変わりました。再計算してください。'),
'API 키가 없어도 원문 근거를 검색합니다. 자연어 요약은 LLM 연결 시 제공됩니다.':('Source search works without an API key. LLM summaries are optional.','无需API密钥也可检索原文依据；连接大模型后可提供摘要。','APIキーなしでも原文を検索できます。LLM接続時に要約を利用できます。'),
'원문 과목명과 근거는 한국어로 함께 표시됩니다. 자유로운 답변 번역은 API 연결이 필요할 수 있습니다.':('Korean course names and source evidence are retained. Free-form answer translation may require an API.','同时保留韩文课程名和原文依据。自由问答翻译可能需要API连接。','韓国語の科目名と原文を併記します。自由な回答の翻訳にはAPI接続が必要な場合があります。'),
'PDF와 제공 학사화면의 차이':('PDF versus supplied university screenshots','PDF与所提供教务截图的差异','PDFと提供された学務画面の違い'),
'학과 홈페이지':('Department website','院系官网','学科ホームページ'),
'교육과정 안내':('Curriculum guide','课程设置','教育課程案内'),
'학과사무실: 041-530-1667 · 미디어랩스관 ML202':('Department office: 041-530-1667 · Media Labs ML202','院系办公室：041-530-1667 · Media Labs ML202','学科事務室：041-530-1667 · Media Labs ML202'),
}

GLOSSARY={
'AI·빅데이터학과':('AI and Big Data','AI与大数据系','AI・ビッグデータ学科'),
'컴퓨터소프트웨어공학과':('Computer Software Engineering','计算机软件工程系','コンピュータソフトウェア工学科'),
'정보보호학과':('Information Security','信息安全系','情報セキュリティ学科'),
'의료IT공학과':('Medical IT Engineering','医疗IT工程系','医療IT工学科'),
'사물인터넷학과':('Internet of Things','物联网系','IoT学科'),
'메타버스&게임학과':('Metaverse and Games','元宇宙与游戏系','メタバース・ゲーム学科'),
'대학공통':('University common','大学共同','大学共通'),
'비교과미지정':('Unspecified extracurricular','非指定课外活动','指定外課外活動'),
'비교과지정':('Designated extracurricular','指定课外活动','指定課外活動'),
'교과':('Curricular','课程','教科'),
'충족':('Met','满足','充足'),'미충족':('Not met','不满足','未充足'),'확인 필요':('Needs review','需确认','要確認'),
'인간사랑':('Love of Humanity','人间之爱','人間愛'),
'ASP(1,2학기)':('ASP (both semesters)','ASP（第一、二学期）','ASP（前期・後期）'),
'자기주도상담':('Self-directed counseling','自主咨询','自主相談'),
'봉사학습':('Service learning','志愿服务学习','奉仕学習'),
'자기개발과전공탐색(M&M)':('Self-development and major exploration (M&M)','自我发展与专业探索（M&M）','自己開発と専攻探索（M&M）'),
'자기개발과전공탐색':('Self-development and major exploration','自我发展与专业探索','自己開発と専攻探索'),
'졸업필수활동':('Mandatory graduation activities','毕业必修活动','卒業必須活動'),
'졸업종합지도':('Comprehensive graduation guidance','毕业综合指导','卒業総合指導'),
'졸업및취ㆍ창업지도':('Graduation and career/start-up guidance','毕业与就业创业指导','卒業・就職・起業指導'),
'현대기본영어':('Modern Basic English','现代基础英语','現代基礎英語'),
'현대실용영어':('Modern Practical English','现代实用英语','現代実用英語'),
'예비창업설계':('Pre-startup Design','创业预备设计','起業準備設計'),
'중핵교양 국제사회언어영역 택1':('One core general-education international-language course','核心通识国际社会语言领域课程选一','中核教養・国際社会言語分野から1科目'),
'코딩역량인증제 Level2 이상':('Coding competency certification Level 2 or higher','编程能力认证Level 2以上','コーディング能力認証Level 2以上'),
'AI·SW전공역량졸업인증제':('AI/SW major competency graduation certification','AI/SW专业能力毕业认证','AI・SW専攻能力卒業認証'),
'자격증/경진대회참가/경진대회수상':('Certificate / competition participation / competition award','资格证书／竞赛参加／竞赛获奖','資格／競技会参加／競技会入賞'),
'비교과자율활동(공감)':('Autonomous extracurricular (Empathy)','自主课外活动（共情）','自主課外活動（共感）'),
'비교과자율활동(창의)':('Autonomous extracurricular (Creativity)','自主课外活动（创造）','自主課外活動（創造）'),
'비교과자율활동(글로벌)':('Autonomous extracurricular (Global)','自主课外活动（全球）','自主課外活動（グローバル）'),
'학과활동':('Department activities','院系活动','学科活動'),'전공상담':('Major counseling','专业咨询','専攻相談'),
'경진대회 참가':('Competition participation','竞赛参加','競技会参加'),'경진대회 수상':('Competition award','竞赛获奖','競技会入賞'),
'공감':('Empathy','共情','共感'),'창의':('Creativity','创造','創造'),'글로벌':('Global','全球','グローバル'),
'공식 인정 점수':('officially recognized points','正式认定分数','正式認定点数'),
'공식 이수/인증 완료':('officially completed/certified','已正式修完／取得认证','正式に修得・認証済み'),
'필수 과목':('required courses','必修课程','必修科目'),
'학사시스템 필요 점수':('university-system required points','教务系统要求分数','学務システムの必要点数'),
'부족한 필수 항목: ':('Missing requirements: ','未满足的必修项目：','不足している必須項目：'),
'학번':('cohort','级','年度入学'),
'진단 시각: ':('Checked at: ','诊断时间：','診断日時：'),
'근거: ':('Source: ','依据：','出典：'),'합계':('Total','合计','合計'),
'필요 합계':('Total required','要求合计','必要合計'),
'원본 p.':('Source p.','原文第','原文 p.'),
'부족':('shortage','不足','不足'),'필요':('required','需要','必要'),
'회/학기당':('per participation/semester','每次／每学期','回・学期あたり'),
'최소':('minimum','最低','最低'),'레벨 또는 시험점수':('level or test score','等级或考试分数','レベルまたは試験点数'),
'점':(' points','分','点'),
}
COLUMNS={'area':('Category','领域','分野'),'required':('Required','要求分数','必要点数'),'earned':('Recognized','已认定','認定点数'),'shortage':('Shortage','不足分数','不足点数'),'status':('Status','状态','状態'),'name':('Item','项目','項目'),'detail':('Details','说明','詳細'),'action':('Next step','下一步','次の準備'),'remaining_count':('Remaining participations','剩余次数','残り回数')}


def tr(text,lang='ko'):
    if not isinstance(text,str) or lang=='ko': return text
    index={'en':0,'zh':1,'ja':2}.get(lang)
    if index is None: return text
    if text in MESSAGES: return MESSAGES[text][index]
    # Single-pass replacement prevents translating inside inserted translations.
    # Exact labels such as 학번 mean "Student ID"; inside "2022학번" the
    # glossary's cohort meaning applies instead.
    mapping={key:value[index] for key,value in {**MESSAGES,**GLOSSARY}.items()}
    pattern='|'.join(re.escape(key) for key in sorted(mapping,key=len,reverse=True))
    return re.sub(pattern,lambda match:mapping[match.group()],text)


def item_label(text,lang):
    translated=tr(text,lang)
    return text if translated==text else f'{translated} · {text}'


def table(rows,lang):
    if lang=='ko': return rows
    idx={'en':0,'zh':1,'ja':2}[lang]
    return [{COLUMNS.get(key,(key,key,key))[idx]:(item_label(value,lang) if key in {'name','course','department'} else value if key=='source' else tr(value,lang)) for key,value in row.items()} for row in rows]


class LocalizedUI:
    """Translate interface labels while keeping widget values and rule keys unchanged."""
    TEXT_METHODS={'title','subheader','header','caption','info','warning','error','success','markdown','write','button','download_button','text_input','text_area','file_uploader','number_input','checkbox','toggle','expander','chat_input','form_submit_button','metric','progress','link_button','spinner'}
    def __init__(self,ui,lang): self.ui,self.lang=ui,lang
    def __getattr__(self,name):
        attr=getattr(self.ui,name)
        if name=='sidebar': return LocalizedUI(attr,self.lang)
        if name in {'selectbox','multiselect','radio'}:
            def widget(label,options,*args,**kwargs):
                formatter=kwargs.pop('format_func',str)
                kwargs['format_func']=lambda value:item_label(formatter(value),self.lang)
                for key in ['help','placeholder']:
                    if key in kwargs: kwargs[key]=tr(kwargs[key],self.lang)
                return attr(tr(label,self.lang),options,*args,**kwargs)
            return widget
        if name=='text':
            def text(body,*args,**kwargs):
                # Chat responses and source text are already localized separately.
                # Only exact UI notices belong in this path; names/evidence stay intact.
                return attr(tr(body,self.lang) if isinstance(body,str) and body in MESSAGES else body,*args,**kwargs)
            return text
        if name in self.TEXT_METHODS:
            def call(*args,**kwargs):
                if args and isinstance(args[0],str):
                    label=item_label(args[0],self.lang) if name in {'checkbox','number_input'} and ' · ' in args[0] else tr(args[0],self.lang)
                    args=(label,)+args[1:]
                if name=='metric' and len(args)>1 and isinstance(args[1],str):
                    args=(args[0],tr(args[1],self.lang))+args[2:]
                for key in ['help','placeholder','text','label']:
                    if key in kwargs: kwargs[key]=tr(kwargs[key],self.lang)
                if name=='metric' and 'value' in kwargs: kwargs['value']=tr(kwargs['value'],self.lang)
                return attr(*args,**kwargs)
            return call
        return attr

MESSAGES.update({
'추천 질문':('Suggested question','推荐问题','おすすめの質問'),
'선택한 질문 보내기':('Ask selected question','发送所选问题','選択した質問を送信'),
'졸업인증 총점':('Total certification points','毕业认证总分','卒業認証の合計点'),
'학과활동 기준':('Department activity requirements','院系活动要求','学科活動の基準'),
'코딩역량인증제 조건':('Coding certification requirements','编程能力认证要求','コーディング認証の要件'),
'자격증 인정 점수':('Certificate recognition points','资格证书认定分数','資格の認定点数'),
'예: AI·빅데이터학과 2022학번 졸업인증 총점은?':('Example: What are the graduation requirements for 2022?','例如：2022级毕业认证要求是什么？','例：2022年の卒業認証要件を教えてください'),
'진단 실행 시 입력과 결과를 내 앱 계정에 저장합니다.':('Running a check saves your inputs and result to your app account.','运行诊断时，将输入和结果保存至您的应用账户。','診断を実行すると入力と結果をアカウントに保存します。'),
'저장된 수강 파일의 이수 과목을 사용합니다.':('Using the completed courses from your saved file.','正在使用已保存文件中的已修课程。','保存したファイルの修得済み科目を使用しています。'),
'저장된 업로드 과목 비우기':('Clear saved uploaded courses','清空已保存的上传课程','保存したアップロード科目を消去'),
'저장한 입력과 결과는 내 앱 계정으로 다시 불러옵니다. 채팅은 현재 로그인 세션에서만 유지됩니다.':('Saved inputs and results can be restored with your account. Chats last for the current login session.','保存的输入和结果可通过账户恢复。聊天仅在当前登录会话中保留。','保存した入力と結果はアカウントで復元できます。会話は現在のログイン中のみ保持します。'),
'과목명은 원문을 확인하세요.':('Check the original Korean course names.','请核对韩文原始课程名。','韓国語の原科目名を確認してください。'),
'처음에는 무료 모델 다운로드가 필요합니다. 끄면 인터넷 없는 원문 검색을 사용합니다.':('The free model downloads on first use. Turn this off for offline source search.','首次使用需下载免费模型。关闭后使用离线原文检索。','初回は無料モデルをダウンロードします。オフにするとオフライン原文検索を使います。'),
'벡터 인덱스 준비 중…':('Preparing vector index…','正在准备向量索引…','ベクトル索引を準備中…'),
'새 PDF는 검색에 반영됩니다. 진단 규칙은 원문 검수 후 JSON에 반영해야 합니다.':('New PDFs become searchable. Diagnosis rules need separate source review and JSON updates.','新PDF将加入检索。诊断规则需人工审核原文后更新JSON。','追加PDFは検索に反映されます。診断ルールは原文確認後にJSONへ別途登録します。'),
'띄어쓰기와 유니코드 정규화만 적용합니다. 다른 이름은 자동 인정하지 않습니다. 대학공통 항목은 공식 이수 여부로 체크하세요.':('Only spacing and Unicode normalization are applied. Different course names are not automatically recognized. Check university-common items against official completion records.','仅统一空格和Unicode，不自动认定不同课程名。大学共同项目请按正式修读记录勾选。','空白とUnicodeのみ正規化します。異なる科目名は自動認定しません。大学共通項目は正式な修得記録を確認してください。'),
'다른 값이 보이면 입력하세요. PDF 규칙을 덮어쓰지 않고 차이를 표시합니다.':('Enter different requirements shown in the university system. Differences are displayed without replacing PDF rules.','如教务系统要求不同，请输入。只显示差异，不覆盖PDF规则。','学務システムに異なる必要点数があれば入力してください。PDFルールを変更せず差を表示します。'),
'권장 자격증은 6점. 대회별 배점은 PDF에 없어 공식 인정 점수가 필요합니다. 참가·수상 중복 합산은 하지 않습니다.':('A recommended certificate earns 6 points. Competition-specific scores require official confirmation; participation and award points are not added together.','推荐资格证书为6分。各竞赛分数需正式确认，不重复累加参加与获奖分数。','推奨資格は6点です。大会別点数は正式な確認が必要です。参加と入賞の点数は重複合算しません。'),
'자율활동의 인재상별 공식 인정 점수 미확인':('Official points by competency category not confirmed','尚未确认各能力领域的正式认定分数','能力分野別の正式点数が未確認'),
'자율활동의 인재상별 공식 인정 점수만 입력하세요.':('Enter only officially recognized points for each category.','仅输入各领域正式认定分数。','分野ごとの正式認定点数のみ入力してください。'),
'PDF에는 활동별 배점이 없습니다. 학사시스템에 표시된 해당 인재상의 공식 인정 점수만 입력하세요.':('The PDF has no per-activity scoring table. Enter the official points for this category shown in the university system.','PDF没有各活动分值表，请输入教务系统显示的本领域正式认定分数。','PDFには活動別配点がありません。学務システムの該当分野の正式点数を入力してください。'),
'PDF에 개별 과목명이 없습니다. 수강 과목명과 해당 중핵교양 영역의 공식 이수 확인이 필요합니다.':('Individual course names are absent from the PDF. Provide the completed course and confirm its official core-category classification.','PDF未列具体课程名，请输入已修课程并确认其正式核心通识领域。','PDFに個別科目名はありません。修得科目名と正式な中核教養分野の確認が必要です。'),
'학과사무실: 041-530-1667 · 미디어랩스관 ML202':('Department office: 041-530-1667 · Media Labs ML202','院系办公室：041-530-1667 · Media Labs ML202','学科事務室：041-530-1667 · Media Labs ML202'),
'홈페이지 교육과정의 교과 학점은 PDF의 졸업인증 점수와 별개입니다. 적용 학번과 최신 확정 기준은 학과에 확인하세요.':('Website curriculum credits are separate from PDF certification points. Confirm your cohort and current final rules with the department.','官网课程学分与PDF认证分数不同，请向院系确认适用年级及最新正式标准。','ホームページの単位とPDFの認証点数は別です。適用年度と最新確定基準は学科に確認してください。'),
'2022학번 참고: 제공 PDF는 졸업필수활동 15점을 대학공통에, 제공된 개인 학사화면은 학과 졸업필수활동에 표시합니다. 자율활동 분류도 다릅니다. 이는 제공된 화면의 대조이며 모든 학생에게 적용되는 공식 변경 규정은 아닙니다.':('2022 cohort example: the supplied PDF lists 15 mandatory-graduation-activity points under university common, while the personal screenshot groups them under the department. Autonomous-activity categories also differ. This screenshot comparison is not a new university rule.','2022级示例：提供的PDF将毕业必修活动15分列入大学共同，个人教务截图列入院系，且自主活动分类也不同。这只是所提供截图的对照，不是新的正式规定。','2022年度入学の例：PDFは卒業必須活動15点を大学共通に、提供された個人画面は学科側に分類しています。自主活動の分類も異なります。画面の比較であり新しい正式規程ではありません。'),
'이 앱은 PDF 기준으로 계산합니다. 화면의 점수나 이수 이력은 자동 입력하지 않습니다. 차이가 있으면 진단 메뉴의 학사시스템 비교에 입력하고 학과에 확인하세요.':('Calculations follow the PDF. Screenshot points and records are not prefilled. Enter differences in the comparison panel and ask the department.','本应用按PDF计算，不预填截图分数或记录。如有差异，请在比较面板输入并向院系确认。','PDF基準で計算し、画面の点数や履歴は事前入力しません。相違は比較欄に入力し学科に確認してください。'),
'공식 홈페이지 확인일: 2026-11-05. 홈페이지 내용은 참고 링크이며 PDF 단독 검색 근거에는 포함하지 않습니다.':('Official website checked: 2026-11-05. Links are references and are excluded from PDF-only retrieval.','官网查看日期：2026-11-05。网页仅供参考，不纳入单一PDF检索依据。','公式サイト確認日：2026-11-05。参考リンクでありPDF単独検索には含めません。'),
})

GLOSSARY.update({
'데이터아키텍처전문가':('Data Architecture Professional','数据架构专家','データアーキテクチャ専門家'),
'SQL전문가':('SQL Professional','SQL专家','SQL専門家'),
'SQL개발자':('SQL Developer','SQL开发者','SQL開発者'),
'데이터분석전문가':('Data Analysis Professional','数据分析专家','データ分析専門家'),
'데이터분석준전문가':('Associate Data Analyst','数据分析准专家','データ分析準専門家'),
'빅데이터분석기사':('Big Data Analysis Engineer','大数据分析工程师','ビッグデータ分析技師'),
'다면적 졸업인증: ':('Certification: ','多维毕业认证：','多面的卒業認証：'),
'최소 기준':('Minimum requirement','最低标准','最低基準'),
'공식 이수 내역 없음':('No official completion record','无正式修读记录','正式な修得記録なし'),
'학사시스템 인정 점수에 대한 사용자 확인 기준':('Based on user-confirmed official university-system points','依据用户确认的教务系统正式分数','利用者が確認した学務システムの正式点数に基づく'),
'공식 영역 이수 확인: ':('Official category completion confirmed: ','已确认正式领域修读：','正式分野の修得確認：'),
'중핵교양 영역 확인과 이수 과목명 필요':('Provide a completed course and confirm its core category','需提供已修课程并确认核心通识领域','修得科目名と中核教養分野の確認が必要'),
'원문만으로 세부 인정 기준 판단 불가':('Detailed recognition rules cannot be determined from the source alone','仅凭原文无法确定详细认定规则','原文だけでは詳細な認定基準を判断できません'),
'입력 정보 확인 필요':('Input information needs review','输入信息需确认','入力情報の確認が必要'),
'입력 또는 공식 인정 내역을 확인하세요.':('Check your inputs or official recognition record.','请确认输入或正式认定记录。','入力または正式な認定記録を確認してください。'),
'필수 교과 이수 필요':('Required course must be completed','需完成必修课程','必修科目の修得が必要'),
'회(학기) 추가 필요':('additional participation(s)/semester(s) needed','还需参加次数／学期数','回・学期の追加が必要'),
'최소 레벨 또는 점수':('Minimum level or score','最低等级或分数','最低レベルまたは点数'),
'문서 근거 검색 결과':('Source-backed search results','基于文档依据的检索结果','文書根拠による検索結果'),
'적용':('Applies to','适用','適用'),
'교과 이수학점이 아닌 졸업인증 점수입니다.':('These are graduation-certification points, not course credits.','这是毕业认证分数，不是课程学分。','卒業認証点数であり、履修単位ではありません。'),
'권장 자격증 취득 6점: ':('Recommended certificate: 6 points. ','取得推荐资格证书：6分。','推奨資格取得：6点。'),
'문서 간 총점 불일치 발견: ':('Conflicting document totals: ','发现文档总分冲突：','文書間の合計点の不一致：'),
'나의 졸업인증':('My certification','我的毕业认证','自分の卒業認証'),
'졸업인증':('Graduation certification','毕业认证','卒業認証'),
'공통':('Common','共同','共通'),'인증':('Certification','认证','認証'),
'영역':('Category','领域','分野'),'인재상':('Competency','能力','能力'),
'학기당':('per semester','每学期','学期あたり'),'회당':('per participation','每次','1回あたり'),
'검색 가능':('searchable','可检索','検索可能'),
})

MESSAGES.update({
'접속 유형':('Access type','访问类型','利用区分'),
'학생':('Student','学生','学生'),
'교수·평가자':('Instructor / Evaluator','教师／评估者','教員・評価者'),
'교수·평가자 (과제 확인용)':('Instructor / Evaluator (assignment review)','教师／评估者（作业评审）','教員・評価者（課題確認用）'),
'평가용 아이디':('Evaluator username','评估用用户名','評価用ユーザー名'),
'검토할 입학연도':('Cohort to review','待评估入学年份','確認する入学年度'),
'학번 없이 평가용 아이디로 가입합니다. 교수 신분을 인증하거나 학생 기록을 열람하는 계정은 아닙니다.':('Register with an evaluator username; no student ID required. This does not verify instructor identity or grant access to student records.','使用评估用户名注册，无需学号。不验证教师身份，也不授予学生记录访问权。','学籍番号なしで評価用IDを登録できます。教員の本人認証や学生記録の閲覧権限はありません。'),
'아이디 또는 비밀번호가 올바르지 않습니다.':('Incorrect username or password.','用户名或密码不正确。','ユーザー名またはパスワードが正しくありません。'),
'계정을 만들었습니다. 왼쪽 로그인 입력란에서 로그인해 주세요.':('Account created. Sign in using the form on the left.','账户已创建，请在左侧登录。','アカウントを作成しました。左のフォームでログインしてください。'),
'이미 등록된 평가용 아이디입니다.':('Evaluator username already registered.','评估用户名已注册。','この評価用IDは登録済みです。'),
'평가용 아이디는 영문으로 시작하는 4~40자 영문·숫자·밑줄·점·하이픈으로 입력하세요.':('Use 4–40 characters starting with a letter: letters, numbers, underscore, dot or hyphen.','用户名须以英文字母开头，长度4至40，可用字母、数字、下划线、点或连字符。','英字で始まる4～40文字で、英数字・下線・点・ハイフンを使用してください。'),
'교수용 과제 평가':('Assignment evaluation','作业评估','教員用課題評価'),
'가상 평가 사례':('Synthetic evaluation case','虚拟评估案例','架空の評価ケース'),
'가상 사례 실행':('Run synthetic case','运行虚拟案例','架空ケースを実行'),
'빈 기록':('Empty record','空白记录','空の記録'),
'일부 과목만 이수':('Only some courses completed','仅完成部分课程','一部の科目のみ修得'),
'확인 가능한 조건 충족':('All verifiable conditions met','满足全部可确认条件','確認可能な条件を充足'),
'필수 과목 누락':('Missing required course','缺少必修课程','必修科目が不足'),
'자율활동 점수 부족':('Insufficient autonomous-activity points','自主活动分数不足','自主活動の点数が不足'),
'이수 정보 미확인':('Unconfirmed completion records','修读信息未确认','修得情報が未確認'),
'이 화면은 가상 사례를 이용한 과제 확인용입니다. 실제 학생의 개인 기록을 불러오거나 저장하지 않습니다.':('This assignment-review page uses synthetic cases. It neither loads nor saves real student records.','此作业评审页面使用虚拟案例，不读取或保存真实学生记录。','課題確認用の架空ケースです。実際の学生記録を読み込み・保存しません。'),
'PDF 단독 RAG 메뉴에서 직접 질문하거나 아래 가상 사례로 영역별 판정을 확인하세요.':('Ask questions in PDF-only chat or inspect category decisions with the cases below.','可在单一PDF问答中提问，或用以下案例查看各领域判定。','PDF単独チャットで質問するか、以下のケースで分野別判定を確認してください。'),
'가상 결과는 학생별 저장 기록이나 실제 졸업 판정에 반영되지 않습니다.':('Synthetic results do not affect saved student records or actual graduation decisions.','虚拟结果不影响学生保存记录或实际毕业判定。','架空の結果は学生の保存記録や実際の卒業判定に反映されません。'),
})

MESSAGES.update({
'학과·졸업 통합 상담':('Department and graduation advisor','院系与毕业综合咨询','学科・卒業総合相談'),
'학과·졸업 통합':('Department and graduation sources','院系与毕业综合资料','学科・卒業総合資料'),
'근거 원문 보기':('View original evidence','查看原文依据','原文の根拠を表示'),
'자유롭게 질문하세요. 학과·학번에 맞는 근거를 찾고, 자료에 없는 내용은 필요한 확인 자료를 안내합니다.':('Ask in your own words. Answers use department/cohort evidence and explain missing sources.','请自由提问。回答依据院系及入学年份资料，缺少信息时说明需确认的材料。','自由な表現で質問できます。学科・入学年度の根拠を使い、不足する資料を案内します。'),
'현재 근거: 졸업인증 PDF + 확인한 학과 홈페이지 교육과정·연락처. 전체 졸업학점 확정 규정은 미제공입니다.':('Sources: certification PDF plus reviewed department curriculum/contact pages. Final graduation-credit regulations are not supplied.','依据：毕业认证PDF及已核对的院系课程和联系方式。尚缺最终毕业学分规定。','根拠：卒業認証PDFと確認済み学科教育課程・連絡先。卒業単位の確定規程は未提供です。'),
})

# Professor review, current search mode and upload/input validation notices.
MESSAGES.update({
'교수님: 가입 없이 실제 챗봇 확인':('Instructor: open the actual chatbot without registering','教师：无需注册，打开实际聊天机器人','教員の方：登録せず実際のチャットボットを確認'),
'평가용 입구에서도 원본 Python의 PDF 검색·추가 업로드·진단을 사용할 수 있습니다. 학생 기록에 접근하지 않으며 입력은 이 세션에서만 유지됩니다.':('The review entry provides the original Python PDF search, additional uploads and checks. It cannot access student records; inputs remain in this session only.','评审入口也可使用原始Python的PDF检索、追加上传及诊断。不能访问学生记录，输入仅在本次会话中保留。','確認用入口でも元のPythonによるPDF検索・追加アップロード・診断を利用できます。学生記録にはアクセスせず、入力はこのセッション内だけで保持します。'),
'교수·평가자 · 가입 없는 확인':('Instructor / Evaluator · no registration','教师／评估者 · 无需注册','教員・評価者 · 登録不要'),
'업로드와 입력은 현재 세션 전용입니다. 체험 종료 시 파일을 정리합니다.':('Uploads and inputs belong to this session only. Files are removed when you end the review.','上传文件和输入仅用于当前会话，结束体验时清理文件。','アップロードと入力は現在のセッション専用です。体験終了時にファイルを削除します。'),
'체험 종료':('End review','结束体验','体験を終了'),
'제공 PDF 다운로드':('Download supplied PDF','下载提供的PDF','提供PDFをダウンロード'),
'제공 PDF는 공통 자료입니다. 추가 업로드는 현재 앱 계정에만 저장되며 다른 계정 검색에 포함되지 않습니다.':('The supplied PDF is shared reference material. Additional uploads belong to the current app account and are excluded from other accounts’ searches.','提供的PDF是公共参考资料。追加上传仅属于当前应用账户，不会出现在其他账户的检索结果中。','提供PDFは共通資料です。追加アップロードは現在のアプリアカウント専用で、他のアカウントの検索には含まれません。'),
'**1. PDF 질문·답변 / 2. 수강 목록과 활동 입력 / 3. 규칙 기반 진단**':('**1. PDF questions and answers / 2. Course and activity input / 3. Rule-based checks**','**1. PDF问答／2. 输入课程列表及活动／3. 基于规则的诊断**','**1. PDFへの質疑応答 / 2. 履修一覧と活動の入力 / 3. ルールに基づく診断**'),
'**교수님 확인 순서**\n1. 왼쪽에서 PDF 단독 RAG를 선택해 질문하고 출처를 확인합니다.\n2. 다국어 임베딩 + FAISS를 켜 실제 벡터 검색을 확인합니다.\n3. 다중 문서 RAG에서 별도 PDF를 등록한 뒤 새 문서 내용으로 질문합니다.\n4. 졸업요건 진단에서 수강 CSV/XLSX와 활동을 입력하고 부족한 항목을 확인합니다.':('**Instructor review steps**\n1. Select PDF-only chat on the left, ask a question and check its source.\n2. Enable Multilingual embeddings + FAISS to inspect actual vector retrieval.\n3. Register another PDF in Multiple-document chat and ask about that document.\n4. In Certification check, enter a course CSV/XLSX and activities, then inspect unmet requirements.','**教师确认步骤**\n1. 在左侧选择单一PDF问答，提问并核对出处。\n2. 开启多语言嵌入 + FAISS，确认实际向量检索。\n3. 在多文档问答中登记其他PDF，再提问新文档内容。\n4. 在毕业认证诊断中输入课程CSV/XLSX及活动，查看不足项目。','**教員の確認手順**\n1. 左側でPDF単独チャットを選び、質問と出典を確認します。\n2. 多言語埋め込み + FAISSをオンにして実際のベクトル検索を確認します。\n3. 複数文書チャットで別のPDFを登録し、新しい文書について質問します。\n4. 卒業認証チェックで履修CSV/XLSXと活動を入力し、不足項目を確認します。'),
'이 화면은 간편 HTML이 아니라 원본 Python 프로그램입니다. API 키 없이 검색·계산을 사용할 수 있으며, 생성형 답변은 별도 API 설정이 필요합니다.':('This is the original Python program, rather than the simplified HTML preview. Search and calculation work without an API key; generated answers require separate API settings.','此页面运行原始Python程序，并非简易HTML预览。检索及计算无需API密钥；生成式回答需另行设置API。','この画面は簡易HTMLではなく元のPythonプログラムです。検索・計算はAPIキーなしで利用でき、生成回答には別途API設定が必要です。'),
'평가자 계정으로 로그인해 주세요.':('Sign in with an evaluator account.','请使用评估者账户登录。','評価者アカウントでログインしてください。'),
'체험 입력과 결과는 현재 세션에서만 유지됩니다.':('Review inputs and results remain in this session only.','体验输入和结果仅在当前会话中保留。','体験中の入力と結果は現在のセッション内だけで保持します。'),
'체험 결과는 현재 세션에서만 유지됩니다.':('Review results remain in this session only.','体验结果仅在当前会话中保留。','体験の結果は現在のセッション内だけで保持します。'),
'체험 입력과 진단 결과는 현재 세션에서만 유지됩니다.':('Review inputs and check results remain in this session only.','体验输入和诊断结果仅在当前会话中保留。','体験中の入力と診断結果は現在のセッション内だけで保持します。'),
'다국어 벡터 인덱스 준비 중…':('Preparing multilingual vector index…','正在准备多语言向量索引…','多言語ベクトル索引を準備中…'),
'요청됨 (API 키·응답 검증 필요)':('Requested (API key and response validation required)','已请求（需要API密钥及回答验证）','要求済み（APIキーと回答検証が必要）'),
'검수된 기준표·키워드 검색':('Reviewed requirements and keyword search','已审核标准表及关键词检索','確認済み基準表・キーワード検索'),
'다국어 임베딩·FAISS':('Multilingual embeddings / FAISS','多语言嵌入／FAISS','多言語埋め込み・FAISS'),
'사용 안 함':('Off','未使用','使用しない'),
'해당 학과·학번 기준이 없습니다. 문서를 추가해 주세요.':('No requirements are available for this department and cohort. Add the relevant document.','没有该院系及入学年份的标准，请添加相应文档。','該当学科・入学年度の基準がありません。対応する文書を追加してください。'),
'로그인한 계정이 필요합니다.':('A signed-in account is required.','需要已登录的账户。','ログイン済みのアカウントが必要です。'),
'PDF는 0바이트 초과 30MB 이하여야 합니다.':('PDF files must be larger than zero bytes and no larger than 30 MB.','PDF须大于0字节且不超过30MB。','PDFは0バイトより大きく30MB以下にしてください。'),
'PDF 확장자가 필요합니다.':('The file must have a PDF extension.','文件必须使用PDF扩展名。','PDF拡張子が必要です。'),
'텍스트 없음: OCR 필요':('No extractable text: OCR required','无可提取文本：需要OCR','抽出可能なテキストなし：OCRが必要'),
'PDF를 읽을 수 없습니다. 파일 손상 여부를 확인하세요.':('Cannot read the PDF. Check whether the file is damaged.','无法读取PDF，请检查文件是否损坏。','PDFを読み取れません。ファイルの破損を確認してください。'),
'암호화된 PDF는 지원하지 않습니다.':('Encrypted PDFs are not supported.','不支持加密PDF。','暗号化されたPDFには対応していません。'),
'추출 가능한 텍스트가 없습니다. OCR 처리 후 등록하세요.':('No extractable text was found. Apply OCR before registering the PDF.','未找到可提取文本，请先进行OCR再登记PDF。','抽出できるテキストがありません。OCR処理後に登録してください。'),
'CSV는 5MB 이하여야 합니다.':('CSV files must be no larger than 5 MB.','CSV不得超过5MB。','CSVは5MB以下にしてください。'),
'XLSX는 5MB 이하여야 합니다.':('XLSX files must be no larger than 5 MB.','XLSX不得超过5MB。','XLSXは5MB以下にしてください。'),
'CSV 또는 XLSX 파일만 지원합니다.':('Only CSV and XLSX files are supported.','仅支持CSV和XLSX文件。','CSVまたはXLSXのみに対応しています。'),
'CSV에 과목명, 이수여부 열이 필요합니다.':('CSV requires the Korean columns 과목명 (course name) and 이수여부 (completion).','CSV需要韩文列名 과목명（课程名）和 이수여부（是否修完）。','CSVには韓国語の列名 과목명（科目名）と 이수여부（修得状況）が必要です。'),
'CSV 열 이름은 비어 있거나 중복될 수 없습니다. 띄어쓰기만 다른 열도 중복입니다.':('CSV column names must be nonempty and unique. Differences in spacing do not make names distinct.','CSV列名不能为空或重复，仅空格不同也视为重复。','CSVの列名は空欄や重複にできません。空白だけが異なる列名も重複です。'),
'CSV 따옴표 또는 행 형식이 올바르지 않습니다. CSV 형식으로 다시 저장해 주세요.':('Invalid CSV quoting or row format. Save the file as CSV again.','CSV引号或行格式不正确，请重新保存为CSV。','CSVの引用符または行形式が正しくありません。CSV形式で保存し直してください。'),
'XLSX 처리에는 openpyxl과 pandas 설치가 필요합니다.':('XLSX processing requires openpyxl and pandas.','处理XLSX需要安装openpyxl和pandas。','XLSXの処理にはopenpyxlとpandasが必要です。'),
'XLSX 파일을 읽을 수 없습니다. 첫 시트의 양식과 파일 손상을 확인하세요.':('Cannot read the XLSX file. Check the first sheet’s format and file integrity.','无法读取XLSX，请检查首个工作表格式及文件是否损坏。','XLSXを読み取れません。最初のシートの形式とファイルの破損を確認してください。'),
'압축 해제 크기가 너무 큰 XLSX입니다.':('The XLSX file is too large when decompressed.','XLSX解压后的大小过大。','XLSXの展開後サイズが大きすぎます。'),
'CSV를 UTF-8 또는 CP949로 저장해 주세요.':('Save the CSV using UTF-8 or CP949.','请使用UTF-8或CP949保存CSV。','CSVをUTF-8またはCP949で保存してください。'),
'입학연도는 정수로 입력하세요.':('Enter the admission year as an integer.','入学年份须为整数。','入学年度は整数で入力してください。'),
'수강 과목은 과목명 문자열 목록으로 입력하세요.':('Provide the courses as a list of course-name strings.','课程须以课程名称字符串列表输入。','履修科目は科目名文字列の一覧で入力してください。'),
'학사시스템 필요 점수는 영역별 사전이어야 합니다.':('University-system requirements must be a category-to-points mapping.','教务系统要求分数须按领域与分数对应输入。','学務システムの必要点数は分野と点数の対応で入力してください。'),
'활동과 증빙 정보는 이름별 사전이어야 합니다.':('Activities and evidence must be mapped by item name.','活动及证明信息须按项目名称对应输入。','活動と証明情報は項目名ごとの対応で入力してください。'),
'입력 완료 여부는 참/거짓이어야 합니다.':('Input-complete status must be true or false.','输入完成状态须为真或假。','入力完了の状態は真または偽にしてください。'),
'해당 학과·학번 기준 없음':('No requirements for this department and cohort','没有该院系及入学年份的标准','該当学科・入学年度の基準がありません'),
'선택 필수 과목의 유사 명칭이 있습니다. 동일 과목 여부 확인 필요; 자동 인정하지 않음':('A similar required-course name was found. Confirm equivalence; it is not automatically accepted.','发现相似的必修课程名，需确认是否为同一课程，不自动认定。','選択必修科目に似た名称があります。同一科目か確認が必要で、自動認定はしません。'),
'다른 필수 교과와 동일 과목을 중복 배정할 수 없습니다. 공식 교과 영역 확인 필요':('The same course cannot fill another required-course slot. Confirm its official category.','同一课程不能重复计入另一必修项目，需确认正式课程领域。','同一科目を別の必修項目に重複登録できません。正式な教科分野の確認が必要です。'),
'목록 외 자격증은 자동 인정하지 않습니다.':('Certificates outside the list are not automatically accepted.','不自动认定列表外资格证书。','リスト外の資格は自動認定しません。'),
'대회별 배점이 없으므로 공식 인정 점수 확인 필요':('Competition-specific scores are not provided; confirm the officially recognized points.','未提供各竞赛配分，需确认正式认定分数。','大会別配点がないため、正式な認定点数の確認が必要です。'),
'PDF 권장 자격증 취득 6점':('PDF-recommended certificate obtained: 6 points','取得PDF推荐资格证书：6分','PDF推奨資格の取得：6点'),
'전공영어 대체과목은 원문 각주에 있으나 조합별 인정은 학과 확인 필요':('Major-English substitutes appear in the source footnotes, but accepted combinations require department confirmation.','原文脚注列有专业英语替代课程，但认可的组合需向院系确认。','専攻英語の代替科目は原文の脚注にありますが、組み合わせの認定は学科への確認が必要です。'),
'2016~2021 전공영어 대체 인정은 학과 확인 필요':('For 2016–2021 cohorts, major-English substitutions require department confirmation.','2016至2021级的专业英语替代认定需向院系确认。','2016～2021年度入学の専攻英語の代替認定は学科への確認が必要です。'),
'자율활동은 인재상별 배분 및 중복인정 확인 필요':('Review competency-category allocation and overlapping recognition of autonomous activities.','自主活动需确认能力领域分配及重复认定。','自主活動の能力分野別配分と重複認定を確認する必要があります。'),
'공인어학 점수별 인정·자율활동 중복 및 인재상 배분 확인 필요':('Review language-score recognition, overlapping autonomous activities and competency-category allocation.','需确认语言考试各分数的认定、自主活动重复认定及能力领域分配。','公認語学の点数別認定、自主活動の重複と能力分野別配分の確認が必要です。'),
'TOPCIT 수준별 표와 5점 세부배점표의 적용 관계 및 자율활동 세부인정 확인 필요':('Review how the TOPCIT level table relates to the detailed 5-point table, and confirm detailed recognition of autonomous activities.','需确认TOPCIT等级表与5分详细配分表的适用关系及自主活动的具体认定。','TOPCITの水準表と5点の詳細配点表の適用関係、および自主活動の詳細認定を確認する必要があります。'),
'제공 PDF의 다면적 졸업인증만 진단. 사용자 입력·공식 인정 확인을 전제로 하며 졸업학점과 최종 졸업 확정은 학사시스템에서 확인하세요.':('Only the supplied PDF’s graduation certification is checked, based on user inputs and confirmed official recognition. Confirm graduation credits and final eligibility in the university system.','仅诊断所提供PDF的多维毕业认证，以用户输入和正式认定确认情况为前提。毕业学分和最终毕业资格请在教务系统确认。','提供PDFの多面的卒業認証だけを診断します。利用者の入力と正式認定の確認を前提とし、卒業単位と最終的な卒業可否は学務システムで確認してください。'),
})

GLOSSARY.update({
'학번':(' cohort','级','年度入学'),
'현재 검색: ':('Current search: ','当前检索：','現在の検索：'),
' / 생성형 답변: ':(' / Generated answers: ','／生成式回答：',' / 生成回答：'),
'벡터 검색 준비 실패. 원문 검색 사용: ':('Vector search could not start; using source search: ','向量检索准备失败，改用原文检索：','ベクトル検索の準備に失敗しました。原文検索を使用：'),
'문서 읽기 오류 · ':('Document read error · ','文档读取错误 · ','文書読み取りエラー · '),
'페이지 검색 가능':('page(s) searchable','页可检索','ページを検索可能'),
'등록 완료':('Registered','登记完成','登録完了'),
'학번의 진단 결과가 없습니다. 진단 메뉴에서 내역을 입력해 주세요.':('cohort has no results. Enter records in Certification check.','级暂无诊断结果，请在诊断菜单输入记录。','年度入学の診断結果がありません。診断メニューで記録を入力してください。'),
' — 세부 기준 확인 필요':(' — Detailed rules need review',' — 需确认详细标准',' — 詳細基準の確認が必要'),
'의 학교 공식 인정 점수를 확인함':('official university points confirmed','已确认学校正式认定分数','大学の正式な認定点数を確認した'),
' (없으면 0, 범위 ':(' (0 if none; range ','（无则填0，范围','（該当なしは0、範囲'),
': 0 이상의 점수를 입력하세요.':(': Enter points of zero or above.', '：请输入不小于0的分数。','：0以上の点数を入力してください。'),
'행: CSV 열 수가 일치하지 않습니다.':(': CSV column counts do not match.', '行：CSV列数不一致。','行：CSVの列数が一致しません。'),
'행: 이수여부 값 ':(': completion value ','行：修读状态值','行：修得状況の値'),
'을 확인하세요.':('needs review.','请确认。','を確認してください。'),
'행: 과목명이 비어 있습니다.':(': Course name is empty.','行：课程名为空。','行：科目名が空です。'),
'증빙 정보는 사전이어야 합니다.':('Evidence must be an item mapping.','证明信息须按项目对应输入。','証明情報は項目ごとの対応にしてください。'),
'자격증은 이름 목록이어야 합니다.':('Certificates must be a list of names.','资格证书须为名称列表。','資格は名称の一覧にしてください。'),
'이수 과목명은 문자열이어야 합니다.':('The completed course name must be text.','已修课程名须为文本。','修得科目名は文字列にしてください。'),
'확인 여부는 참/거짓이어야 합니다.':('Confirmation must be true or false.','确认状态须为真或假。','確認の状態は真または偽にしてください。'),
'0 이상의 유한한 숫자가 필요합니다.':('A finite number of zero or above is required.','需要不小于0的有限数值。','0以上の有限数が必要です。'),
'정수 횟수가 필요합니다.':('A whole-number count is required.','次数须为整数。','回数は整数にしてください。'),
'2019학번 이전 대학공통 세부 기준 없음':('University-common details for cohorts before 2019 are unavailable','没有2019级以前的大学共同详细标准','2019年度入学より前の大学共通詳細基準がありません'),
'유사 과목명 ':('Similar course name: ','相似课程名：','類似科目名：'),
'의 동일 과목 여부 확인 필요; 자동 인정하지 않음':('requires an equivalence check; not automatically accepted','需确认是否为同一课程，不自动认定','との同一科目の確認が必要。自動認定しません'),
'와 동일 과목인지 확인 필요; 자동 인정하지 않음':('requires a course-equivalence check; not automatically accepted','需确认是否为同一课程，不自动认定','との同一科目の確認が必要。自動認定しません'),
'알 수 없는 영역: ':('Unknown category: ','未知领域：','不明な分野：'),
'세부 규칙 합계가 영역 필요 점수보다 작음':('Detailed-item totals are below the category requirement','详细项目合计低于领域要求分数','詳細項目の合計が分野の必要点数未満です'),
'기준 차이 확인 필요':('Review the differing requirements','需确认标准差异','基準の相違を確認する必要があります'),
'입력한 학사시스템 필요 ':('entered university requirement ','输入的教务系统要求','入力した学務システムの必要点数'),
'인정 점수는 ':('recognized points must be ','认定分数须为','認定点数は'),
' 범위여야 합니다.':(' within the allowed range.','，并在允许范围内。','の範囲内にしてください。'),
'이수/인증 여부는 참·거짓 또는 0·1이어야 합니다.':('Completion/certification must be true/false or 0/1.','修读／认证状态须为真／假或0／1。','修得・認証の状態は真・偽または0・1にしてください。'),
})


MESSAGES.update({
'가입 없이 챗봇 시작':('Start without an account','无需注册，开始使用','登録せずに始める'),
'교수님도 학생도 가입 없이 PDF 질문과 진단을 체험할 수 있습니다. 입력은 현재 세션에만 유지됩니다.':('Instructors and students can try PDF questions and certification checks without registering. Inputs stay in this session only.','教师和学生均可无需注册体验PDF问答与认证诊断。输入仅在当前会话保留。','教員も学生も登録なしでPDFへの質問と認証チェックを体験できます。入力は現在のセッション内のみ保持します。'),
'개인 기록을 저장하려면 로그인·회원가입':('Sign in or create an account to save your records','登录或注册以保存个人记录','記録を保存するにはログイン・登録'),
'PDF에 질문하기':('Ask the PDF','向PDF提问','PDFに質問する'),
'문서 추가하기':('Add documents','添加文档','文書を追加する'),
'내 졸업인증 진단':('Check my progress','诊断我的认证进度','自分の認証状況を確認'),
'처음 오셨나요? 사용 순서 보기':('First visit? See how it works','首次使用？查看操作步骤','初めての方へ：使い方を見る'),
'문서에서 근거를 확인하고 있어요…':('Checking the source documents…','正在核对文档依据…','文書の根拠を確認しています…'),
})

MESSAGES.update({
'학과·학번':('Department / cohort','院系及入学年份','学科・入学年度'),
'수강 과목':('Courses','修读课程','履修科目'),
'활동·인정 정보':('Activities / recognition','活动及认定','活動・認定情報'),
'진단 실행':('Run check','运行诊断','診断実行'),
'결과·상담':('Results / advice','结果及咨询','結果・相談'),
'진단 진행 단계':('Certification workflow','认证诊断步骤','認証チェックの手順'),
'입력 수정하기':('Edit my inputs','修改输入','入力を修正'),
'진단 결과로 상담하기':('Discuss my results','咨询诊断结果','診断結果について相談'),
'진단 결과 CSV 다운로드':('Download results as CSV','下载CSV诊断结果','診断結果をCSVで保存'),
'샘플 수강 CSV 다운로드':('Download sample course CSV','下载示例课程CSV','履修CSVサンプルを保存'),
'샘플 수강 XLSX 다운로드':('Download sample course XLSX','下载示例课程XLSX','履修XLSXサンプルを保存'),
'가상 추가 PDF 다운로드':('Download synthetic demo PDF','下载合成演示PDF','架空デモPDFを保存'),
'1. 학과·학번 확인':('1. Confirm department / cohort','1. 确认院系及入学年份','1. 学科・入学年度を確認'),
'2. 수강 과목 입력':('2. Enter completed courses','2. 输入修读课程','2. 履修科目を入力'),
'3. 활동·공식 인정 정보 입력':('3. Enter activities / official recognition','3. 输入活动及正式认定','3. 活動・正式認定を入力'),
'4. 입력 확인 후 진단':('4. Review inputs and run check','4. 确认输入后诊断','4. 入力を確認して診断'),
'5. 부족 조건 확인 및 상담':('5. Review missing requirements / ask for advice','5. 查看不足并咨询','5. 不足要件を確認して相談'),
'가상 시연 입력 결과입니다. 실제 학생 이수 내역이나 학교의 승인 결과가 아닙니다.':('Synthetic demonstration inputs. These are not actual student records or university approval.','此结果来自合成演示输入，并非实际学生记录或学校审批。','架空のデモ入力による結果です。実際の履修記録や大学の承認ではありません。'),
})
