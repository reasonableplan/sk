import random
import json
import os
import requests # 외부 API 호출을 위해 추가
import nltk     # 자연어 처리를 위해 추가
import re       # 정규 표현식 추가
import datetime # 날짜 동적 생성 위해 추가

# --- scikit-learn 임포트 ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline # 파이프라인으로 묶기 위해 추가
import joblib # 모델 저장/로드를 위해 추가

# --- python-dotenv 임포트 및 환경 변수 로드 ---
from dotenv import load_dotenv
load_dotenv() # .env 파일에서 환경 변수를 로드합니다.

# --- KoNLPy 설치 및 JPype 설정 가이드 ---
# 1. Java 설치: Oracle JDK 또는 OpenJDK를 설치합니다. (버전 8 이상 권장)
#    - Windows: PATH 환경 변수에 Java/bin 경로를 추가해야 할 수 있습니다.
#    - Linux/macOS: 보통 자동으로 설정됩니다.
# 2. KoNLPy 설치: pip install konlpy
# 3. JPype 설치: pip install JPype1 (KoNLPy 설치 시 자동으로 설치될 수 있음)

# JPype 라이브러리 임포트
import jpype
# KoNLPy의 JVM 초기화 헬퍼 함수 임포트
from konlpy import jvm # KoNLPy 0.6.0 이상 버전에서 konlpy.jvm 모듈 사용
from konlpy.tag import Okt # 한국어 형태소 분석을 위해 추가

# --- JPype JVM 시작 및 경고/오류 해결 (konlpy.jvm.init_jvm 활용) ---
try:
    if not jpype.isJVMStarted():
        # KoNLPy의 jvm.init_jvm 함수를 사용하여 JVM을 시작합니다.
        # 어떤 인자도 전달하지 않고 호출합니다.
        jvm.init_jvm()
        print("JPype JVM started successfully using konlpy.jvm.init_jvm (no custom arguments).")
    else:
        print("JPype JVM is already running.")

    # JVM이 성공적으로 시작되고 클래스패스가 설정되었다면, Okt 객체는 오류 없이 생성될 것입니다.
    okt = Okt()
    print("Okt tagger initialized successfully.")

except Exception as e:
    print(f"Error initializing Okt tagger or starting JPype JVM: {e}")
    print("Troubleshooting steps:")
    print(f"- Ensure Java (JDK) is installed and its 'bin' directory is in your PATH environment variable.")
    print(f"- Try reinstalling KoNLPy and JPype (pip uninstall konlpy JPype1 && pip install konlpy JPype1).")
    exit("Exiting due to KoNLPy initialization failure.")


# --- Google Gemini API 설정 ---
import google.generativeai as genai

# Gemini API Key를 환경 변수에서 가져옵니다.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY: # 환경 변수가 설정되지 않았는지 확인
    print("\n경고: Gemini API 키 (환경 변수 'GEMINI_API_KEY')가 설정되지 않았습니다. Gemini 기능을 사용할 수 없습니다.\n")
    USE_GEMINI = False
else:
    genai.configure(api_key=GEMINI_API_KEY)

    try:
        GEMINI_MODEL = genai.GenerativeModel('gemini-pro-latest')
        USE_GEMINI = True
        # print("Gemini model 'gemini-pro-latest' initialized successfully.")

    except Exception as e:
        print(f"Gemini API 모델을 초기화하는 중 오류 발생: {e}")
        print("Gemini API 키가 유효한지, 인터넷 연결이 되어 있는지 확인하세요.")
        USE_GEMINI = False


# --- NLTK 데이터 다운로드 (최초 1회 실행 후 주석 처리하거나 별도 실행)
# try:
#     nltk.data.find('tokenizers/punkt')
# except nltk.downloader.DownloadError:
#     nltk.download('punkt')
# # 불용어 사용 시
# # try:
# #     nltk.data.find('corpora/stopwords')
# # except nltk.downloader.DownloadError:
# #     nltk.download('stopwords')

# --- 0. 설정 및 데이터 파일 경로 ---
DATA_FILE = "ultron_data.json"
MODEL_FILE = "intent_model.joblib" # 모델 저장 파일
# OpenWeatherMap API Key도 환경 변수에서 가져옵니다.
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

WEATHER_API_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_API_URL = "http://api.openweathermap.org/data/2.5/forecast" # 5일치 예보


# 한국어 불용어 예시 (NLU 패턴 매칭에서 제외하거나 전처리에서 사용할 수 있습니다)
korean_stopwords = ['은', '는', '이', '가', '을', '를', '에', '에서', '에게', '의', '와', '과', '하다', '이다', '되다', '이다', '있다', '없다', '좀', '정말', '진짜', '알려줘', '어때', '궁금해', '어떻게', '해줘', '해', '줘', '무슨', '무엇', '뭐', '좀', '막', '너무', '정말', '진짜']

# 모델 예측 신뢰도 임계값
CONFIDENCE_THRESHOLD = 0.65 # 65% 미만이면 'general_query'로 처리


# --- 1. 데이터 불러오기 또는 초기화 함수 ---
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "user_name": None,
        "user_facts": {},
        # --- '하오' 응답을 custom_responses 초기값에서 제거 ---
        "custom_responses": {},
        "last_intent": None, # 문맥 유지를 위해 추가
        "last_entity": {}    # 문맥 유지를 위해 추가 (예: {"city": "서울"})
    }

# --- 2. 데이터 저장 함수 ---
def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- 3. 외부 API 함수: 날씨 정보 가져오기 ---
def get_weather_info(city, date_type="today"):
    if not OPENWEATHERMAP_API_KEY: # 환경 변수에서 가져온 키가 없으면
        return "죄송합니다, 울트론은 아직 날씨 API 키가 설정되지 않아 날씨를 알 수 없습니다."

    params = {
        "q": city,
        "appid": OPENWEATHERMAP_API_KEY,
        "units": "metric", # 섭씨
        "lang": "kr"       # 한국어
    }

    try:
        if date_type == "today":
            response = requests.get(WEATHER_API_URL, params=params)
            response.raise_for_status() # HTTP 오류가 발생하면 예외 발생
            weather_data = response.json()

            if weather_data and weather_data.get('main') and weather_data.get('weather'):
                main_info = weather_data['main']
                weather_desc = weather_data['weather'][0]['description']
                temp = main_info['temp']
                feels_like = main_info['feels_like']
                return f"{city}의 현재 날씨는 '{weather_desc}', 기온은 {temp}°C (체감 {feels_like}°C) 입니다."
            else:
                return f"{city}의 날씨 정보를 찾을 수 없습니다. 도시 이름을 확인해주세요."
        elif date_type == "tomorrow":
            # 5일치 예보를 가져와 내일 날씨를 찾습니다.
            response = requests.get(FORECAST_API_URL, params=params)
            response.raise_for_status()
            forecast_data = response.json()

            if forecast_data and forecast_data.get('list'):
                # 내일 날짜
                tomorrow = datetime.date.today() + datetime.timedelta(days=1)
                tomorrow_str = tomorrow.strftime('%Y-%m-%d')

                tomorrow_forecasts = []
                for item in forecast_data['list']:
                    if item['dt_txt'].startswith(tomorrow_str):
                        # 내일의 가장 가까운 정오/오후 시간대 예보
                        if "12:00:00" in item['dt_txt'] or "15:00:00" in item['dt_txt']:
                             tomorrow_forecasts.append(item)
                             break

                if tomorrow_forecasts:
                    main_info = tomorrow_forecasts[0]['main']
                    weather_desc = tomorrow_forecasts[0]['weather'][0]['description']
                    temp_min = main_info['temp_min']
                    temp_max = main_info['temp_max']
                    return f"{city}의 내일 날씨는 '{weather_desc}', 최저 {temp_min}°C, 최고 {temp_max}°C로 예상됩니다."
                else:
                    return f"{city}의 내일 날씨 예보를 찾을 수 없습니다."
            else:
                return f"{city}의 날씨 예보를 찾을 수 없습니다. 도시 이름을 확인해주세요."

    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류 발생: {e}")
        return "날씨 정보를 가져오는 데 문제가 발생했습니다. 다시 시도해주세요."
    except json.JSONDecodeError:
        print("API 응답을 해석하는 데 문제가 발생했습니다.")
        return "날씨 정보를 해석하는 데 문제가 발생했습니다. 다시 시도해주세요."
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        return "날씨 정보를 가져오는 중 알 수 없는 오류가 발생했습니다."

# --- Gemini API 호출 함수 ---
def get_gemini_response(prompt_text, user_name=None):
    if not USE_GEMINI:
        return "죄송합니다. Gemini API 키가 설정되지 않아 이 질문에 답할 수 없습니다."

    # Gemini에 전달할 초기 프롬프트 (페르소나 설정)
    system_prompt = "당신은 울트론이라는 이름의 유용한 인공지능 어시스턴트입니다. 사용자의 질문에 친절하고 상세하게 답변해주세요. 창의적인 질문에도 잘 응답합니다."
    if user_name:
        system_prompt += f" 현재 사용자의 이름은 {user_name}입니다. 답변에 {user_name}님을 적절히 언급해주세요."

    try:
        response = GEMINI_MODEL.generate_content(
            [system_prompt, prompt_text],
            safety_settings={
                "HARASSMENT": "BLOCK_NONE",
                "HATE_SPEECH": "BLOCK_NONE",
                "SEXUALLY_EXPLICIT": "BLOCK_NONE",
                "DANGEROUS": "BLOCK_NONE",
            }
        )
        return response.text
    except Exception as e:
        print(f"Gemini API 호출 중 오류 발생: {e}")
        return "죄송합니다, 제미나이 API 호출 중 문제가 발생했습니다. 다시 시도해주세요."


# --- 4. 챗봇의 응답 규칙 정의 (기본 응답) ---
# 이제 키워드 대신 '의도'에 매핑됩니다.
default_responses_by_intent = {
    "greeting": [
        "안녕하세요{name_suffix}! 만나서 반갑습니다.",
        "반가워요{name_suffix}!",
        "안녕하세요{name_suffix}, 좋은 하루 되세요!",
        "하이{name_suffix}, 무얼 도와드릴까요?"
    ],
    "farewell": [
        "다음에 또 만나요{name_suffix}! 안녕히 계세요.",
        "잘 가세요{name_suffix}!",
        "또 방문해주세요{name_suffix}!",
        "안녕히 가세요{name_suffix}! 즐거운 시간 보내세요."
    ],
    "chatbot_name": [
        "저는 울트론입니다. 당신은요?",
        "저는 울트론입니다. 당신의 이름은 무엇인가요?",
        "저는 인공지능 '울트론'입니다. 당신의 이름은 궁금하네요!",
        "저는 울트론, 당신을 돕기 위해 만들어진 AI입니다."
    ],
    "who_made_you": [
        "저는 진화하는 AI 울트론입니다. 개발자들의 노력을 통해 탄생했습니다.",
        "울트론은 당신을 위해 존재합니다.",
        "정확히 누가 저를 만들었는지보다는, 울트론을 통해 무엇을 할 수 있는지가 더 중요하지 않을까요{name_suffix}?"
    ],
    "date_query": [
        f"오늘 날짜는 {datetime.date.today().strftime('%Y년 %m월 %d일')}입니다{{name_suffix}}.",
        f"오늘은 {datetime.date.today().strftime('%m월 %d일')}입니다{{name_suffix}}.",
        f"벌써 {datetime.date.today().strftime('%m월 %d일')}이네요{{name_suffix}}!"
    ],
    "hao_response": [ # <--- '하오' 의도에 대한 응답 추가
        "하오"
    ]
    # 날씨, 정보 학습/질문, 규칙 학습 등은 동적으로 처리되므로 여기에 추가하지 않습니다.
    # custom_responses는 별도로 관리됩니다.
}

# --- NLU 강화를 위한 전처리 함수 ---
def preprocess_text(text):
    # KoNLPy의 Okt를 사용하여 명사, 동사, 형용사 등의 어간을 추출하여 토큰화
    # 모델 학습 및 예측 시 일관된 전처리를 위해 사용
    tokens = okt.phrases(text) # 더 구 단위로 묶어서 처리
    # 불용어 제거는 학습 데이터에서는 하지 않고, NLU 로직에서 fact_key 추출 시에만 적용
    return ' '.join(tokens)

# --- 의도 분류 모델 학습 데이터 ---
# (실제 서비스에서는 훨씬 더 많은 데이터와 다양한 표현이 필요합니다!)
intent_training_data = [
    ("안녕", "greeting"),
    ("안녕하세요", "greeting"),
    ("반가워", "greeting"),
    ("하이", "greeting"),
    ("잘가", "farewell"),
    ("종료", "farewell"),
    ("또 봐", "farewell"),
    ("안녕히 계세요", "farewell"),
    ("너 이름이 뭐니", "chatbot_name"),
    ("너 누구야", "chatbot_name"),
    ("울트론 누구야", "chatbot_name"),
    ("이름 알려줘", "chatbot_name"),
    ("누가 널 만들었어", "who_made_you"),
    ("만든 사람", "who_made_you"),
    ("개발자가 누구야", "who_made_you"),
    ("오늘 날짜 뭐야", "date_query"),
    ("오늘이 며칠이야", "date_query"),
    ("날짜 알려줘", "date_query"),
    ("오늘 몇월 며칠", "date_query"),
    ("서울 날씨 어때", "weather"),
    ("부산 날씨 알려줘", "weather"),
    ("내일 날씨 궁금해", "weather"),
    ("광주 내일 기온", "weather"),
    ("제주도 오늘 날씨", "weather"),
    ("내 취미는 뭐야", "query_user_fact"),
    ("내가 좋아하는 색깔이 뭐야", "query_user_fact"),
    ("내 특기 알려줘", "query_user_fact"),
    ("내 생일이 언제야", "query_user_fact"),
    ("내 이름은 울트론이야", "learn_user_name"), # 이름 학습 의도 (규칙 기반으로 처리)
    ("내 취미는 독서야", "learn_user_fact"),
    ("내가 좋아하는 음식은 피자야", "learn_user_fact"),
    ("내 특기는 코딩이야", "learn_user_fact"),
    ("내 좌우명은 긍정이야", "learn_user_fact"),
    ("울트론, [심심해]라고 물으면 [놀자]라고 해줘", "learn_custom_response"),
    ("울트론, [졸려] 하면 [자러가자]라고 대답해줘", "learn_custom_response"),
    ("울트론, [밥 먹었어]라고 하면 [아직]이라고 해줘", "learn_custom_response"),
    ("하오", "hao_response"), # <--- '하오' 학습 데이터 추가
    ("이거 무슨 말이야", "general_query"),
    ("세상에서 가장 높은 산은 어디야", "general_query"),
    ("파이썬 코딩 알려줘", "general_query"),
    ("인공지능이란 무엇인가", "general_query"),
    ("그거 어떻게 하는거야", "general_query"),
    ("미래 기술에 대해 말해줘", "general_query"),
]


# --- 의도 분류 모델 학습 및 로드 함수 ---
def train_and_load_intent_model():
    if os.path.exists(MODEL_FILE):
        print(f"DEBUG: 기존 모델 파일 '{MODEL_FILE}' 로드 중...")
        pipeline = joblib.load(MODEL_FILE)
        print("DEBUG: 모델 로드 완료.")
        return pipeline

    print("DEBUG: 새로운 의도 분류 모델 학습 중...")
    X_train = [preprocess_text(text) for text, _ in intent_training_data]
    y_train = [intent for _, intent in intent_training_data]

    # TF-IDF 벡터화와 로지스틱 회귀를 파이프라인으로 연결
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2))), # n-gram 범위 확장 (단어 1~2개 조합)
        ('clf', LogisticRegression(random_state=42, solver='liblinear', max_iter=200)) # solver 변경, max_iter 증가
    ])

    pipeline.fit(X_train, y_train)
    joblib.dump(pipeline, MODEL_FILE) # 학습된 모델 저장
    print("DEBUG: 모델 학습 및 저장 완료.")
    return pipeline

# --- 의도 분류 모델 전역 변수 ---
intent_pipeline = None


# --- 5. NLU (자연어 이해) 로직 ---
def analyze_input(raw_text, current_data, intent_pipeline):
    intent = None
    entity = {}
    preprocessed_text = raw_text.lower().strip() # 일부 규칙에 사용할 소문자 텍스트

    # KoNLPy를 사용한 형태소 분석 (정규화, 어간 추출 적용)
    pos_tags = okt.pos(raw_text, norm=True, stem=True)
    # print(f"DEBUG: POS Tags: {pos_tags}") # 디버깅용

    # --- Phase 1: 높은 우선순위의 규칙 기반 의도 탐지 (학습/이름 설정 등) ---
    # 1. 사용자 이름 설정 의도 (가장 먼저 처리)
    name_match = re.search(r"(내|저의) 이름은\s*(.+)(이|야|입니다|에요)", raw_text)
    if name_match:
        intent = "learn_user_name"
        name_part = name_match.group(2).strip()
        entity["user_name"] = " ".join([w for w in name_part.split() if w not in korean_stopwords])
        return intent, entity

    # 2. 새로운 응답 규칙 학습 의도 파악
    custom_response_learn_match = re.search(r"울트론,\s*\[([^\]]+)\]라고\s*물으면\s*\[([^\]]+)\]라고\s*해줘", raw_text)
    if custom_response_learn_match:
        intent = "learn_custom_response"
        entity["taught_keyword"] = custom_response_learn_match.group(1).strip()
        entity["taught_response"] = custom_response_learn_match.group(2).strip()
        return intent, entity

    # 3. 사용자 정보 학습 의도 파악
    learn_fact_match = re.search(r"(내|저의)\s*(.+)\s*는\s*(.+)(이|가)?(다|야|에요|입니다)\s*$", preprocessed_text)
    if learn_fact_match:
        intent = "learn_user_fact"
        fact_key_raw = learn_fact_match.group(2).strip()
        entity["fact_key"] = " ".join([w for w in fact_key_raw.split() if w not in korean_stopwords])
        entity["fact_value"] = learn_fact_match.group(3).strip()
        return intent, entity


    # --- Phase 2: 의도 분류 모델을 사용한 의도 예측 ---
    processed_for_model = preprocess_text(raw_text)
    if intent_pipeline:
        probabilities = intent_pipeline.predict_proba([processed_for_model])[0]
        max_prob_index = probabilities.argmax()
        predicted_intent = intent_pipeline.classes_[max_prob_index]
        confidence = probabilities[max_prob_index]

        # print(f"DEBUG: 모델 예측: {predicted_intent} (신뢰도: {confidence:.2f})")

        if confidence >= CONFIDENCE_THRESHOLD:
            intent = predicted_intent
        else:
            intent = "general_query" # 신뢰도가 낮으면 일반 질문으로 처리
    else:
        intent = "general_query" # 모델이 로드되지 않았으면 일반 질문으로 처리


    # --- Phase 3: 파악된 의도에 따른 개체(Entity) 추출 ---
    if intent == "weather":
        cities = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "제주", "고양", "수원", "성남", "창원", "청주", "천안", "전주", "포항"] # 더 많은 도시 추가 가능
        city_found_in_input = None
        for word, tag in pos_tags:
            if tag == "Noun" and word in cities:
                city_found_in_input = word
                break

        date_type_found_in_input = None
        for word, tag in pos_tags:
            if word == "내일" and tag in ["Noun", "Adverb"]:
                date_type_found_in_input = "tomorrow"
                break
            elif word == "오늘" and tag in ["Noun", "Adverb"]:
                date_type_found_in_input = "today"
                break
        
        entity["city"] = city_found_in_input if city_found_in_input else (
            current_data["last_entity"].get("city") if current_data["last_intent"] == "weather" else "서울" # 기본값 서울
        )
        entity["date_type"] = date_type_found_in_input if date_type_found_in_input else "today"


    elif intent == "query_user_fact":
        # '내 ~는 뭐야' 패턴은 모델이 이미 의도를 분류했으므로, 여기서 ~만 추출
        query_fact_match = re.search(r"(내|저의)\s*(.+)\s*는\s*뭐(야|예요|요)?\s*$", preprocessed_text)
        if query_fact_match:
            fact_key_raw = query_fact_match.group(2).strip()
            entity["fact_key"] = " ".join([w for w in fact_key_raw.split() if w not in korean_stopwords])
        else: # 모델이 query_user_fact로 분류했지만 패턴이 맞지 않는 경우 (예: "내 직업은?")
              # 여기서도 명사만 추출하는 등의 추가 로직이 필요할 수 있으나, 일단 빈 값으로 둠
            entity["fact_key"] = None


    # `learn_user_fact`, `learn_custom_response`, `learn_user_name`은 Phase 1에서 entity까지 추출했으므로 여기서 추가 작업 필요 없음


    return intent, entity

# --- 한국어 감지 함수 ---
def contains_hangul(text):
    """주어진 텍스트에 한글 문자가 포함되어 있는지 확인합니다."""
    for char in text:
        if '\uac00' <= char <= '\ud7a3':
            return True
    return False

# --- 6. 챗봇 시작 메시지 및 데이터 로드 ---
print("---------------------------------------")
print("안녕하세요! 저는 진화하는 인공지능 '울트론'입니다. '종료'라고 입력하면 대화가 끝나요.")
print("울트론에게 당신의 이름을 알려주세요! (예: 내 이름은 [이름])")
print("울트론에게 정보를 가르칠 수 있습니다! (예: 내 취미는 독서야)")
print("울트론에게 새로운 대화 규칙을 가르칠 수 있습니다! (예: 울트론, [심심해]라고 물으면 [놀자]라고 해줘)")
print("날씨를 물어보세요! (예: 서울 날씨 알려줘, 내일 부산 날씨 어때?)")
if USE_GEMINI:
    print("Gemini API가 활성화되어 있어 더 다양한 질문에 답변할 수 있습니다!")
else:
    print("Gemini API가 비활성화되어 일반 질문에는 답변하기 어렵습니다.")
print("---------------------------------------")

# 저장된 데이터 불러오기
data = load_data()
user_name = data["user_name"]
user_facts = data["user_facts"]
custom_responses = data["custom_responses"]
last_intent = data["last_intent"]
last_entity = data["last_entity"]

# 의도 분류 모델 학습 또는 로드
intent_pipeline = train_and_load_intent_model()

# --- 7. 챗봇의 메인 대화 루프 ---
while True:
    user_input_raw = input(f"{user_name if user_name else '사용자'}: ")

    # --- 한국어 감지 로직 (복구된 메시지) ---
    if not contains_hangul(user_input_raw):
        print("울트론: 한국어로 말해 이 맞장깔 새끼야")
        continue

    user_input = user_input_raw.lower().strip()

    found_response = False
    current_intent = None
    current_entity = {}

    # 7-1. 종료 조건 확인 (모델 예측보다 항상 우선)
    if user_input == "종료":
        if user_name:
            print(f"울트론: 다음에 또 만나요, {user_name}님! 대화를 종료합니다.")
        else:
            print("울트론: 다음에 또 만나요! 대화를 종료합니다.")
        save_data(data)
        break

    # 7-2. NLU를 통해 의도와 개체 파악 (의도 분류 모델 활용)
    current_intent, current_entity = analyze_input(user_input_raw, data, intent_pipeline)

    name_suffix = f", {user_name}님" if user_name else ""

    # 7-3. 파악된 의도에 따른 동적 응답 처리 (학습, 날씨 등)
    if current_intent == "learn_user_name":
        user_name_to_set = current_entity.get("user_name")
        if user_name_to_set:
            user_name = user_name_to_set
            data["user_name"] = user_name
            print(f"울트론: 안녕하세요, {user_name}님! 만나서 반갑습니다.")
            found_response = True
        else: # 이름 추출 실패 시 (예: "내 이름은")
            print(f"울트론: 이름을 정확히 알려주시겠어요? '내 이름은 [이름]이야' 형식으로 알려주세요.")
            found_response = True
        
    elif current_intent == "weather":
        city = current_entity.get("city")
        date_type = current_entity.get("date_type", "today")

        if not city:
            print(f"울트론: 어느 도시의 날씨를 알려드릴까요{name_suffix}?")
            found_response = True
        elif city:
            response = get_weather_info(city, date_type)
            print(f"울트론: {response}{name_suffix}")
            found_response = True

    elif current_intent == "query_user_fact":
        fact_key = current_entity.get("fact_key")
        if fact_key and fact_key in user_facts:
            print(f"울트론: 당신의 {fact_key}은/는 {user_facts[fact_key]}입니다{name_suffix}.")
            found_response = True
        elif fact_key:
            print(f"울트론: {fact_key}에 대한 정보를 알려주신 적이 없는 것 같아요{name_suffix}.")
            found_response = True
        else:
            print(f"울트론: 어떤 정보를 궁금해하시나요{name_suffix}? '내 [정보]는 뭐야?' 형식으로 질문해주세요.")
            found_response = True

    elif current_intent == "learn_user_fact":
        fact_key = current_entity.get("fact_key")
        fact_value = current_entity.get("fact_value")
        if fact_key and fact_value:
            user_facts[fact_key] = fact_value
            data["user_facts"] = user_facts
            print(f"울트론: 알겠습니다{name_suffix}! {fact_key}은/는 {fact_value}(이)라고 기억할게요.")
            found_response = True
        else:
            print("울트론: 어떤 정보를 가르쳐 주시는지 잘 모르겠어요{name_suffix}. '내 [정보]는 [값]이야' 형식으로 알려주세요.")
            found_response = True

    elif current_intent == "learn_custom_response":
        taught_keyword = current_entity.get("taught_keyword")
        taught_response = current_entity.get("taught_response")
        if taught_keyword and taught_response:
            custom_responses[taught_keyword] = taught_response
            data["custom_responses"] = custom_responses
            print(f"울트론: 알겠습니다{name_suffix}! '{taught_keyword}'라고 물으면 '{taught_response}'라고 답변할게요.")
            found_response = True
        else:
            print("울트론: 어떤 규칙을 가르쳐 주시는지 잘 모르겠어요{name_suffix}. '울트론, [키워드]라고 물으면 [응답]이라고 해줘' 형식으로 알려주세요.")
            found_response = True


    # 7-4. 정적 응답 딕셔너리 또는 사용자 정의 응답에서 찾기
    if not found_response:
        # custom_responses는 user_input_raw와 정확히 일치하는 경우 우선 적용
        if user_input_raw in custom_responses:
            final_response = custom_responses[user_input_raw]
            print(f"울트론: {final_response}")
            found_response = True
        # 그 외의 의도 기반 정적 응답
        elif current_intent in default_responses_by_intent:
            selected_response_template = random.choice(default_responses_by_intent[current_intent])
            final_response = selected_response_template.replace("{name_suffix}", name_suffix)
            print(f"울트론: {final_response}")
            found_response = True

    # --- 7-5. 모든 내부 로직으로 처리할 수 없는 질문은 Gemini API로 전달 ---
    # current_intent가 "general_query"이거나, 위에서 아무것도 찾지 못했을 때
    if not found_response and current_intent == "general_query" and USE_GEMINI:
        print(f"울트론: (Gemini에게 문의 중...)")
        gemini_answer = get_gemini_response(user_input_raw, user_name)
        print(f"울트론: {gemini_answer}") # Gemini 응답에는 name_suffix가 이미 포함될 수 있으므로 직접 추가하지 않음
        found_response = True
    elif not found_response and current_intent == "general_query" and not USE_GEMINI:
        print(f"울트론: 죄송합니다{name_suffix}. 무슨 말씀인지 잘 모르겠어요. Gemini API가 비활성화되어 있어 이 질문에 답변할 수 없습니다.")
        found_response = True
    elif not found_response: # 혹시 모를 상황 (의도가 파악됐지만 응답이 없는 경우)
        print(f"울트론: 죄송합니다{name_suffix}. 현재 질문에 대한 답변을 찾을 수 없습니다.")


    # 7-6. 문맥 업데이트
    data["last_intent"] = current_intent
    data["last_entity"] = current_entity
    save_data(data)
