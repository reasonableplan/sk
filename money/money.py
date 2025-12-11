import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import random 
from flask import Flask, jsonify, request, render_template # render_template 임포트 추가
from flask_cors import CORS

app = Flask(__name__)
# Flask 앱이 정적 파일(JS, CSS 등)을 찾을 기본 경로를 설정할 수 있지만
# 이 예시에서는 index.html이 모든 것을 포함하고 있어 특별히 필요하지 않습니다.
# 만약 별도의 static 폴더에 JS/CSS 파일이 있다면
# app = Flask(__name__, static_folder='static', template_folder='templates')
# 와 같이 설정할 수 있습니다.
CORS(app) # 모든 경로에 대해 CORS 허용. 실제 서비스에서는 특정 Origin만 허용하는 것이 좋습니다.

# --- 전역 상수 및 설정 (기존 코드에서 가져옴) ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x66) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/109.0.1518.78",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/110.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15"
]

# --- 1. 환율 크롤링 함수 (Frankfurter API 사용으로 수정) ---
import yfinance as yf
from datetime import datetime, timedelta

def get_exchange_rates_from_frankfurter():
    print("\n--- Frankfurter API에서 환율 데이터를 가져오는 중... ---")
    
    target_currencies = ["KRW", "CNY", "JPY", "RUB", "CAD", "AUD", "MXN", "INR", "GBP", "EUR", "TWD"]
    frankfurter_api_url = "https://api.frankfurter.app/latest"

    try:
        response = requests.get(frankfurter_api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rates = data['rates']
        
        eur_rates = {currency: rates.get(currency) for currency in target_currencies if currency in rates}
        
        # EUR/USD 환율은 yfinance에서 가져옵니다.
        eur_usd_ticker = yf.Ticker("EURUSD=X")
        eur_usd_data = eur_usd_ticker.history(period="1d")
        if not eur_usd_data.empty:
            eur_usd_rate = eur_usd_data['Close'].iloc[-1]
        else:
            print("[경고] yfinance에서 EUR/USD 환율을 가져오는 데 실패했습니다. USD 기반 환율 계산에 오류가 있을 수 있습니다.")
            return pd.DataFrame() 

        exchange_data = []
        for currency, eur_to_currency_rate in eur_rates.items():
            if eur_to_currency_rate is not None and eur_usd_rate is not None:
                if currency == "EUR":
                    # USD/EUR은 1 / EUR/USD
                    usd_to_currency_rate = 1 / eur_usd_rate
                    pair_name = "USD/EUR"
                    ticker = "EUR=X" 
                else:
                    # EUR 기준 환율을 USD 기준으로 변환
                    usd_to_currency_rate = eur_to_currency_rate / eur_usd_rate
                    pair_name = f"USD/{currency}"
                    # Ticker는 yfinance에서 통용되는 형식으로 (USD/KRW -> KRW=X)
                    ticker = f"{currency}=X" if currency != "USD" else "USD=X"

                exchange_data.append({"통화쌍": pair_name, "환율": usd_to_currency_rate, "Ticker": ticker})
        
        # GBP/USD와 JPY/KRW는 특별히 추가 (요청에 있었던 항목)
        if "GBP" in eur_rates and eur_rates["GBP"] is not None and eur_usd_rate is not None:
            gbp_usd_rate = eur_rates["GBP"] / eur_usd_rate
            exchange_data.append({"통화쌍": "GBP/USD", "환율": gbp_usd_rate, "Ticker": "GBPUSD=X"})

        if "JPY" in eur_rates and "KRW" in eur_rates and eur_rates["JPY"] is not None and eur_rates["KRW"] is not None:
            jpy_krw_rate = eur_rates["KRW"] / eur_rates["JPY"] 
            exchange_data.append({"통화쌍": "JPY/KRW", "환율": jpy_krw_rate, "Ticker": "JPYKRW=X"})
        
        if "EUR" in eur_rates and "KRW" in eur_rates and eur_rates["KRW"] is not None:
            eur_krw_rate = eur_rates["KRW"] 
            exchange_data.append({"통화쌍": "EUR/KRW", "환율": eur_krw_rate, "Ticker": "EURKRW=X"})

        print("--- 환율 데이터 가져오기 완료. ---")
        return pd.DataFrame(exchange_data)
        
    except requests.exceptions.RequestException as e:
        print(f"[오류] Frankfurter API에서 환율 데이터를 가져오는 중 네트워크 오류 발생: {e}")
    except Exception as e:
        print(f"[오류] Frankfurter API 응답 처리 중 오류 발생: {e}")
    return pd.DataFrame()


# --- 2. 금리 크롤링 함수 (기존 코드 재사용) ---
def crawl_interest_rates_current():
    countries_map = {
        "한국": "south-korea", "중국": "china", "일본": "japan", "미국": "united-states",
        "러시아": "russia", "캐나다": "canada", "호주": "australia", "멕시코": "mexico",
        "인도": "india", "영국": "united-kingdom", "프랑스": "france", "독일": "germany",
        "대만": "taiwan"
    }
    
    interest_data = []
    base_url = "https://tradingeconomics.com/{country_slug}/interest-rate"
    
    headers = {'User-Agent': random.choice(USER_AGENTS)}

    print("\n--- 금리 데이터를 크롤링 중 (TradingEconomics.com)... ---")
    for kr_name, slug in countries_map.items():
        # URL 슬러그가 'russia'로 정확히 들어가도록 수정
        if slug == "rusia": slug = "russia" 
        
        url = base_url.format(country_slug=slug)
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status() 
            soup = BeautifulSoup(response.text, 'html.parser')
            
            rate_value = "N/A"
            rate_element = None

            # 1. id="actual"을 가진 td 태그를 가장 먼저 시도 (사용자님 스크린샷 기반)
            rate_element = soup.find('td', {'id': 'actual'})
            
            # 2. id="ctl00_Content_lbValue"를 가진 span 태그 시도 (이전 버전에서 흔했던 패턴)
            if not rate_element:
                rate_element = soup.find('span', {'id': 'ctl00_Content_lbValue'})
            
            # 3. h4 태그에 class="number" 시도
            if not rate_element:
                rate_element = soup.find('h4', class_='number')
            
            # 4. h1 태그 내부에 %를 포함하는 span을 찾기
            if not rate_element:
                h1_tags = soup.find_all('h1')
                for h1 in h1_tags:
                    span_in_h1 = h1.find('span', string=re.compile(r'\d+\.?\d*%'))
                    # 값의 길이가 너무 길면 다른 의미일 가능성 배제
                    if span_in_h1 and len(span_in_h1.get_text(strip=True)) < 15: 
                        rate_element = span_in_h1
                        break

            # 5. 최종적으로 rate_element가 찾아졌다면 값 추출
            if rate_element:
                rate_value = rate_element.get_text(strip=True)
            else:
                # 6. 최후의 수단: 페이지 전체 텍스트에서 '숫자%' 패턴을 찾아보기 (정확도 낮음)
                text_content = soup.get_text()
                match = re.search(r'Interest Rate\s*(\d+\.?\d*%)', text_content, re.IGNORECASE)
                if match:
                    rate_value = match.group(1)
                else: # Fallback for just a percentage in the text
                    match = re.search(r'(\d+\.?\d*%)', text_content)
                    if match:
                        rate_value = match.group(1)
            
            if rate_value != "N/A":
                interest_data.append({"국가": kr_name, "기준 금리": rate_value})
            else:
                print(f"[경고] TradingEconomics에서 '{kr_name}' 금리 요소를 찾을 수 없습니다. (URL: {url})")
                interest_data.append({"국가": kr_name, "기준 금리": "N/A"})

            time.sleep(random.uniform(1, 2)) # 과도한 요청 방지
        except requests.exceptions.RequestException as e:
            print(f"[오류] '{kr_name}' 금리 크롤링 오류 (URL: {url}): {e}")
            interest_data.append({"국가": kr_name, "기준 금리": f"Error: {e}"})
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            print(f"[오류] '{kr_name}' 금리 파싱 오류 (URL: {url}): {e}")
            interest_data.append({"국가": kr_name, "기준 금리": f"Parse Error: {e}"})
            time.sleep(random.uniform(2, 3))
    
    print("--- 금리 데이터 가져오기 완료. ---")
    return pd.DataFrame(interest_data)

# --- 3. 과거 데이터 및 변화량 계산 함수 (기존 코드 재사용) ---
def calculate_change_data(current_value, historical_series):
    changes = {}
    today_timestamp = pd.Timestamp(datetime.now().date())

    periods = {
        "1일": timedelta(days=1), "1주일": timedelta(weeks=1), "1개월": timedelta(days=30), 
        "3개월": timedelta(days=90), "6개월": timedelta(days=180), "1년": timedelta(days=365)
    }

    for name, delta in periods.items():
        past_date_target = today_timestamp - delta
        
        available_dates = historical_series.index.normalize() 
        past_rate = current_value 
        try:
            idx = available_dates.searchsorted(past_date_target, side='right')
            if idx == 0:
                if not available_dates.empty:
                    past_rate = historical_series.iloc[0] 
            else:
                past_rate = historical_series.iloc[idx - 1]
        except IndexError: 
            pass 

        if pd.isna(past_rate) or past_rate == 0:
            changes[name] = {"절대값": 0.0, "퍼센트": "N/A"}
        else:
            abs_change = current_value - past_rate
            pct_change = (abs_change / past_rate) * 100
            changes[name] = {
                "절대값": abs_change, 
                "퍼센트": f"{pct_change:.2f}%"
            }
    return changes

def get_historical_fx_data_and_changes(ticker, current_rate):
    if ticker is None or ticker == "N/A":
        return None, None, None 

    try:
        print(f"  > '{ticker}' 과거 데이터 가져오는 중 (yfinance)...")
        # yfinance 데이터 기간을 더 늘려 웹에서 더 긴 추이를 볼 수 있도록
        data = yf.download(ticker, period="2y", interval="1d", progress=False) 
        if data.empty:
            print(f"[경고] '{ticker}'에 대한 yfinance 데이터를 찾을 수 없거나 불러오는 데 실패했습니다 (DataFrame empty).")
            return None, None, None

        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        close_prices = data['Close']
        if close_prices.empty:
            print(f"[경고] '{ticker}'에 대한 종가 데이터가 비어있습니다.")
            return None, None, None
        
        changes_data = calculate_change_data(current_rate, close_prices)
        
        return current_rate, close_prices, changes_data 
    except Exception as e:
        print(f"[오류] '{ticker}'의 과거 환율 데이터를 가져오는 중 오류 발생: {e}")
        return None, None, None

def get_historical_interest_rates_and_changes(country, current_rate_numeric):
    # 멕시코만 예시 데이터 (실제 TradingEconomics 크롤링 로직 추가 필요)
    if country == "멕시코":
        print(f"  > '{country}' 과거 금리 (예시 데이터) 가져오는 중...")
        dates = pd.to_datetime(pd.date_range(end=datetime.now(), periods=365, freq='D'))
        values = [current_rate_numeric - (i / 365) * 0.1 + (0.05 * (i % 100) / 100) for i in range(365)]
        historical_series = pd.Series(values, index=dates).round(3)
        
        changes_data = calculate_change_data(current_rate_numeric, historical_series)
        return current_rate_numeric, historical_series, changes_data
    else:
        print(f"[정보] '{country}'에 대한 과거 금리 데이터는 현재 지원되지 않습니다. TradingEconomics.com 등의 과거 데이터 테이블 크롤링 또는 다른 API를 활용해야 합니다.")
        return None, None, None


# --- Flask 라우트 (API 엔드포인트) ---

# 루트 경로('/')에 접속하면 index.html을 렌더링합니다.
@app.route('/')
def index():
    return render_template('index.html')

# 1. 모든 환율 및 금리 데이터 가져오기 (초기 로딩 및 새로고침)
@app.route('/api/data', methods=['GET'])
def get_all_data():
    exchange_df = get_exchange_rates_from_frankfurter()
    interest_df = crawl_interest_rates_current()

    # DataFrame을 JSON으로 변환
    # to_dict(orient='records')는 각 행을 하나의 사전으로 만들고 그 사전들의 리스트를 반환합니다.
    exchange_data = exchange_df.to_dict(orient='records')
    interest_data = interest_df.to_dict(orient='records')
    
    return jsonify({
        'exchangeRates': exchange_data,
        'interestRates': interest_data
    })

# 2. 특정 항목의 상세 정보 및 과거 데이터 가져오기
@app.route('/api/details', methods=['POST'])
def get_details():
    data = request.get_json()
    item_type = data.get('itemType')
    # itemId는 이제 프론트엔드에서 데이터를 식별하는 데 사용되고,
    # 백엔드에서는 historical_series를 직접 생성하므로 사용하지 않습니다.
    # originalIndex 대신 item_id로 일관성 있게 사용해도 좋습니다.
    current_rate = data.get('currentRate') # 현재 표시된 값
    ticker_or_country = data.get('tickerOrCountry') # Ticker 또는 국가명

    details_text = ""
    changes_text = ""
    graph_data_list = [] # 날짜와 값의 리스트로 반환
    
    try:
        if item_type == "fx":
            current_rate_val, historical_series, changes = get_historical_fx_data_and_changes(ticker_or_country, current_rate)
            
            if current_rate_val is not None:
                details_text = f"현재 환율: {current_rate_val:,.4f}"
            
            if changes:
                changes_text = "\n최근 변화량:\n"
                for period, change_data in changes.items():
                    abs_change = change_data['절대값']
                    pct_change = change_data['퍼센트']
                    sign = "+" if abs_change >= 0 else ""
                    changes_text += f"  {period} 변화: {sign}{abs_change:,.4f} ({pct_change})\n"
            
            if historical_series is not None and not historical_series.empty:
                # pandas Series를 (날짜, 값) 리스트로 변환
                # to_json(orient='split') 등 pandas 내장 함수를 사용할 수도 있습니다.
                # 여기서는 직접 리스트 컴프리헨션으로 변환합니다.
                graph_data_list = [{'date': str(idx.date()), 'value': val} for idx, val in historical_series.items()]

        elif item_type == "ir":
            # 금리 데이터는 현재 멕시코만 예시이므로, 해당 조건에서만 과거 데이터를 제공합니다.
            current_rate_val, historical_series, changes = get_historical_interest_rates_and_changes(ticker_or_country, current_rate)
            
            if current_rate_val is not None:
                details_text = f"현재 기준 금리: {current_rate_val:,.3f}%"
            
            if changes:
                changes_text = "\n최근 변화량:\n"
                for period, change_data in changes.items():
                    abs_change = change_data['절대값']
                    pct_change = change_data['퍼센트']
                    sign = "+" if abs_change >= 0 else ""
                    changes_text += f"  {period} 변화: {sign}{abs_change:,.3f}% ({pct_change})\n"
            
            if historical_series is not None and not historical_series.empty:
                graph_data_list = [{'date': str(idx.date()), 'value': val} for idx, val in historical_series.items()]
        
        return jsonify({
            'detailsText': details_text,
            'changesText': changes_text,
            'graphData': graph_data_list
        })
    except Exception as e:
        print(f"Error getting details for {item_type} {ticker_or_country}: {e}")
        # 오류 발생 시 클라이언트에게도 오류 메시지 전달
        return jsonify({'error': str(e), 'message': '상세 정보를 가져오는 중 오류가 발생했습니다.'}), 500

if __name__ == '__main__':
    # debug=True는 개발 중에 편리하지만, 실제 운영 환경에서는 False로 설정해야 합니다.
    app.run(debug=True, port=5000)
