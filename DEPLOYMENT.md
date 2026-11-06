# 교수님이 실제 원본 챗봇을 확인하는 방법

## 구현과 공개 상태 구분

기존 chatgpt.site 주소와 교수님_확인.html은 JavaScript 간편 체험입니다. 실제 Python·FAISS RAG 서버로 게시된 주소가 아닙니다. 원본 Python 앱에 가입 없는 교수 평가 입구를 추가했으므로 실제 서버를 게시하면 교수님은 학생 계정 없이 전 기능을 확인할 수 있습니다.

## 준비한 배포 파일

- Dockerfile: Python 3.12, CPU PyTorch, 동일 원본 앱을 실행합니다.
- deploy.py: 호스팅의 PORT 환경변수를 받아 0.0.0.0에서 Streamlit을 시작합니다.
- render.yaml: 무료 플랜의 검토용 템플릿입니다. 아직 Render 서버가 생성·게시되었다는 의미가 아닙니다.
- .dockerignore 및 명시적 COPY: 비밀번호·개인 DB·로컬 인덱스·중첩 옛 프로젝트를 서버 이미지에 포함하지 않습니다.

현재 환경에는 Docker가 없어 컨테이너 빌드는 미검증입니다. Linux CPU 휠 설치·모델 다운로드·호스팅 메모리 제한은 서버 빌드와 실제 배포 후 검증해야 합니다. 검토 없이 유료 플랜으로 전환하지 않습니다.

## Render에 게시할 때

1. 프로젝트를 GitHub 저장소 루트에 올립니다. .env와 .local, 기존 학생 기록은 포함하지 않습니다.
2. Render에서 해당 저장소를 연결하고 Docker Web Service를 선택하거나 render.yaml을 사용합니다.
3. 서비스가 부여한 PORT를 deploy.py가 사용합니다. health 경로는 /_stcore/health입니다.
4. 준비 완료 후 Render가 반환하는 실제 onrender.com 주소로 접속합니다. 주소를 미리 추측해 제출하지 않습니다.
5. 로그인 화면의 ‘교수님: 가입 없이 실제 챗봇 확인’을 누릅니다.
6. PDF 단독 RAG, 다중 문서 RAG, 졸업요건 진단을 확인합니다. 벡터 검색은 ‘다국어 임베딩 + FAISS’를 켜고 검색 모드 표시를 확인합니다.

무료 템플릿은 메모리·최초 모델 다운로드·유휴 종료 등의 제한을 고려해 벡터 자동 시작을 꺼 두었습니다. 호스팅에서 실제 벡터 검색이 동작하는지 확인되기 전에는 그 서버의 전체 RAG 검증이 완료됐다고 간주하지 않습니다. 서버 재시작 시 임시 저장소의 계정·입력·업로드는 사라질 수 있습니다. 평가 입구는 원래 세션 전용입니다.

## Railway에 게시할 때

프로젝트의 Dockerfile과 railway.json을 그대로 사용합니다. 계정·프로젝트 연결 후 소스를 배포하고 Public Networking에서 공개 도메인을 생성합니다. 서버는 Railway가 부여한 PORT를 사용합니다. 새로운 유료 플랜·유료 리소스가 필요하면 비용과 한도를 확인한 뒤 진행해야 합니다. 현재 이 프로젝트의 Railway 설치·계정 연결과 실제 서버 배포는 완료되지 않았습니다.

배포 후 교수용 입구와 실제 벡터 검색을 검증한 다음 서버가 반환하는 주소를 이클래스 제출 내용에 적으세요. 기존 간편 체험 주소를 원본 Python 서버 주소로 설명하지 마세요.

## Streamlit Community Cloud에 게시할 때

GitHub 저장소에 동일 프로젝트를 올린 뒤 main file을 app.py, Python을 3.12로 선택합니다. requirements.txt와 .streamlit/config.toml을 함께 사용합니다. 생성형 답변이 필요하면 비공개 Secrets 또는 서버 환경변수로 OPENAI_API_KEY를 설정하고 앱의 LLM 토글을 켭니다. 키를 소스·과제 ZIP·교수 안내문에 넣지 마세요.

## 게시 후 필수 확인

교수 평가 입구 → PDF 5쪽 출처 질문 → 실제 벡터 모드 확인 → 추가 PDF 등록·새 내용 검색 → CSV/XLSX 진단 → 필수 과목 누락 → 95점 충족 사례 → 체험 종료 후 다른 세션의 업로드 미노출. 실제 API 호출은 유효한 키가 있는 경우 별도로 확인합니다.

참고: https://docs.streamlit.io/deploy/tutorials/docker · https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy · https://render.com/docs/free · https://docs.railway.com/builds/dockerfiles · https://docs.railway.com/networking/public-networking
