# EDA Master

PyQt6 기반 탐색적 데이터 분석(EDA) 대시보드 애플리케이션

## ✨ 주요 기능

### 📊 데이터 분석
- CSV 파일 로드 및 탐색
- 기술 통계량 자동 계산
- 결측치 및 이상치 탐지

### 🤖 AI 기반 분석
- **AI Data Engineer**: 전처리 제안
- **AI Analyst**: 데이터 인사이트 및 시각화 추천
- Gemini API 통합

### 📈 시각화
- 히스토그램, 박스플롯
- 상관관계 히트맵
- 파이차트, 바차트
- 차트 이미지 내보내기

### 🔧 데이터 전처리
- 결측치 처리 (평균/중앙값/최빈값)
- 이상치 제거 (IQR, Z-score)
- 인코딩 (Label, One-Hot)
- 스케일링 (MinMax, Standard, Robust)
- 피처 엔지니어링

### 🎯 머신러닝
- **지원 알고리즘**: XGBoost, RandomForest, LightGBM
- 교차 검증 (K-Fold)
- 하이퍼파라미터 튜닝
- 모델 저장/로드

## 🚀 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. API 키 설정
```bash
# .env.example을 .env로 복사
copy .env.example .env

# .env 파일 편집
GEMINI_API_KEY=your_api_key_here
```

### 3. 실행
```bash
python main.py
```

## 📦 필수 패키지

- PyQt6 >= 6.4.0
- pandas >= 1.5.0
- numpy >= 1.23.0
- matplotlib >= 3.6.0
- seaborn >= 0.12.0
- scikit-learn >= 1.2.0
- xgboost >= 1.7.0
- lightgbm >= 3.3.0
- google-generativeai >= 0.3.0
- python-dotenv >= 0.21.0

## 📁 프로젝트 구조

```
EDA_Master/
├── main.py              # 메인 애플리케이션
├── ai_engine.py         # AI 분석 엔진
├── ml_engine.py         # 머신러닝 엔진
├── data_processor.py    # 데이터 전처리
├── ui_pages.py          # UI 페이지
├── config_manager.py    # 설정 관리
├── common.py            # 공통 유틸리티
├── requirements.txt     # 의존성 목록
├── .env.example         # API 키 템플릿
└── .gitignore          # Git 제외 파일
```

## 🔒 보안

- `.env` 파일은 Git에 커밋되지 않습니다
- API 키는 환경 변수로 관리
- 민감한 데이터는 로컬에만 저장

## 📝 사용 방법

1. **데이터 로드**: "📂 Load CSV" 버튼으로 CSV 파일 로드
2. **데이터 탐색**: 대시보드에서 기본 통계 확인
3. **AI 분석**: AI Analyst/Engineer로 인사이트 획득
4. **전처리**: 제안된 전처리 적용
5. **ML 모델링**: 알고리즘 선택 후 학습
6. **결과 저장**: 모델 및 차트 저장

## ⚠️ 주의사항

- Gemini API 무료 티어 한도 확인
- 대용량 데이터는 처리 시간 소요
- API 키는 절대 공유하지 마세요

## 🐛 문제 해결

### API 오류
- `.env` 파일 확인
- API 키 유효성 확인
- 인터넷 연결 확인

### 패키지 오류
```bash
pip install --upgrade -r requirements.txt
```

## 📄 라이선스

개인 프로젝트
