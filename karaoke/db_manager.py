import sqlite3

class DBManager:
    def __init__(self, db_name="karaoke_songs.db"):
        self.db_name = db_name
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
            self._create_tables()
            print(f"데이터베이스 '{self.db_name}'에 성공적으로 연결되었습니다.")
            return True
        except sqlite3.Error as e:
            print(f"데이터베이스 연결 오류: {e}")
            self.connection = None # 연결 실패 시 connection을 None으로 설정
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None # 연결 해제 시 connection을 None으로 설정
            print("데이터베이스 연결이 해제되었습니다.")

    def is_connected(self):
        """
        데이터베이스 연결이 활성화되어 있는지 확인합니다.
        sqlite3.Connection 객체는 'is_connected' 메서드를 직접 제공하지 않으므로,
        connection 객체가 None이 아닌지 확인하여 연결 상태를 유추합니다.
        """
        return self.connection is not None

    def _create_tables(self):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않아 테이블을 생성할 수 없습니다.")
            return
        
        # 노래 정보 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                song_no TEXT PRIMARY KEY,
                title TEXT,
                artist TEXT,
                composer TEXT,
                lyricist TEXT,
                lyrics TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 재생목록 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                list_id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_name TEXT NOT NULL UNIQUE,
                creation_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 재생목록에 담긴 노래 연결 테이블
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_songs (
                list_song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                list_id INTEGER NOT NULL,
                song_no TEXT NOT NULL,
                added_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (list_id) REFERENCES playlists(list_id) ON DELETE CASCADE,
                FOREIGN KEY (song_no) REFERENCES songs(song_no) ON DELETE CASCADE,
                UNIQUE (list_id, song_no) -- 한 재생목록에 같은 노래 중복 추가 방지
            )
        ''')
        self.connection.commit()

    def insert_or_update_song(self, song_data):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. insert_or_update_song 실패.")
            return None
        try:
            self.cursor.execute('''
                INSERT INTO songs (song_no, title, artist, composer, lyricist, lyrics)
                VALUES (:song_no, :title, :artist, :composer, :lyricist, :lyrics)
                ON CONFLICT(song_no) DO UPDATE SET
                    title=excluded.title,
                    artist=excluded.artist,
                    composer=excluded.composer,
                    lyricist=excluded.lyricist,
                    lyrics=excluded.lyrics,
                    last_updated=CURRENT_TIMESTAMP
            ''', song_data)
            self.connection.commit()
            print(f"노래 '{song_data['title']}' ({song_data['song_no']}) DB에 저장/업데이트 완료.")
            return self.cursor.rowcount
        except sqlite3.Error as e:
            print(f"노래 저장/업데이트 오류: {e}")
            return None

    def get_song(self, song_no=None, query_text=None):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. get_song 실패.")
            return []
        
        query = "SELECT song_no, title, artist, composer, lyricist, lyrics FROM songs"
        params = []
        if song_no:
            query += " WHERE song_no = ?"
            params.append(song_no)
        elif query_text:
            query += " WHERE title LIKE ? OR artist LIKE ? OR song_no LIKE ?"
            params.extend([f'%{query_text}%', f'%{query_text}%', f'%{query_text}%'])
        
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        
        # 컬럼 이름과 함께 딕셔너리 형태로 반환
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    # --- 재생목록 관련 메서드 ---

    def create_playlist(self, list_name):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. create_playlist 실패.")
            return None
        try:
            self.cursor.execute("INSERT INTO playlists (list_name) VALUES (?)", (list_name,))
            self.connection.commit()
            return self.cursor.lastrowid # 새로 생성된 list_id 반환
        except sqlite3.IntegrityError:
            print(f"재생목록 '{list_name}'은(는) 이미 존재합니다.")
            return None
        except sqlite3.Error as e:
            print(f"재생목록 생성 오류: {e}")
            return None

    def rename_playlist(self, list_id, new_name):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. rename_playlist 실패.")
            return False
        try:
            self.cursor.execute("UPDATE playlists SET list_name = ? WHERE list_id = ?", (new_name, list_id))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.IntegrityError:
            print(f"재생목록 이름 '{new_name}'은(는) 이미 존재합니다. 다른 이름을 사용해주세요.")
            return False
        except sqlite3.Error as e:
            print(f"재생목록 이름 변경 오류: {e}")
            return False

    def delete_playlist(self, list_id):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. delete_playlist 실패.")
            return False
        try:
            self.cursor.execute("DELETE FROM playlists WHERE list_id = ?", (list_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"재생목록 삭제 오류: {e}")
            return False

    def get_all_playlists(self):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. get_all_playlists 실패.")
            return []
        self.cursor.execute("SELECT list_id, list_name FROM playlists ORDER BY list_name")
        rows = self.cursor.fetchall()
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def add_song_to_playlist(self, list_id, song_no):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. add_song_to_playlist 실패.")
            return False
        try:
            self.cursor.execute("INSERT INTO playlist_songs (list_id, song_no) VALUES (?, ?)", (list_id, song_no))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.IntegrityError:
            print(f"이 노래는 이미 선택된 재생목록에 있습니다. (list_id: {list_id}, song_no: {song_no})")
            return False
        except sqlite3.Error as e:
            print(f"재생목록에 노래 추가 오류: {e}")
            return False

    def remove_song_from_playlist(self, list_id, song_no):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. remove_song_from_playlist 실패.")
            return False
        try:
            self.cursor.execute("DELETE FROM playlist_songs WHERE list_id = ? AND song_no = ?", (list_id, song_no))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"재생목록에서 노래 삭제 오류: {e}")
            return False

    def get_songs_in_playlist(self, list_id):
        if not self.is_connected():
            print("DBManager: 데이터베이스가 연결되어 있지 않습니다. get_songs_in_playlist 실패.")
            return []
        query = '''
            SELECT s.song_no, s.title, s.artist, s.composer, s.lyricist, s.lyrics
            FROM playlist_songs ps
            JOIN songs s ON ps.song_no = s.song_no
            WHERE ps.list_id = ?
            ORDER BY s.title
        '''
        self.cursor.execute(query, (list_id,))
        rows = self.cursor.fetchall()
        columns = [description[0] for description in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]
