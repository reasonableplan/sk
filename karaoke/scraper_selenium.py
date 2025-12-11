# scraper_selenium.py - 파트 1/3 (초기 설정 및 기본 도우미 함수)

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
import re
import os
from db_manager import DBManager
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def _get_selenium_driver():
    """Selenium WebDriver 인스턴스를 초기화하고 반환합니다."""
    chrome_options = Options()
    # 개발 중에는 --headless 옵션을 주석 처리하여 브라우저 동작을 직접 확인하는 것이 좋습니다.
    # chrome_options.add_argument("--headless") # 브라우저를 백그라운드에서 실행하려면 이 줄의 주석을 해제하세요.
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        chromedriver_path = os.path.join(current_dir, "chromedriver.exe")
        
        if not os.path.exists(chromedriver_path):
            raise FileNotFoundError(f"ChromeDriver not found at {chromedriver_path}")

        service = Service(executable_path=chromedriver_path) 
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except WebDriverException as e:
        print(f"WebDriver 초기화 오류: {e}")
        print("ChromeDriver가 PATH에 없거나 버전이 맞지 않거나, 실행 권한이 없을 수 있습니다.")
        print(f"현재 예상되는 ChromeDriver 경로: {chromedriver_path}")
        raise 
    except FileNotFoundError as e:
        print(f"파일 경로 오류: {e}")
        raise 


def _extract_song_info_from_search_result_area(parent_element):
    """
    accompaniment_search 페이지의 검색 결과 영역에서 노래 정보를 추출합니다.
    (div.music-search-list 내 ul.chart-list-area.music 구조)
    """
    extracted_songs = []
    
    # 통합 검색 페이지는 여러 div.music-search-list 블록을 가질 수 있습니다.
    # 각 블록(예: "곡 제목" 또는 "가수" 섹션)에서 노래를 추출합니다.
    # parent_element는 driver 또는 특정 div.music-search-list가 될 수 있습니다.
    search_blocks = parent_element.find_elements(By.CSS_SELECTOR, "div.music-search-list")
    
    if not search_blocks:
        # 가끔 직접 strType을 지정하면 div.music-search-list 없이 ul.chart-list-area.music이 바로 있을 수도 있습니다.
        # 이 경우를 대비해 직접 ul.chart-list-area.music을 찾아봅니다.
        try:
            chart_list = parent_element.find_element(By.CSS_SELECTOR, "ul.chart-list-area.music")
            song_items = chart_list.find_elements(By.CSS_SELECTOR, "li:not(:first-child)")
            for song_item in song_items:
                try:
                    grid_container = song_item.find_element(By.CSS_SELECTOR, "ul.grid-container.list.ico")
                    song_no_element = grid_container.find_element(By.CSS_SELECTOR, "li.grid-item.center.pos-type span.num2")
                    title_element = grid_container.find_element(By.CSS_SELECTOR, "li.grid-item.title3 p span")
                    artist_element = grid_container.find_element(By.CSS_SELECTOR, "li.grid-item.title4.singer p span")

                    song_no = song_no_element.text.strip()
                    title = title_element.text.strip()
                    artist = artist_element.text.strip()

                    if song_no and title and artist:
                        extracted_songs.append({
                            'song_no': song_no, 'title': title, 'artist': artist,
                            'composer': '정보 없음', 'lyricist': '정보 없음', 'lyrics': '가사 정보 없음'
                        })
                except NoSuchElementException:
                    continue
                except Exception as e:
                    print(f"  단일 노래 항목 파싱 중 오류: {e}")
            return extracted_songs
        except NoSuchElementException:
            # print("  'div.music-search-list' 또는 'ul.chart-list-area.music'을 찾을 수 없습니다.")
            return []

    for block in search_blocks:
        # 이 블록 안에 h2 태그가 있을 수 있지만, strType 지정 검색에서는 섹션 구분이 명확하지 않을 수 있습니다.
        # 바로 ul.chart-list-area.music을 찾습니다.
        try:
            chart_list = block.find_element(By.CSS_SELECTOR, "ul.chart-list-area.music")
            song_items = chart_list.find_elements(By.CSS_SELECTOR, "li:not(:first-child)") 
            
            for song_item in song_items:
                try:
                    grid_container = song_item.find_element(By.CSS_SELECTOR, "ul.grid-container.list.ico")
                    
                    song_no_element = grid_container.find_element(By.CSS_SELECTOR, "li.grid-item.center.pos-type span.num2")
                    title_element = grid_container.find_element(By.CSS_SELECTOR, "li.grid-item.title3 p span")
                    artist_element = grid_container.find_element(By.CSS_SELECTOR, "li.grid-item.title4.singer p span")

                    song_no = song_no_element.text.strip()
                    title = title_element.text.strip()
                    artist = artist_element.text.strip()

                    if not song_no or not title or not artist:
                        continue 

                    song_data = {
                        'song_no': song_no,
                        'title': title,
                        'artist': artist,
                        'composer': '정보 없음', 
                        'lyricist': '정보 없음',  
                        'lyrics': '가사 정보 없음' 
                    }
                    extracted_songs.append(song_data)

                except StaleElementReferenceException:
                    continue 
                except NoSuchElementException:
                    continue 
                except Exception as e:
                    print(f"  스크래핑 중 예상치 못한 오류 (노래 항목): {e}")
                    continue
        except NoSuchElementException:
            continue # 이 블록에 ul.chart-list-area.music이 없으면 다음 블록으로 이동
            
    return extracted_songs


def _get_song_details_from_detail_page(driver, song_no):
    """
    주어진 song_no를 이용하여 상세 페이지에서 노래 정보를 스크래핑합니다.
    """
    detail_url = f"https://www.tjmedia.com/song/songDetail.asp?songNo={song_no}"
    try:
        driver.get(detail_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.song_area_box"))
        )
    except TimeoutException:
        print(f"상세 페이지 로드 시간 초과: {detail_url}")
        return None
    except WebDriverException as e:
        print(f"상세 페이지 접속 오류 ({detail_url}): {e}")
        return None

    data = {'song_no': song_no}
    
    try:
        data['title'] = driver.find_element(By.CSS_SELECTOR, "div.song_area_box > h3 > span").text.strip()
    except NoSuchElementException:
        data['title'] = "제목 없음"
    
    try:
        lyrics_info_elements = driver.find_elements(By.CSS_SELECTOR, "#lyrics_area p")
        artist_line = ""
        composer_lyricist_line = ""

        if len(lyrics_info_elements) > 0:
            artist_line = lyrics_info_elements[0].text.strip()
        if len(lyrics_info_elements) > 1:
            composer_lyricist_line = lyrics_info_elements[1].text.strip()

        artist_match = re.search(r'가수\s*:\s*(.+)', artist_line)
        data['artist'] = artist_match.group(1).strip() if artist_match else "가수 정보 없음"
        
        composer_match = re.search(r'작곡\s*:\s*(.+?)(?:\s*작사\s*:|$)', composer_lyricist_line)
        lyricist_match = re.search(r'작사\s*:\s*(.+)', composer_lyricist_line)

        data['composer'] = composer_match.group(1).strip() if composer_match else "작곡가 정보 없음"
        data['lyricist'] = lyricist_match.group(1).strip() if lyricist_match else "작사가 정보 없음"
        
    except NoSuchElementException:
        data['artist'] = "가수 정보 없음"
        data['composer'] = "작곡가 정보 없음"
        data['lyricist'] = "작사가 정보 없음"
    except Exception as e: 
        print(f"곡번호 {song_no}의 상세 정보 파싱 오류 (메타데이터): {e}")
        data['artist'] = "가수 정보 없음"
        data['composer'] = "작곡가 정보 없음"
        data['lyricist'] = "작사가 정보 없음"

    try:
        lyrics_element = driver.find_element(By.CSS_SELECTOR, "div.song_lyrics_list pre")
        data['lyrics'] = lyrics_element.text.strip()
    except NoSuchElementException:
        data['lyrics'] = "가사 정보 없음"
    except Exception as e:
        print(f"곡번호 {song_no}의 가사 추출 오류: {e}")
        data['lyrics'] = "가사 정보 없음"
            
    return data


def scrape_single_song_details(song_no):
    """
    주어진 곡번호의 상세 정보(작곡가, 작사가, 가사 포함)를 TJ 미디어 웹사이트에서 스크래핑합니다.
    """
    local_db_manager = DBManager()
    if not local_db_manager.connect():
        print("ERROR: scrape_single_song_details 내부 DB 연결 실패.")
        return None

    driver = None
    try:
        driver = _get_selenium_driver()
        print(f"곡번호 {song_no} 상세 정보 스크래핑 시작...")
        song_details = _get_song_details_from_detail_page(driver, song_no)
        
        if song_details:
            local_db_manager.insert_or_update_song(song_details)
            print(f"곡번호 {song_no} '{song_details['title']}' 상세 정보 DB 저장 완료.")
        else:
            print(f"곡번호 {song_no} 상세 정보를 가져오지 못했습니다.")
        return song_details
    except Exception as e:
        print(f"곡번호 {song_no} 상세 스크래핑 중 오류 발생: {e}")
        return None
    finally:
        if driver:
            driver.quit()
        local_db_manager.disconnect()

# scraper_selenium.py - 파트 2/3 (accompaniment_search 페이지 스크래핑 로직)

# --- (파트 1/3 코드 바로 아래에 이어서 붙여넣기) ---

def _scrape_accompaniment_search_page_with_pagination(driver, search_text, str_type_code, max_pages=100):
    """
    주신 URL 패턴을 사용하여 accompaniment_search 페이지를 페이지네이션하며 스크래핑합니다.
    str_type_code: '1' (곡 제목), '2' (가수 이름)
    """
    base_url = "https://www.tjmedia.com/song/accompaniment_search"
    all_songs = []
    unique_song_nos = set()
    
    page_no = 1
    previous_page_data_hash = None # 페이지 내용 변화 감지를 위한 해시

    while page_no <= max_pages:
        params = {
            'pageNo': page_no,
            'pageRowCnt': 100, # 주신 URL 패턴에 따라 30으로 고정
            'strSotrGubun': 'ASC',
            'strSortType': '',
            'nationType': '',
            'strType': str_type_code, # '1' 또는 '2'
            'searchTxt': search_text
        }
        
        full_url = f"{base_url}?{urlencode(params, doseq=True)}"
        print(f"  요청 URL (accompaniment_search): {full_url}")

        try:
            driver.get(full_url)
            
            # 페이지 내용이 완전히 로드될 때까지 기다립니다.
            # div.content_wrap_search나 ul.chart-list-area.music이 나타날 때까지 기다립니다.
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.content_wrap_search, ul.chart-list-area.music"))
            )
            
            # 페이지의 가시적인 내용의 해시를 계산하여 이전 페이지와 비교
            # body 전체의 innerHTML을 사용하면 페이지네이션이 끝났을 때를 더 잘 감지할 수 있습니다.
            current_page_body_html = driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")
            current_page_data_hash = hash(current_page_body_html)

            if previous_page_data_hash is not None and current_page_data_hash == previous_page_data_hash:
                print(f"  페이지 {page_no}에서 이전 페이지와 동일한 내용이 감지되었습니다. 스크래핑 종료.")
                break
            previous_page_data_hash = current_page_data_hash

            current_page_songs = _extract_song_info_from_search_result_area(driver)
            
            new_songs_added_this_page = 0
            for song in current_page_songs:
                if song['song_no'] not in unique_song_nos:
                    all_songs.append(song)
                    unique_song_nos.add(song['song_no'])
                    new_songs_added_this_page += 1
            
            # 현재 페이지에서 아무 노래도 추출되지 않았거나 (첫 페이지가 아니면서),
            # 또는 새로운 노래가 추가되지 않았다면 pagination 종료
            if (not current_page_songs and page_no > 1) or \
               (new_songs_added_this_page == 0 and len(current_page_songs) > 0 and page_no > 1):
                print(f"  페이지 {page_no}에서 더 이상 새로운 노래를 찾을 수 없습니다. 스크래핑 종료.")
                break

            print(f"  페이지 {page_no}에서 {len(current_page_songs)}개 노래 추출 (새로운 노래: {new_songs_added_this_page}개). 현재 총 노래 수: {len(all_songs)}개.")

        except TimeoutException:
            print(f"  페이지 로드 시간 초과 또는 결과 로드 실패: {full_url}. 스크래핑 종료.")
            break
        except WebDriverException as e:
            print(f"  WebDriver 오류 ({full_url}): {e}. 스크래핑 종료.")
            break
        except Exception as e:
            print(f"  페이지 스크래핑 중 오류 (URL: {full_url}): {e}")
            break
        
        page_no += 1
        time.sleep(1) # 서버 부하를 줄이기 위한 지연

    return all_songs


def web_search_tj_media_by_song_title(query_text):
    """
    TJ 미디어에서 '곡 제목'으로 검색하여 모든 결과를 스크래핑합니다. (Selenium 기반)
    strType=1 사용 (주신 URL 패턴 반영)
    """
    driver = None
    try:
        driver = _get_selenium_driver()
        print(f"TJ 미디어 곡 제목 검색 시작: '{query_text}' (Selenium, accompaniment_search)")
        songs = _scrape_accompaniment_search_page_with_pagination(driver, query_text, '1') # strType '1'은 곡명
        print(f"TJ 미디어 곡 제목 검색 '{query_text}' 완료. 총 {len(songs)}개 결과 발견.")
        return songs
    except Exception as e:
        print(f"TJ 미디어 곡 제목 검색 '{query_text}' 중 예상치 못한 오류 발생: {e}")
        return []
    finally:
        if driver:
            driver.quit()


def web_search_tj_media_by_artist(query_text):
    """
    TJ 미디어에서 '가수'로 검색하여 모든 결과를 스크래핑합니다. (Selenium 기반)
    strType=2 사용 (주신 URL 패턴 반영)
    """
    driver = None
    try:
        driver = _get_selenium_driver()
        print(f"TJ 미디어 가수 검색 시작: '{query_text}' (Selenium, accompaniment_search)")
        songs = _scrape_accompaniment_search_page_with_pagination(driver, query_text, '2') # strType '2'는 가수이름
        print(f"TJ 미디어 가수 검색 '{query_text}' 완료. 총 {len(songs)}개 결과 발견.")
        return songs
    except Exception as e:
        print(f"TJ 미디어 가수 검색 '{query_text}' 중 예상치 못한 오류 발생: {e}")
        return []
    finally:
        if driver:
            driver.quit()

# scraper_selenium.py - 파트 3/3 (전체 데이터 스크래핑 함수)

# --- (파트 2/3 코드 바로 아래에 이어서 붙여넣기) ---

def scrape_tj_songs_to_db_selenium():
    """
    TJ Media 웹사이트에서 모든 노래 데이터를 스크래핑하여 DB에 저장합니다.
    Selenium을 사용하여 초성/알파벳/숫자별로 곡명 및 가수 검색을 수행합니다.
    """
    local_db_manager = DBManager()
    if not local_db_manager.connect():
        print("ERROR: scrape_tj_songs_to_db_selenium 내부 DB 연결 실패.")
        return 0

    total_scraped_songs_count = 0
    processed_song_nos = set() 

    try:
        existing_songs = local_db_manager.get_song() 
        for song in existing_songs:
            processed_song_nos.add(song['song_no'])
        print(f"DB에 이미 {len(processed_song_nos)}개의 노래가 존재합니다. 기존 노래는 스킵합니다.")

        search_chars = (
            ['ㄱ', 'ㄴ', 'ㄷ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅅ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'] + 
            ['가', '나', '다', '라', '마', '바', '사', '아', '자', '차', '카', '타', '파', '하'] + 
            ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'] + 
            ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] 
        )

        # Selenium driver는 한 번만 생성하여 여러 검색에 재활용합니다.
        # 주의: driver를 계속 재활용하면 메모리 누수가 발생할 수 있으므로, 주기적으로 quit() 후 다시 생성하는 로직을 고려할 수 있습니다.
        # 여기서는 전체 스크래핑 시작 시 한 번 생성하고 끝날 때 한 번 종료합니다.
        temp_driver = _get_selenium_driver() 

        for query_char in search_chars:
            print(f"\n--- 전체 스크래핑: '{query_char}' 검색어 처리 시작 (Selenium) ---")

            # 1. '곡 제목' 카테고리 스크래핑 (strType=1)
            print(f"  '{query_char}' (곡 제목) 검색 시작...")
            songs_from_title = _scrape_accompaniment_search_page_with_pagination(temp_driver, query_char, '1')
            new_songs_title = 0
            for song_data in songs_from_title:
                if song_data['song_no'] not in processed_song_nos:
                    local_db_manager.insert_or_update_song(song_data)
                    processed_song_nos.add(song_data['song_no'])
                    total_scraped_songs_count += 1
                    new_songs_title += 1
            print(f"  '{query_char}' (곡 제목)에서 {len(songs_from_title)}개 노래 중 {new_songs_title}개 추가/업데이트.")

            time.sleep(1) # 섹션 간 지연

            # 2. '가수' 카테고리 스크래핑 (strType=2)
            print(f"  '{query_char}' (가수) 검색 시작...")
            songs_from_artist = _scrape_accompaniment_search_page_with_pagination(temp_driver, query_char, '2')
            new_songs_artist = 0
            for song_data in songs_from_artist:
                if song_data['song_no'] not in processed_song_nos:
                    local_db_manager.insert_or_update_song(song_data)
                    processed_song_nos.add(song_data['song_no'])
                    total_scraped_songs_count += 1
                    new_songs_artist += 1
            print(f"  '{query_char}' (가수)에서 {len(songs_from_artist)}개 노래 중 {new_songs_artist}개 추가/업데이트.")
            
            time.sleep(2) # 각 query_char 처리 완료 후 약간 더 긴 지연

    except Exception as e:
        print(f"전체 스크래핑 중 치명적인 오류 발생: {e}")
        # 오류 발생 시 스택 트레이스 출력
        import traceback
        traceback.print_exc()
    finally:
        if temp_driver:
            temp_driver.quit() # 전체 스크래핑이 끝나면 드라이버 종료
        local_db_manager.disconnect()
    
    print(f"\n총 {total_scraped_songs_count}개의 노래 데이터를 새로 스크래핑하여 DB에 추가/업데이트했습니다.")
    return total_scraped_songs_count
