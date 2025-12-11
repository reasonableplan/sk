# main.py - 파트 1/5 (클래스 정의 및 __init__ 메서드 초기 UI 설정)

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import threading
from concurrent.futures import ThreadPoolExecutor
import os 

from db_manager import DBManager
# scraper_selenium에서 함수들을 임포트합니다.
from scraper_selenium import scrape_tj_songs_to_db_selenium, web_search_tj_media_by_song_title, web_search_tj_media_by_artist, scrape_single_song_details 

class TJKaraokeApp:
    def __init__(self, master):
        self.master = master
        master.title("TJ 노래방 검색 및 가사 뷰어")
        master.geometry("1200x700") # 창 크기 확장

        self.default_font = ("Malgun Gothic", 10)
        self.heading_font = ("Malgun Gothic", 12, "bold")
        self.lyrics_font = ("Malgun Gothic", 11)

        # NEW: ttk.Button 스타일 정의 (wraplength 적용을 위해)
        self.style = ttk.Style()
        # '재생목록에 추가' 텍스트에 맞게 wraplength를 조정합니다.
        # 이전에 70, 120을 시도했으나, 텍스트가 한 줄로 표시될 최소 너비를 찾습니다.
        # 폰트에 따라 달라질 수 있으므로, 대략 100~110 정도가 적절해 보입니다.
        self.style.configure("Wrapped.TButton", wraplength=100, anchor="center") 

        self.selected_song_data = None # 현재 선택된 검색 결과 노래 데이터 (단일 선택용)
        self.selected_playlist_id = None # 현재 "내 재생목록" 탭에서 선택된 재생목록 ID
        self.selected_playlist_name = None # 현재 "내 재생목록" 탭에서 선택된 재생목록 이름
        self.all_playlists_data = [] # 모든 재생목록 데이터를 저장할 리스트

        # 메인 스레드에서 사용될 DBManager 인스턴스 (스크래핑 스레드에서는 별도 생성)
        self.db_manager = DBManager()
        if not self.db_manager.connect():
            messagebox.showerror("DB 연결 오류", "데이터베이스 연결에 실패했습니다. 프로그램을 종료합니다.")
            master.destroy()
            return
        
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 쓰레드 풀 초기화 (웹 검색 등 비동기 작업을 위한)
        self.executor = ThreadPoolExecutor(max_workers=2) 

        # 1. 검색 섹션
        self.search_frame = ttk.LabelFrame(master, text="노래 검색", padding="10 10 10 10")
        self.search_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # 검색 타입 선택 콤보박스 추가
        self.search_type_label = ttk.Label(self.search_frame, text="검색 타입:", font=self.default_font)
        self.search_type_label.pack(side=tk.LEFT, padx=5, pady=5)
        self.search_type_var = tk.StringVar(value="통합 검색") # 기본값 설정
        self.search_type_combobox = ttk.Combobox(self.search_frame, textvariable=self.search_type_var,
                                                 values=["통합 검색", "곡 제목", "가수"], # 곡 제목 (strType=1), 가수 (strType=2)
                                                 font=self.default_font, width=10, state="readonly")
        self.search_type_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.search_label = ttk.Label(self.search_frame, text="검색어:", font=self.default_font)
        self.search_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.search_entry = ttk.Entry(self.search_frame, width=40, font=self.default_font)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", self.perform_search_event)

        self.search_button = ttk.Button(self.search_frame, text="검색", command=self.perform_search)
        self.search_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 스크래핑 버튼
        self.scrape_button = ttk.Button(self.search_frame, text="전체 데이터 스크래핑", command=self.start_full_scraping)
        self.scrape_button.pack(side=tk.LEFT, padx=5, pady=5)
        

        # 메인 콘텐츠 프레임
        self.main_content_frame = ttk.Frame(master)
        self.main_content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 2. 검색 결과 섹션
        self.results_frame = ttk.LabelFrame(self.main_content_frame, text="검색 결과", padding="10 10 10 10")
        # padx=(0, 1)로 변경: 버튼과의 간격을 최소화
        self.results_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 1)) 

        # Treeview 다중 선택 활성화 (selectmode='extended')
        self.results_tree = ttk.Treeview(self.results_frame, columns=("song_no", "title", "artist"), show="headings", height=15, selectmode='extended')
        # side=tk.LEFT 유지
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) 

        self.results_tree.heading("song_no", text="곡번호", anchor=tk.CENTER)
        self.results_tree.heading("title", text="제목", anchor=tk.W)
        self.results_tree.heading("artist", text="가수", anchor=tk.W)

        self.results_tree.column("song_no", width=80, anchor=tk.CENTER)
        self.results_tree.column("title", width=200)
        self.results_tree.column("artist", width=150)

        # 스크롤바는 Treeview와 같은 프레임에 묶고, Treeview 옆에 배치합니다.
        self.results_tree_scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=self.results_tree_scrollbar.set)

        self.results_tree.bind("<<TreeviewSelect>>", self.on_search_result_select) # 다중 선택 이벤트
        
        # ----------------------------------------------------
        # NEW: 버튼을 담을 프레임 (검색 결과와 노래 정보 탭 사이에 위치)
        self.middle_button_frame = ttk.Frame(self.main_content_frame)
        # fill=tk.Y를 사용하여 프레임이 수직으로 확장되도록 합니다.
        # padx는 제거하여 이웃 위젯의 padx로 간격을 조절합니다.
        self.middle_button_frame.pack(side=tk.LEFT, fill=tk.Y) 

        # '재생목록에 추가' 버튼을 이 프레임으로 이동
        self.add_selected_to_playlist_button = ttk.Button(
            self.middle_button_frame,
            text="재생목록에 추가", # 텍스트 변경
            command=self.open_add_selected_to_playlist_dialog,
            state=tk.DISABLED,
            style="Wrapped.TButton" # 새로 정의한 스타일 적용
        )
        # pady=(35, 0)으로 다시 조정: LabelFrame 제목, padding, Treeview 헤더를 고려한 값
        # 이 값은 가장 미세한 조정이 필요한 부분이며, 실행 후 원하는 위치에 맞게 조절하세요.
        self.add_selected_to_playlist_button.pack(side=tk.TOP, pady=(35, 0), anchor=tk.CENTER)
        # ----------------------------------------------------


        # 3. 노래 상세 정보 및 재생목록 섹션
        self.right_panel_notebook = ttk.Notebook(self.main_content_frame)
        # padx=(1, 0)으로 변경: 버튼과의 간격을 최소화
        self.right_panel_notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(1, 0))

        # 3-1. 노래 상세 정보 탭
        self.details_tab = ttk.Frame(self.right_panel_notebook, padding="10")
        self.right_panel_notebook.add(self.details_tab, text="노래 정보")
        self.setup_details_tab(self.details_tab)

        # 3-2. 내 재생목록 탭
        self.playlists_tab = ttk.Frame(self.right_panel_notebook, padding="10")
        self.right_panel_notebook.add(self.playlists_tab, text="내 재생목록")
        self.setup_playlists_tab(self.playlists_tab) # setup_playlists_tab은 파트 4/5에 정의됨
        
        self.load_playlists() # load_playlists는 파트 4/5에 정의됨


    def on_closing(self):
        if messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?"):
            if self.executor:
                self.executor.shutdown(wait=True)
            if self.db_manager:
                self.db_manager.disconnect()
            self.master.destroy()

    # --- 노래 상세 정보 탭 관련 메서드 ---
    def setup_details_tab(self, parent_frame):
        self.detail_info_label = ttk.Label(parent_frame, text="선택된 노래 정보:", font=self.heading_font)
        self.detail_info_label.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))

        self.detail_song_no_label = ttk.Label(parent_frame, text="곡번호: ", font=self.default_font)
        self.detail_song_no_label.pack(side=tk.TOP, anchor=tk.W)
        self.detail_title_label = ttk.Label(parent_frame, text="제목: ", font=self.default_font)
        self.detail_title_label.pack(side=tk.TOP, anchor=tk.W)
        self.detail_artist_label = ttk.Label(parent_frame, text="가수: ", font=self.default_font)
        self.detail_artist_label.pack(side=tk.TOP, anchor=tk.W)
        self.detail_composer_label = ttk.Label(parent_frame, text="작곡가: ", font=self.default_font)
        self.detail_composer_label.pack(side=tk.TOP, anchor=tk.W)
        self.detail_lyricist_label = ttk.Label(parent_frame, text="작사가: ", font=self.default_font)
        self.detail_lyricist_label.pack(side=tk.TOP, anchor=tk.W)

        self.scrape_details_button = ttk.Button(parent_frame, text="선택 노래 상세 정보 가져오기", command=self.start_single_song_details_scraping, state=tk.DISABLED)
        self.scrape_details_button.pack(side=tk.TOP, pady=(5, 10))


        self.lyrics_label = ttk.Label(parent_frame, text="\n--- 가 사 ---", font=self.heading_font)
        self.lyrics_label.pack(side=tk.TOP, anchor=tk.W, pady=(10, 5))

        self.lyrics_text_widget = scrolledtext.ScrolledText(parent_frame, wrap=tk.WORD, width=60, height=20, font=self.lyrics_font)
        self.lyrics_text_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.lyrics_text_widget.insert(tk.END, "검색 후 노래를 선택하면 가사가 여기에 표시됩니다.")
        self.lyrics_text_widget.config(state=tk.DISABLED) # This is line 218 in the provided code structure.




# main.py - 파트 3/5 (검색 기능 및 스크래핑 관련 메서드)

# --- (파트 2/5 코드 바로 아래에 이어서 붙여넣기) ---
    def update_details_view(self, song_data):
        self.detail_song_no_label.config(text=f"곡번호: {song_data.get('song_no', '')}")
        self.detail_title_label.config(text=f"제목: {song_data.get('title', '')}")
        self.detail_artist_label.config(text=f"가수: {song_data.get('artist', '')}")
        # '정보 없음'이면 기본값 사용
        self.detail_composer_label.config(text=f"작곡가: {song_data.get('composer', '정보 없음')}") 
        self.detail_lyricist_label.config(text=f"작사가: {song_data.get('lyricist', '정보 없음')}")   

        self.lyrics_text_widget.config(state=tk.NORMAL)
        self.lyrics_text_widget.delete(1.0, tk.END)
        self.lyrics_text_widget.insert(tk.END, song_data.get('lyrics', '가사 정보 없음.')) 
        self.lyrics_text_widget.config(state=tk.DISABLED)

        # 상세 정보 가져오기 버튼 활성화/비활성화 로직
        if self.selected_song_data: # 이 부분은 self.selected_song_data가 현재 선택된 노래 정보와 다를 수 있으므로 selected_song_data를 직접 사용하도록 조정할 수 있음.
                                    # 하지만 여기서는 기존 로직 유지.
            if (self.selected_song_data.get('composer') == '정보 없음' or
                self.selected_song_data.get('lyricist') == '정보 없음' or
                self.selected_song_data.get('lyrics') == '가사 정보 없음'):
                self.scrape_details_button.config(state=tk.NORMAL)
            else:
                self.scrape_details_button.config(state=tk.DISABLED)
        else:
            self.scrape_details_button.config(state=tk.DISABLED)
            
    def clear_details_view(self):
        self.selected_song_data = None 
        self.scrape_details_button.config(state=tk.DISABLED)

        self.detail_song_no_label.config(text="곡번호: ")
        self.detail_title_label.config(text="제목: ")
        self.detail_artist_label.config(text="가수: ")
        self.detail_composer_label.config(text="작곡가: ")
        self.detail_lyricist_label.config(text="작사가: ")

        self.lyrics_text_widget.config(state=tk.NORMAL)
        self.lyrics_text_widget.delete(1.0, tk.END)
        self.lyrics_text_widget.insert(tk.END, "노래를 선택해 주세요.")
        self.lyrics_text_widget.config(state=tk.DISABLED)
    # --- 검색 관련 메서드 ---
    def perform_search_event(self, event):
        self.perform_search()

    def perform_search(self):
        search_query = self.search_entry.get().strip()
        search_type = self.search_type_var.get()

        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.clear_details_view() 
        self.add_selected_to_playlist_button.config(state=tk.DISABLED) # 검색 결과 초기화 시 버튼 비활성화

        if not search_query:
            messagebox.showwarning("검색 오류", "검색어를 입력해주세요.")
            return

        messagebox.showinfo("검색 시작", f"'{search_query}' ({search_type})에 대한 검색을 시작합니다. TJ 미디어 웹사이트에서 최신 데이터를 가져옵니다. 잠시만 기다려주세요...")
        
        self.search_button.config(state=tk.DISABLED, text="웹 검색 중...")
        
        # 선택된 검색 타입에 따라 다른 스크래퍼 함수 호출
        if search_type == "곡 제목":
            future = self.executor.submit(web_search_tj_media_by_song_title, search_query)
        elif search_type == "가수":
            future = self.executor.submit(web_search_tj_media_by_artist, search_query)
        elif search_type == "통합 검색":
            def unified_search_task(query):
                print(f"통합 검색 태스크 시작: {query}")
                title_results = web_search_tj_media_by_song_title(query)
                artist_results = web_search_tj_media_by_artist(query)
                
                combined_results_map = {}
                for song in title_results + artist_results:
                    combined_results_map[song['song_no']] = song
                print(f"통합 검색 태스크 완료: 총 {len(combined_results_map)}개 결과")
                return list(combined_results_map.values())
            
            future = self.executor.submit(unified_search_task, search_query)
        else:
            messagebox.showerror("검색 오류", "알 수 없는 검색 타입입니다.")
            self.search_button.config(state=tk.NORMAL, text="검색")
            return

        future.add_done_callback(lambda f: self.master.after(0, self._process_web_search_results, search_query, f.result()))


    def _process_web_search_results(self, search_query, web_results):
        # UI 업데이트이므로 메인 스레드에서 실행됨
        try:
            all_results_map = {} 
            
            # 1. 먼저 로컬 DB에서 해당 검색어에 대한 기존 노래들을 모두 가져옵니다.
            current_local_results = self.db_manager.get_song(query_text=search_query) 
            for song in current_local_results:
                all_results_map[song['song_no']] = song

            # 2. 웹 검색 결과를 처리합니다.
            for web_song in web_results:
                song_no = web_song['song_no']

                # 로컬 DB에 노래가 이미 존재하는 경우
                if song_no in all_results_map:
                    existing_song = all_results_map[song_no]
                    
                    existing_song['title'] = web_song['title']
                    existing_song['artist'] = web_song['artist']

                    existing_song['composer'] = web_song.get('composer') if web_song.get('composer') != '정보 없음' else existing_song.get('composer', '정보 없음')
                    existing_song['lyricist'] = web_song.get('lyricist') if web_song.get('lyricist') != '정보 없음' else existing_song.get('lyricist', '정보 없음')
                    existing_song['lyrics'] = web_song.get('lyrics') if web_song.get('lyrics') != '가사 정보 없음' else existing_song.get('lyrics', '가사 정보 없음')
                    
                    self.db_manager.insert_or_update_song(existing_song)
                    all_results_map[song_no] = existing_song
                else:
                    self.db_manager.insert_or_update_song(web_song)
                    updated_song = self.db_manager.get_song(song_no=song_no)
                    if updated_song:
                        all_results_map[song_no] = updated_song[0]
            
            # 최종 결과 Treeview에 표시
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            final_display_results = list(all_results_map.values())
            final_display_results.sort(key=lambda x: x.get('title', '')) 

            for song in final_display_results:
                # 다중 선택 기능만 사용하므로 image= 와 tags= 옵션 제거
                self.results_tree.insert("", tk.END, values=(song["song_no"], song["title"], song["artist"]), iid=song["song_no"])

            if not final_display_results:
                messagebox.showinfo("검색 결과", f"'{search_query}'에 대한 검색 결과가 없습니다.")
            else:
                messagebox.showinfo("웹 검색 완료", f"'{search_query}'에 대한 웹 검색 결과 {len(web_results)}개를 포함하여 총 {len(final_display_results)}개의 결과를 찾았습니다.")

        except Exception as e:
            messagebox.showerror("웹 검색 처리 오류", f"웹 검색 결과 처리 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.search_button.config(state=tk.NORMAL, text="검색")

    def on_search_result_select(self, event): # TreeviewSelect 이벤트 핸들러
        selected_items = self.results_tree.selection() # 선택된 모든 항목의 iid를 가져옴
        
        if selected_items:
            # 첫 번째 선택된 노래의 상세 정보만 표시 (기존 동작 유지)
            # Treeview.selection()은 iid 리스트를 반환합니다.
            first_selected_item_iid = selected_items[0] 
            
            selected_songs_data = self.db_manager.get_song(song_no=first_selected_item_iid)
            selected_song = selected_songs_data[0] if selected_songs_data else None

            if selected_song:
                self.selected_song_data = selected_song 
                self.update_details_view(selected_song)
            else:
                self.clear_details_view()
            
            # 선택된 노래가 하나 이상이면 일괄 추가 버튼 활성화
            self.add_selected_to_playlist_button.config(state=tk.NORMAL)
        else:
            self.clear_details_view()
            self.add_selected_to_playlist_button.config(state=tk.DISABLED)
    
    def start_full_scraping(self):
        if not self.db_manager.is_connected():
            messagebox.showerror("DB 연결 오류", "데이터베이스 연결이 끊어져 스크래핑을 시작할 수 없습니다.")
            return

        response = messagebox.askyesno("스크래핑 시작", "TJ미디어 웹사이트에서 모든 노래 데이터를 스크래핑하여 DB에 저장하시겠습니까?\n이 작업은 시간이 오래 걸릴 수 있으며, 브라우저가 자동 실행됩니다. (진행 상황은 콘솔에 표시됩니다.)")
        if response:
            self.scrape_button.config(state=tk.DISABLED)
            future = self.executor.submit(scrape_tj_songs_to_db_selenium)
            future.add_done_callback(self._full_scraping_callback)

    def _full_scraping_callback(self, future):
        try:
            total_scraped = future.result()
            self.master.after(0, lambda: messagebox.showinfo("스크래핑 완료", f"총 {total_scraped}개의 노래 데이터를 스크래핑하여 DB에 추가/업데이트했습니다."))
        except Exception as e:
            error_message = f"스크래핑 중 오류가 발생했습니다: {e}\n자세한 내용은 콘솔을 확인해주세요."
            if "WebDriverException" in str(e):
                error_message = "WebDriver 초기화 오류 또는 브라우저와 WebDriver 버전 불일치.\n" + error_message
            self.master.after(0, lambda: messagebox.showerror("스크래핑 오류", error_message))
            print(f"ERROR: Selenium 스크래핑 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.master.after(0, lambda: self.scrape_button.config(state=tk.NORMAL))


    def start_single_song_details_scraping(self):
        if not self.selected_song_data:
            messagebox.showwarning("선택 오류", "상세 정보를 가져올 노래를 선택해주세요.")
            return
        
        song_no = self.selected_song_data['song_no']
        messagebox.showinfo("상세 정보 가져오기", f"곡번호 {song_no}의 상세 정보를 웹에서 가져옵니다. 잠시만 기다려주세요...")
        self.scrape_details_button.config(state=tk.DISABLED, text="가져오는 중...")

        future = self.executor.submit(scrape_single_song_details, song_no)
        future.add_done_callback(self._single_song_details_scraping_callback)

    def _single_song_details_scraping_callback(self, future):
        try:
            updated_song_data = future.result()
            if updated_song_data:
                refreshed_song = self.db_manager.get_song(song_no=updated_song_data['song_no'])
                if refreshed_song:
                    self.selected_song_data = refreshed_song[0]
                    self.update_details_view(self.selected_song_data)
                    messagebox.showinfo("가져오기 완료", f"'{updated_song_data['title']}'의 상세 정보가 업데이트되었습니다.")
                else:
                    messagebox.showerror("가져오기 오류", "DB에서 업데이트된 노래 정보를 가져오지 못했습니다.")
            else:
                messagebox.showerror("가져오기 실패", "노래 상세 정보 가져오기에 실패했습니다.")
        except Exception as e:
            messagebox.showerror("상세 정보 스크래핑 오류", f"노래 상세 정보 스크래핑 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.scrape_details_button.config(state=tk.NORMAL, text="선택 노래 상세 정보 가져오기")

# main.py - 파트 4/5 (재생목록 탭 UI 설정 및 관련 메서드)

# --- (파트 3/5 코드 바로 아래에 이어서 붙여넣기) ---

    # --- 재생목록 탭 관련 메서드 ---
    def setup_playlists_tab(self, parent_frame):
        # 재생목록 목록 프레임
        self.playlist_list_frame = ttk.LabelFrame(parent_frame, text="재생목록", padding="5")
        self.playlist_list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=False, pady=(0, 10))

        self.playlists_listbox = tk.Listbox(self.playlist_list_frame, font=self.default_font, height=8)
        self.playlists_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.playlists_listbox.bind("<<ListboxSelect>>", self.on_playlist_select)

        self.playlist_list_scrollbar = ttk.Scrollbar(self.playlist_list_frame, orient="vertical", command=self.playlists_listbox.yview)
        self.playlist_list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.playlists_listbox.config(yscrollcommand=self.playlist_list_scrollbar.set)

        # 재생목록 관리 버튼 프레임
        playlist_button_frame = ttk.Frame(parent_frame)
        playlist_button_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.add_playlist_button = ttk.Button(playlist_button_frame, text="새 재생목록 추가", command=self.add_new_playlist)
        self.add_playlist_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.rename_playlist_button = ttk.Button(playlist_button_frame, text="재생목록 이름 변경", command=self.rename_selected_playlist, state=tk.DISABLED)
        self.rename_playlist_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.delete_playlist_button = ttk.Button(playlist_button_frame, text="재생목록 삭제", command=self.delete_selected_playlist, state=tk.DISABLED)
        self.delete_playlist_button.pack(side=tk.LEFT, padx=5, pady=5)

        # 선택된 재생목록의 노래 목록 프레임
        self.songs_in_playlist_frame = ttk.LabelFrame(parent_frame, text="선택된 재생목록 노래", padding="5")
        self.songs_in_playlist_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 재생목록 Treeview 다중 선택 활성화 (selectmode='extended')
        self.songs_in_playlist_tree = ttk.Treeview(self.songs_in_playlist_frame, columns=("song_no", "title", "artist"), show="headings", height=10, selectmode='extended')
        self.songs_in_playlist_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # #0 컬럼은 이제 사용하지 않으므로 기본값 (숨김) 유지
        # self.songs_in_playlist_tree.column("#0", width=0, stretch=False)
        # self.songs_in_playlist_tree.heading("#0", text="") 

        self.songs_in_playlist_tree.heading("song_no", text="곡번호", anchor=tk.CENTER)
        self.songs_in_playlist_tree.heading("title", text="제목", anchor=tk.W)
        self.songs_in_playlist_tree.heading("artist", text="가수", anchor=tk.W)

        self.songs_in_playlist_tree.column("song_no", width=80, anchor=tk.CENTER)
        self.songs_in_playlist_tree.column("title", width=150)
        self.songs_in_playlist_tree.column("artist", width=120)
        
        self.songs_in_playlist_scrollbar = ttk.Scrollbar(self.songs_in_playlist_frame, orient="vertical", command=self.songs_in_playlist_tree.yview)
        self.songs_in_playlist_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.songs_in_playlist_tree.configure(yscrollcommand=self.songs_in_playlist_scrollbar.set)

        self.songs_in_playlist_tree.bind("<<TreeviewSelect>>", self.on_playlist_song_select) # 다중 선택 이벤트

        # 재생목록에서 노래 일괄 삭제 버튼
        self.remove_songs_from_playlist_button = ttk.Button(parent_frame, text="선택된 노래 재생목록에서 삭제", command=self.remove_selected_songs_from_current_playlist, state=tk.DISABLED)
        self.remove_songs_from_playlist_button.pack(side=tk.TOP, pady=5)

    def load_playlists(self):
        self.playlists_listbox.delete(0, tk.END) # 기존 목록 지우기
        self.all_playlists_data = self.db_manager.get_all_playlists() # {list_id, list_name} 딕셔너리 목록
        
        for p_data in self.all_playlists_data:
            self.playlists_listbox.insert(tk.END, p_data['list_name'])
        
        # 재생목록이 없으면 노래 목록 초기화
        if not self.all_playlists_data:
            self.clear_songs_in_playlist_view()
            self.rename_playlist_button.config(state=tk.DISABLED)
            self.delete_playlist_button.config(state=tk.DISABLED)

    def on_playlist_select(self, event):
        selected_indices = self.playlists_listbox.curselection()
        if not selected_indices:
            self.clear_songs_in_playlist_view()
            self.selected_playlist_id = None
            self.selected_playlist_name = None
            self.rename_playlist_button.config(state=tk.DISABLED)
            self.delete_playlist_button.config(state=tk.DISABLED)
            return

        index = selected_indices[0]
        selected_playlist_name = self.playlists_listbox.get(index)
        
        # 선택된 재생목록 데이터를 찾음
        selected_playlist_data = next((p for p in self.all_playlists_data if p['list_name'] == selected_playlist_name), None)

        if selected_playlist_data:
            self.selected_playlist_id = selected_playlist_data['list_id']
            self.selected_playlist_name = selected_playlist_name
            self.load_songs_into_playlist_tree(self.selected_playlist_id)
            self.rename_playlist_button.config(state=tk.NORMAL)
            self.delete_playlist_button.config(state=tk.NORMAL)
        else:
            self.clear_songs_in_playlist_view()
            self.selected_playlist_id = None
            self.selected_playlist_name = None
            self.rename_playlist_button.config(state=tk.DISABLED)
            self.delete_playlist_button.config(state=tk.DISABLED)

    def clear_songs_in_playlist_view(self):
        for item in self.songs_in_playlist_tree.get_children():
            self.songs_in_playlist_tree.delete(item)
        self.remove_songs_from_playlist_button.config(state=tk.DISABLED) # 버튼 비활성화


    def load_songs_into_playlist_tree(self, list_id):
        self.clear_songs_in_playlist_view()
        songs = self.db_manager.get_songs_in_playlist(list_id)
        for song in songs:
            # 다중 선택 기능만 사용하므로 image= 와 tags= 옵션 제거
            self.songs_in_playlist_tree.insert("", tk.END, values=(song["song_no"], song["title"], song["artist"]), 
                                               iid=song["song_no"])

    def on_playlist_song_select(self, event): # TreeviewSelect 이벤트 핸들러
        selected_items = self.songs_in_playlist_tree.selection() # 선택된 모든 항목의 iid를 가져옴
        
        # 선택된 노래 상세 정보는 표시하지 않음 (이 탭에서는 필요 없음)

        # 선택된 노래가 하나 이상이면 일괄 삭제 버튼 활성화
        if selected_items:
            self.remove_songs_from_playlist_button.config(state=tk.NORMAL)
        else:
            self.remove_songs_from_playlist_button.config(state=tk.DISABLED)
    
    def add_new_playlist(self):
        new_name = simpledialog.askstring("새 재생목록", "새 재생목록의 이름을 입력하세요:")
        if new_name:
            new_name = new_name.strip()
            if not new_name:
                messagebox.showwarning("입력 오류", "재생목록 이름을 비워둘 수 없습니다.")
                return
            
            list_id = self.db_manager.create_playlist(new_name)
            if list_id:
                messagebox.showinfo("재생목록 생성", f"'{new_name}' 재생목록이 생성되었습니다.")
                self.load_playlists() # 목록 새로고침
            else:
                messagebox.showerror("재생목록 생성 실패", f"'{new_name}' 재생목록 생성에 실패했습니다. (이름 중복 등)")

    def rename_selected_playlist(self):
        if not self.selected_playlist_id:
            messagebox.showwarning("선택 오류", "이름을 변경할 재생목록을 선택해주세요.")
            return
        
        new_name = simpledialog.askstring("재생목록 이름 변경", f"'{self.selected_playlist_name}' 재생목록의 새 이름을 입력하세요:",
                                          initialvalue=self.selected_playlist_name)
        if new_name:
            new_name = new_name.strip()
            if not new_name:
                messagebox.showwarning("입력 오류", "재생목록 이름을 비워둘 수 없습니다.")
                return
            if new_name == self.selected_playlist_name:
                messagebox.showinfo("변경 없음", "이름이 변경되지 않았습니다.")
                return

            if self.db_manager.rename_playlist(self.selected_playlist_id, new_name):
                messagebox.showinfo("이름 변경 완료", f"재생목록 이름이 '{new_name}'(으)로 변경되었습니다.")
                self.load_playlists() # 목록 새로고침
                self.selected_playlist_name = new_name # 현재 선택된 이름도 업데이트
                # 리스트박스에서 재선택하여 UI 동기화
                for i, playlist in enumerate(self.all_playlists_data):
                    if playlist['list_id'] == self.selected_playlist_id:
                        self.playlists_listbox.selection_set(i)
                        self.playlists_listbox.activate(i)
                        self.playlists_listbox.see(i)
                        break
            else:
                messagebox.showerror("이름 변경 실패", f"재생목록 이름 변경에 실패했습니다. (이름 중복 등)")

    def delete_selected_playlist(self):
        if not self.selected_playlist_id:
            messagebox.showwarning("선택 오류", "삭제할 재생목록을 선택해주세요.")
            return
        
        if messagebox.askyesno("재생목록 삭제", f"'{self.selected_playlist_name}' 재생목록을 삭제하시겠습니까?\n이 재생목록의 모든 노래 정보도 함께 삭제됩니다.", icon='warning'):
            if self.db_manager.delete_playlist(self.selected_playlist_id):
                messagebox.showinfo("삭제 완료", f"'{self.selected_playlist_name}' 재생목록이 삭제되었습니다.")
                self.selected_playlist_id = None
                self.selected_playlist_name = None
                self.load_playlists() # 목록 새로고침 및 UI 초기화
                self.clear_songs_in_playlist_view()
                self.rename_playlist_button.config(state=tk.DISABLED)
                self.delete_playlist_button.config(state=tk.DISABLED)
            else:
                messagebox.showerror("삭제 실패", "재생목록 삭제에 실패했습니다.")

# main.py - 파트 5/5 (일괄 추가/삭제 다이얼로그 로직 및 메인 실행 블록)

# --- (파트 4/5 코드 바로 아래에 이어서 붙여넣기) ---

    def remove_selected_songs_from_current_playlist(self): # 함수명은 기존대로 유지, 기능은 다중 선택 기반
        if not self.selected_playlist_id:
            messagebox.showwarning("선택 오류", "노래를 삭제할 재생목록이 선택되지 않았습니다.")
            return
        
        selected_song_nos = self.songs_in_playlist_tree.selection() # Treeview의 selection() 사용
        if not selected_song_nos:
            messagebox.showwarning("선택 오류", "재생목록에서 삭제할 노래를 선택해주세요.")
            return
        
        if messagebox.askyesno("노래 삭제", f"'{self.selected_playlist_name}' 재생목록에서 선택된 {len(selected_song_nos)}개의 노래를 삭제하시겠습니까?"):
            deleted_count = 0
            for song_no in selected_song_nos:
                if self.db_manager.remove_song_from_playlist(self.selected_playlist_id, song_no):
                    deleted_count += 1
            
            if deleted_count > 0:
                messagebox.showinfo("삭제 완료", f"{deleted_count}개의 노래가 재생목록에서 삭제되었습니다.")
                self.load_songs_into_playlist_tree(self.selected_playlist_id) # 노래 목록 새로고침
                self.remove_songs_from_playlist_button.config(state=tk.DISABLED) # 버튼 비활성화
            else:
                messagebox.showerror("삭제 실패", "선택된 노래들을 재생목록에서 삭제하는 데 실패했습니다.")


    # --- 검색 결과 일괄 등록 다이얼로그 ---
    def open_add_selected_to_playlist_dialog(self): # 함수명 변경
        selected_search_results_iids = self.results_tree.selection() # Treeview의 selection() 사용
        if not selected_search_results_iids:
            messagebox.showwarning("오류", "리스트에 추가할 노래를 선택해주세요.")
            return
        
        # 선택된 모든 노래 데이터를 추출
        songs_to_add = []
        for item_iid in selected_search_results_iids:
            song_no = item_iid
            # DB에서 노래 데이터를 다시 가져와서 사용 (확실한 정보 로드)
            song_data = self.db_manager.get_song(song_no=song_no)
            if song_data:
                songs_to_add.append(song_data[0])
        
        if not songs_to_add:
            messagebox.showwarning("오류", "선택된 노래 정보를 가져오지 못했습니다.")
            return

        dialog = tk.Toplevel(self.master)
        dialog.title(f"{len(songs_to_add)}개 노래를 리스트에 추가")
        dialog.transient(self.master)
        dialog.grab_set()

        ttk.Label(dialog, text="노래를 추가할 재생목록을 선택하거나 새로 만드세요:", font=self.default_font).pack(pady=10)

        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(padx=10, fill=tk.X)

        playlist_listbox_dialog = tk.Listbox(listbox_frame, font=self.default_font, height=5, exportselection=0)
        playlist_listbox_dialog.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        dialog_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=playlist_listbox_dialog.yview)
        dialog_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        playlist_listbox_dialog.config(yscrollcommand=dialog_scrollbar.set)

        playlists = self.db_manager.get_all_playlists()
        playlist_map = {}
        for i, p_data in enumerate(playlists):
            playlist_listbox_dialog.insert(tk.END, p_data['list_name'])
            playlist_map[p_data['list_name']] = p_data['list_id']
            # 현재 선택된 재생목록이 있다면 미리 선택
            if self.selected_playlist_id and p_data['list_id'] == self.selected_playlist_id:
                playlist_listbox_dialog.selection_set(i)
                playlist_listbox_dialog.activate(i)
                playlist_listbox_dialog.see(i)

        new_playlist_frame = ttk.Frame(dialog)
        new_playlist_frame.pack(padx=10, pady=5, fill=tk.X)
        ttk.Label(new_playlist_frame, text="또는 새 재생목록 이름:", font=self.default_font).pack(side=tk.LEFT)
        new_playlist_entry = ttk.Entry(new_playlist_frame, width=30, font=self.default_font)
        new_playlist_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        def add_songs_action():
            selected_indices = playlist_listbox_dialog.curselection()
            new_list_name = new_playlist_entry.get().strip()

            target_list_id = None

            if selected_indices:
                selected_name = playlist_listbox_dialog.get(selected_indices[0])
                target_list_id = playlist_map.get(selected_name)
            
            if new_list_name:
                if selected_indices:
                    messagebox.showwarning("선택 오류", "기존 재생목록을 선택했거나 새 이름을 입력하세요. 둘 다 할 수 없습니다.")
                    return
                target_list_id = self.db_manager.create_playlist(new_list_name)
                if not target_list_id:
                    messagebox.showerror("생성 실패", f"재생목록 '{new_list_name}' 생성에 실패했습니다. (이름 중복 등)")
                    return
            
            if target_list_id:
                added_count = 0
                failed_songs = []
                for song in songs_to_add:
                    if self.db_manager.add_song_to_playlist(target_list_id, song['song_no']):
                        added_count += 1
                    else:
                        failed_songs.append(song['title'])
                
                if added_count > 0:
                    messagebox.showinfo("추가 완료", f"{added_count}개 노래가 재생목록에 추가되었습니다.")
                    if failed_songs:
                        messagebox.showwarning("부분 실패", f"{', '.join(failed_songs)} 노래는 이미 재생목록에 있었거나 추가에 실패했습니다.")
                    self.load_playlists() # 재생목록 목록 갱신
                    # 만약 현재 재생목록 탭에 추가된 리스트가 선택되어 있다면, 그 노래 목록도 갱신
                    if self.selected_playlist_id == target_list_id:
                        self.load_songs_into_playlist_tree(self.selected_playlist_id)
                else:
                    messagebox.showerror("추가 실패", "선택된 노래들을 재생목록에 추가하는 데 실패했습니다. (모두 이미 존재하거나 DB 오류)")
                dialog.destroy()
            else:
                messagebox.showwarning("선택 오류", "노래를 추가할 재생목록을 선택하거나 새 재생목록 이름을 입력해주세요.")


        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="추가", command=add_songs_action).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="취소", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        self.master.wait_window(dialog) # 다이얼로그가 닫힐 때까지 메인 윈도우 대기


if __name__ == "__main__":
    root = tk.Tk()
    app = TJKaraokeApp(root)
    # db_manager.connect()에서 문제가 발생하면 app.db_manager.connection이 None이 됩니다.
    # 따라서 app.db_manager가 존재하고 (생성자에서 오류 없이 진행됐다면), 
    # 그 연결이 성공적으로 이루어졌을 때만 mainloop를 실행합니다.
    if hasattr(app, 'db_manager') and app.db_manager.is_connected():
        root.mainloop()
    else:
        print("애플리케이션이 데이터베이스 연결 문제로 시작되지 않았습니다.")
