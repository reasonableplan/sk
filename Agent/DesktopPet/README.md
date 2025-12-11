# Desktop Pet - AI 코딩 전문 에이전트

귀여운 Desktop Pet이 강력한 AI 코딩 에이전트로 변신! 🚀

## ✨ 주요 기능

### 🤖 AI 코드 리뷰어 (Phase 1)
- 코드 품질 평가 (1-10점)
- 버그 및 문제점 자동 감지
- 개선 제안 및 리팩토링 코드 제공
- 10개 언어 지원 (Python, JavaScript, Java 등)

### 📦 Git 커밋 도우미 (Phase 2)
- 저장소 상태 실시간 표시
- 변경사항 Diff 뷰어
- AI 커밋 메시지 자동 생성 (3가지 스타일)
  - Conventional Commits
  - Simple
  - Detailed
- 원클릭 커밋 실행
- 커밋 히스토리 조회

### 📋 클립보드 모니터링 (Phase 3)
- 코드 복사 시 자동 감지 (20+ 패턴)
- 언어 자동 식별
- 빠른 분석 (복잡도, 구조)
- AI 피드백 제공
- AI 리뷰 탭 자동 연동

### 🧪 자동 테스트 생성기 (Phase 4)
- 함수 자동 파싱
- pytest 테스트 자동 생성
- 정상/엣지/예외 케이스 포함
- AI 기반 스마트 테스트

### 🔍 실시간 코드 분석 (Phase 5)
- PEP 8 스타일 체크
- 코드 복잡도 분석
- 보안 취약점 검사
- 개선 제안
- 종합 품질 리포트

## 🚀 설치 및 실행

### 1. 패키지 설치
```bash
pip install -r requirements_coding_agent.txt
```

**필수 패키지**:
- `google-generativeai` - AI 기능
- `GitPython` - Git 통합
- `pyperclip` - 클립보드 모니터링
- `python-dotenv` - 환경 변수
- `pycodestyle` - 코드 스타일 체크 (선택)

### 2. API 키 설정
```bash
# .env 파일 생성
copy .env.example .env
```

`.env` 파일 편집:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

**API 키 발급**: https://makersuite.google.com/app/apikey

### 3. Desktop Pet 실행
```bash
python main.py
```

## 💡 사용 방법

### 기본 워크플로우

1. **Desktop Pet 실행**
   - `python main.py`

2. **코딩 비서 열기**
   - Desktop Pet 우클릭
   - "💻 프로 코딩 비서" 선택

3. **기능 사용**

#### 🤖 AI 코드 리뷰
1. "🤖 AI 리뷰" 탭
2. 코드 붙여넣기
3. 언어 선택
4. "🚀 AI 리뷰 받기" 클릭

#### 📦 Git 커밋
1. "📦 Git" 탭
2. 파일 수정 후 `git add`
3. "🤖 AI 메시지 생성" 클릭
4. "✅ 커밋 실행" 클릭

#### 📋 클립보드 모니터링
1. "📊 대시보드" 탭
2. "📋 클립보드 모니터 OFF" → ON
3. 코드 복사 시 자동 감지

#### 🧪 테스트 생성
1. "🤖 AI 리뷰" 탭
2. 함수 코드 입력
3. "🧪 테스트 생성" 클릭

#### 🔍 코드 분석
1. "🤖 AI 리뷰" 탭
2. 코드 입력
3. "🔍 코드 분석" 클릭

## 📁 프로젝트 구조

```
DesktopPet/
├── main.py                      # 메인 애플리케이션
├── coding_assistant.py          # 코딩 비서 (통합)
├── ai_code_reviewer.py          # AI 코드 리뷰어
├── git_assistant.py             # Git 도우미
├── clipboard_monitor.py         # 클립보드 모니터
├── test_generator.py            # 테스트 생성기
├── code_analyzer.py             # 코드 분석기
├── requirements_coding_agent.txt # 의존성
├── .env.example                 # API 키 템플릿
└── assets/                      # 리소스 파일
```

## 🎯 핵심 차별화 포인트

### 1. 올인원 통합
- 코드 리뷰, Git, 테스트, 분석을 하나로
- IDE 없이도 강력한 개발 지원

### 2. AI 기반 지능화
- Gemini API로 고급 분석
- 자연어 이해 및 생성
- 맥락 기반 제안

### 3. 백그라운드 자동화
- 클립보드 자동 감지
- 실시간 모니터링
- 비간섭적 알림

### 4. 귀여운 펫 + 강력한 기능
- 재미있는 UI
- 실용적인 도구
- 개발 동기 부여

## ⚠️ 주의사항

### API 사용
- Gemini API 무료 티어 한도 확인
- 과도한 사용 시 제한 가능

### 성능
- 클립보드 모니터링은 필요시에만 ON
- 대용량 코드는 처리 시간 소요

### 보안
- 민감한 코드는 AI 전송 주의
- `.env` 파일은 Git에 커밋 금지

## 🐛 문제 해결

### 모듈 import 오류
```bash
pip install google-generativeai GitPython pyperclip python-dotenv pycodestyle
```

### API 키 오류
- `.env` 파일 존재 확인
- API 키 형식 확인
- 유효한 키인지 확인

### Git 기능 오류
- Git 설치 확인: `git --version`
- Git 저장소 내에서 실행

## 📊 구현 통계

- **새 파일**: 7개
- **총 코드**: ~2,500줄
- **새 기능**: 20+ 메서드
- **지원 언어**: 10개

## 🎉 완성된 기능

| Phase | 기능 | 상태 |
|-------|------|------|
| 1 | AI 코드 리뷰어 | ✅ |
| 2 | Git 커밋 도우미 | ✅ |
| 3 | 클립보드 모니터링 | ✅ |
| 4 | 자동 테스트 생성기 | ✅ |
| 5 | 실시간 코드 분석 | ✅ |

**진행률**: 100% 🎉

## 📄 라이선스

개인 프로젝트
