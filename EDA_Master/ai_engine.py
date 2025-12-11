# ai_engine.py
import json
import re
import time
import hashlib
from functools import lru_cache
import google.generativeai as genai

# 캐시 저장소 (간단한 딕셔너리 기반)
_response_cache = {}

def _get_cache_key(prompt):
    """프롬프트의 해시값을 캐시 키로 사용"""
    return hashlib.md5(prompt.encode()).hexdigest()

def _call_gemini_with_timeout(model_name, prompt, timeout=30):
    """타임아웃을 적용한 Gemini API 호출"""
    try:
        model = genai.GenerativeModel(model_name)
        # 타임아웃 설정 (request_options 사용)
        response = model.generate_content(
            prompt,
            request_options={"timeout": timeout}
        )
        return response.text, model_name
    except Exception as e:
        raise Exception(f"{model_name}: {str(e)}")

def ai_preprocess_task(info_str, describe_str, head_str, skew_str, prev_insight, use_cache=True, timeout=30):
    """
    AI에게 데이터 전처리 제안을 요청하는 함수
    - info, describe, head 뿐만 아니라 왜도(skew)와 이전 분석가(insight)의 의견까지 참고함
    - use_cache: 캐싱 사용 여부
    - timeout: API 호출 타임아웃 (초)
    """
    # v1beta API에서 사용 가능한 모델 (models/ 접두사 필수)
    candidate_models = [
        "models/gemini-1.5-flash",      # 안정 버전
        "models/gemini-1.5-pro",        # Pro 버전
    ]
    
    prompt = f"""
    당신은 수석 데이터 엔지니어입니다. 다음 데이터 정보를 종합적으로 판단하여 전처리 작업을 제안하세요.
    특히, [이전 AI 분석가의 소견]과 [데이터 왜도 정보]를 적극 반영하여 추천 사유를 작성하세요.
    
    [1. 데이터 기본 정보]
    {info_str}
    
    [2. 기술 통계 (Describe)]
    {describe_str}
    
    [3. 데이터 분포 특성 (왜도/Skewness)]
    * 양수: 왼쪽 쏠림(긴 오른쪽 꼬리), 음수: 오른쪽 쏠림(긴 왼쪽 꼬리)
    {skew_str}
    
    [4. 이전 AI 분석가의 소견 (참고용)]
    {prev_insight}
    
    [5. 데이터 샘플]
    {head_str}
    
    ---
    **지시사항:**
    1. 데이터의 이상치, 결측치, 치우침(Skew), 범주형 변수 변환 필요성 등을 식별하세요.
    2. 'reason' 필드에 단순히 "결측치가 있어서"라고 쓰지 말고, 
       **"분석가가 언급한 OOO 문제 해결을 위해"** 또는 **"왜도가 3.5로 높아 정규화를 위해"**와 같이 구체적인 근거를 한국어로 서술하세요.
    3. 반드시 아래 JSON 형식으로만 응답하세요. (마크다운 태그 없이)
    
    {{
        "report": "전처리 제안 요약 보고서 (한국어)",
        "actions": [
            {{
                "column": "컬럼명 (전체에 적용시 'DataFrame')", 
                "action": "작업코드 (아래 목록 중 선택)", 
                "reason": "구체적인 추천 사유 (한국어)"
            }}
        ]
    }}
    
    [가능한 작업 코드]
    - drop_column_all_nan, drop_rows_any_nan, fill_mean, fill_median, fill_mode
    - remove_outliers_iqr, cap_outliers_iqr, label_encode, one_hot_encode
    - convert_to_numeric, strip_lower_text, drop_duplicates_all_cols
    - create_squared_feature, extract_datetime_features
    """
    
    # 캐시 확인
    cache_key = _get_cache_key(prompt)
    if use_cache and cache_key in _response_cache:
        cached_result = _response_cache[cache_key]
        return json.dumps({
            **json.loads(cached_result),
            "_cached": True,
            "_model": "cached"
        })
    
    errors = []
    for model_name in candidate_models:
        try:
            text, used_model = _call_gemini_with_timeout(model_name, prompt, timeout)
            
            # 마크다운 코드 블록 제거 (```json ... ```)
            if "```" in text:
                text = re.sub(r"```json|```", "", text).strip()
            
            # JSON 객체 부분만 추출
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                result = match.group(0)
                # 캐시에 저장
                if use_cache:
                    _response_cache[cache_key] = result
                
                # 성공한 모델 정보 추가
                result_dict = json.loads(result)
                result_dict["_model"] = used_model
                return json.dumps(result_dict)
                
        except Exception as e:
            errors.append(str(e))
            continue 

    return json.dumps({"report": f"AI 모델 호출 실패: {'; '.join(errors)}", "actions": [], "_model": "none"})


def gemini_analysis_task(info_str, head_str, describe_str, extra_info, use_cache=True, timeout=30):
    """
    AI에게 데이터 분석 및 시각화 추천을 요청하는 함수
    - head_str: 여기서는 Random Sample 10개가 들어옴
    - extra_info: 상관관계 및 범주형 데이터 비율 정보
    - use_cache: 캐싱 사용 여부
    - timeout: API 호출 타임아웃 (초)
    """
    # v1beta API에서 사용 가능한 모델 (models/ 접두사 필수)
    candidate_models = [
        "models/gemini-1.5-flash",      # 안정 버전
        "models/gemini-1.5-pro",        # Pro 버전
    ]

    prompt = f"""
    다음 데이터프레임 정보를 바탕으로 심층 분석을 수행하세요.
    
    [1. 기본 정보 (Info)]
    {info_str}
    
    [2. 데이터 무작위 샘플 (Random 10 Rows)]
    {head_str}
    
    [3. 기초 통계 (Describe)]
    {describe_str}
    
    [4. 심층 분석 데이터 (상관관계 및 분포)]
    {extra_info}
    
    ---
    **요청사항:**
    1. 위 정보를 종합하여 데이터의 숨겨진 패턴이나 특징(Insight)을 **한국어**로 서술하세요. (특히 상관관계와 범주형 분포에 주목하세요)
    2. 이를 시각적으로 잘 보여줄 수 있는 그래프 2~3개를 추천하세요.
    3. 반드시 아래 JSON 형식으로만 응답하세요. (마크다운 태그 없이)
    
    {{
        "insight": "여기에 분석 내용을 한국어로 작성",
        "plots": [
            {{
                "type": "histogram, boxplot, scatterplot, barplot 중 하나",
                "x": "컬럼명 (정확히)",
                "y": "컬럼명 (필요시, 없으면 null)",
                "title": "그래프 제목 (한국어)"
            }}
        ]
    }}
    """
    
    # 캐시 확인
    cache_key = _get_cache_key(prompt)
    if use_cache and cache_key in _response_cache:
        cached_result = _response_cache[cache_key]
        return json.dumps({
            **json.loads(cached_result),
            "_cached": True,
            "_model": "cached"
        })
    
    errors = []
    for model_name in candidate_models:
        try:
            text, used_model = _call_gemini_with_timeout(model_name, prompt, timeout)
            
            if "```" in text:
                text = re.sub(r"```json|```", "", text).strip()
            
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                result = match.group(0)
                # 캐시에 저장
                if use_cache:
                    _response_cache[cache_key] = result
                
                # 성공한 모델 정보 추가
                result_dict = json.loads(result)
                result_dict["_model"] = used_model
                return json.dumps(result_dict)
                
        except Exception as e:
            errors.append(str(e))
            continue

    return json.dumps({"insight": f"AI 호출 실패: {'; '.join(errors)}", "plots": [], "_model": "none"})
