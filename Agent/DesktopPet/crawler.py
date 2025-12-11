import requests
from bs4 import BeautifulSoup
import time

class SmartCrawler:
    def __init__(self):
        # 캐싱: {key: (data, timestamp)}
        self.cache = {}
        self.TTL = 300 # 5분 (300초)

    def _get_from_cache(self, key):
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.TTL:
                return data
        return None

    def _set_cache(self, key, data):
        self.cache[key] = (data, time.time())

    def get_weather(self):
        cached = self._get_from_cache("weather")
        if cached: return cached
        
        try:
            # 네이버 날씨 (서울)
            url = "https://search.naver.com/search.naver?query=서울날씨"
            res = requests.get(url)
            soup = BeautifulSoup(res.content, 'html.parser')
            
            # 구조가 자주 바뀌므로 예외처리 필수
            # 현재 기온
            temp = soup.find('div', {'class': 'temperature_text'}).text.strip().replace("현재 온도", "").strip()
            # 날씨 상태 (맑음, 흐림 등)
            status = soup.find('span', {'class': 'weather before_slash'}).text.strip()
            # 미세먼지?
            
            result = f"[서울 날씨]\n기온: {temp}\n상태: {status}"
            self._set_cache("weather", result)
            return result
        except Exception as e:
            return f"날씨 정보를 가져오는데 실패했습니다.\n({e})"

    def get_news(self, category):
        cache_key = f"news_{category}"
        cached = self._get_from_cache(cache_key)
        if cached: return cached
        
        # 네이버 뉴스 (섹션별 URL 변경 대응)
        cat_map = {"경제": "101", "과학": "105", "세계": "104"}
        sid1 = cat_map.get(category, "101")
        
        try:
            # 새로운 뉴스 섹션 URL 구조
            url = f"https://news.naver.com/section/{sid1}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.content, 'html.parser')
            
            headlines = []
            
            # Selector: sa_text_title
            items = soup.select('.sa_text_title')
            
            seen = set()
            count = 0
            for item in items:
                title = item.text.strip()
                if title not in seen:
                    headlines.append(f"• {title}")
                    seen.add(title)
                    count += 1
                if count >= 3:
                    break
                
            if not headlines:
                items = soup.select('.cluster_text_headline')
                for item in items[:3]:
                    headlines.append(f"• {item.text.strip()}")

            if not headlines:
                return f"[{category} 뉴스] 가져올 뉴스가 없어요."

            result = f"[{category} 뉴스] (속보)\n" + "\n".join(headlines)
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            return f"뉴스를 가져오는데 실패했습니다.\n({e})"

    def get_exchange_rate(self):
        """환율 정보 가져오기 (USD, JPY)"""
        cache_key = "exchange"
        cached = self._get_from_cache(cache_key)
        if cached: return cached
        
        try:
            # 네이버 금융 환율 페이지
            url = "https://finance.naver.com/marketindex/"
            # User-Agent 헤더 추가하여 요청 (기존 get_news에서 사용된 헤더 재활용)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0'}
            response = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # USD/KRW
            usd_element = soup.select_one('#exchangeList > li.on > a.head.usd > div > span.value')
            usd = usd_element.text.strip() if usd_element else "N/A"
            
            # JPY/KRW (100엔 기준)
            # 기존 selector: '#exchangeList > li.on > a.head.jpy > div > span.value'
            # 변경된 selector: '#exchangeList > li:nth-child(3) > a.head.jpy > div > span.value'
            jpy_element = soup.select_one('#exchangeList > li:nth-child(3) > a.head.jpy > div > span.value')
            jpy = jpy_element.text.strip() if jpy_element else "N/A"
            
            result = f"💵 USD: {usd}원 | 💴 JPY(100엔): {jpy}원"
            self._set_cache(cache_key, result)
            return result
        except Exception as e:
            return f"환율 정보를 가져올 수 없습니다 ({e})"
