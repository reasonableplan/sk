from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QTextEdit, QLineEdit, QListWidget, QTabWidget, QMessageBox,
                             QComboBox, QProgressBar, QListWidgetItem, QInputDialog, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QClipboard
from datetime import datetime
import json
import os

# AI Code Reviewer import
try:
    from ai_code_reviewer import AICodeReviewer
    AI_REVIEWER_AVAILABLE = True
except ImportError:
    AI_REVIEWER_AVAILABLE = False
    print("Warning: ai_code_reviewer module not found. AI review features will be disabled.")

# Git Assistant import
try:
    from git_assistant import GitAssistant
    GIT_ASSISTANT_AVAILABLE = True
except ImportError:
    GIT_ASSISTANT_AVAILABLE = False
    print("Warning: git_assistant module not found. Git features will be disabled.")

# Clipboard Monitor import
try:
    from clipboard_monitor import ClipboardMonitor, ClipboardAnalyzer
    CLIPBOARD_MONITOR_AVAILABLE = True
except ImportError:
    CLIPBOARD_MONITOR_AVAILABLE = False
    print("Warning: clipboard_monitor module not found. Clipboard monitoring will be disabled.")

# Test Generator import
try:
    from test_generator import TestGenerator
    TEST_GENERATOR_AVAILABLE = True
except ImportError:
    TEST_GENERATOR_AVAILABLE = False
    print("Warning: test_generator module not found. Test generation will be disabled.")

# Code Analyzer import
try:
    from code_analyzer import CodeAnalyzer
    CODE_ANALYZER_AVAILABLE = True
except ImportError:
    CODE_ANALYZER_AVAILABLE = False
    print("Warning: code_analyzer module not found. Code analysis will be disabled.")

class EnhancedCodingAssistant(QWidget):
    """고급 코딩 비서 - 개발자를 위한 올인원 도구"""
    
    reminder_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # 기존 데이터
        self.coding_start_time = None
        self.total_coding_time = 0
        self.commits_today = 0
        self.pomodoro_sessions_today = 0
        
        # 새로운 데이터
        self.code_snippets = {}  # {category: [{name, code}]}
        self.debug_logs = []  # [{time, bug, solution}]
        self.daily_goals = []  # [{goal, completed}]
        self.bookmarks = []  # [{name, url}]
        self.notes = ""  # 자유 노트
        
        # 포모도로
        self.pomodoro_running = False
        self.pomodoro_time_left = 25 * 60
        
        # AI Code Reviewer
        self.ai_reviewer = None
        if AI_REVIEWER_AVAILABLE:
            try:
                self.ai_reviewer = AICodeReviewer()
            except Exception as e:
                print(f"Failed to initialize AI Code Reviewer: {e}")
        
        # Git Assistant
        self.git_assistant = None
        if GIT_ASSISTANT_AVAILABLE:
            try:
                self.git_assistant = GitAssistant()
            except Exception as e:
                print(f"Failed to initialize Git Assistant: {e}")
        
        # Clipboard Monitor
        self.clipboard_monitor = None
        self.clipboard_analyzer = None
        self.clipboard_enabled = False
        if CLIPBOARD_MONITOR_AVAILABLE:
            try:
                self.clipboard_monitor = ClipboardMonitor()
                self.clipboard_analyzer = ClipboardAnalyzer(self.ai_reviewer)
                self.clipboard_monitor.code_detected.connect(self.on_code_detected)
                self.clipboard_monitor.start()  # 스레드 시작 (비활성 상태)
            except Exception as e:
                print(f"Failed to initialize Clipboard Monitor: {e}")
        
        # Test Generator
        self.test_generator = None
        if TEST_GENERATOR_AVAILABLE:
            try:
                self.test_generator = TestGenerator()
            except Exception as e:
                print(f"Failed to initialize Test Generator: {e}")
        
        # Code Analyzer
        self.code_analyzer = None
        if CODE_ANALYZER_AVAILABLE:
            try:
                self.code_analyzer = CodeAnalyzer()
            except Exception as e:
                print(f"Failed to initialize Code Analyzer: {e}")
        
        self.load_data()
        self.init_ui()
        
        # 타이머
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)
        
        self.pomodoro_timer = QTimer(self)
        self.pomodoro_timer.timeout.connect(self.update_pomodoro)
    
    def init_ui(self):
        self.setWindowTitle("💻 프로 코딩 비서")
        self.setGeometry(150, 150, 800, 700)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        
        # 다크 테마 스타일
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QTabWidget::pane {
                border: 1px solid #3c3c3c;
                background: #252526;
            }
            QTabBar::tab {
                background: #2d2d30;
                color: #cccccc;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #007acc;
                color: white;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0e639c, stop:1 #1177bb);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1177bb, stop:1 #1e88c7);
            }
            QPushButton:pressed {
                background: #0e639c;
            }
            QLineEdit, QTextEdit {
                background-color: #3c3c3c;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
                color: #d4d4d4;
            }
            QListWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
            }
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                text-align: center;
                background: #2d2d30;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0e639c, stop:1 #1177bb);
            }
        """)
        
        layout = QVBoxLayout()
        
        # 헤더
        header = QLabel("💻 프로 코딩 비서")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        layout.addWidget(header)
        
        # 탭 위젯
        tabs = QTabWidget()
        tabs.addTab(self.create_dashboard_tab(), "📊 대시보드")
        
        # AI Code Reviewer 탭 추가 (최우선 위치)
        if AI_REVIEWER_AVAILABLE and self.ai_reviewer:
            tabs.addTab(self.create_ai_review_tab(), "🤖 AI 리뷰")
        
        # Git Assistant 탭 추가
        if GIT_ASSISTANT_AVAILABLE and self.git_assistant:
            tabs.addTab(self.create_git_tab(), "📦 Git")
        
        tabs.addTab(self.create_snippets_tab(), "📚 스니펫")
        tabs.addTab(self.create_debug_tab(), "🐛 디버그")
        tabs.addTab(self.create_goals_tab(), "🎯 목표")
        tabs.addTab(self.create_shortcuts_tab(), "⌨️ 단축키")
        tabs.addTab(self.create_bookmarks_tab(), "🔗 북마크")
        tabs.addTab(self.create_notes_tab(), "📝 노트")
        layout.addWidget(tabs)
        
        # 닫기
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 통계
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("background-color: #2d2d30; padding: 15px; border-radius: 5px;")
        self.update_stats_display()
        layout.addWidget(self.stats_label)
        
        # 포모도로
        pomo_label = QLabel("🍅 포모도로 타이머")
        pomo_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(pomo_label)
        
        self.pomodoro_display = QLabel("25:00")
        self.pomodoro_display.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        self.pomodoro_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pomodoro_display.setStyleSheet("background-color: #2d2d30; padding: 20px; border-radius: 8px;")
        layout.addWidget(self.pomodoro_display)
        
        pomo_btns = QHBoxLayout()
        start_btn = QPushButton("▶️ 시작")
        start_btn.clicked.connect(self.start_pomodoro)
        pomo_btns.addWidget(start_btn)
        
        pause_btn = QPushButton("⏸️ 일시정지")
        pause_btn.clicked.connect(self.pause_pomodoro)
        pomo_btns.addWidget(pause_btn)
        
        reset_btn = QPushButton("🔄 리셋")
        reset_btn.clicked.connect(self.reset_pomodoro)
        pomo_btns.addWidget(reset_btn)
        layout.addLayout(pomo_btns)
        
        # 빠른 액션
        actions = QHBoxLayout()
        commit_btn = QPushButton("✅ 커밋")
        commit_btn.clicked.connect(self.mark_commit)
        actions.addWidget(commit_btn)
        
        break_btn = QPushButton("☕ 휴식")
        break_btn.clicked.connect(self.take_break)
        actions.addWidget(break_btn)
        
        # 클립보드 모니터링 토글
        if CLIPBOARD_MONITOR_AVAILABLE and self.clipboard_monitor:
            self.clipboard_toggle_btn = QPushButton("📋 클립보드 모니터 OFF")
            self.clipboard_toggle_btn.setCheckable(True)
            self.clipboard_toggle_btn.clicked.connect(self.toggle_clipboard_monitor)
            self.clipboard_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #636e72;
                }
                QPushButton:checked {
                    background-color: #00b894;
                }
            """)
            actions.addWidget(self.clipboard_toggle_btn)
        
        layout.addLayout(actions)
        
        widget.setLayout(layout)
        return widget
    
    def create_snippets_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 카테고리 선택
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("카테고리:"))
        self.snippet_category = QComboBox()
        self.snippet_category.addItems(["Python", "JavaScript", "CSS", "HTML", "Git", "기타"])
        self.snippet_category.currentTextChanged.connect(self.load_snippets_list)
        cat_layout.addWidget(self.snippet_category)
        layout.addLayout(cat_layout)
        
        # 스니펫 리스트
        self.snippets_list = QListWidget()
        self.snippets_list.itemClicked.connect(self.show_snippet)
        layout.addWidget(self.snippets_list)
        
        # 스니펫 내용
        self.snippet_content = QTextEdit()
        self.snippet_content.setPlaceholderText("스니펫 코드가 여기 표시됩니다...")
        layout.addWidget(self.snippet_content)
        
        # 버튼
        btns = QHBoxLayout()
        add_btn = QPushButton("➕ 추가")
        add_btn.clicked.connect(self.add_snippet)
        btns.addWidget(add_btn)
        
        copy_btn = QPushButton("📋 복사")
        copy_btn.clicked.connect(self.copy_snippet)
        btns.addWidget(copy_btn)
        
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.clicked.connect(self.delete_snippet)
        btns.addWidget(delete_btn)
        layout.addLayout(btns)
        
        widget.setLayout(layout)
        self.load_snippets_list()
        return widget
    
    def create_debug_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("🐛 디버깅 로그"))
        
        # 로그 리스트
        self.debug_list = QListWidget()
        for log in self.debug_logs:
            item_text = f"[{log['time']}] {log['bug'][:50]}"
            self.debug_list.addItem(item_text)
        self.debug_list.itemClicked.connect(self.show_debug_log)
        layout.addWidget(self.debug_list)
        
        # 로그 상세
        self.debug_detail = QTextEdit()
        self.debug_detail.setPlaceholderText("버그 상세 정보...")
        layout.addWidget(self.debug_detail)
        
        # 버튼
        btns = QHBoxLayout()
        add_log_btn = QPushButton("➕ 버그 기록")
        add_log_btn.clicked.connect(self.add_debug_log)
        btns.addWidget(add_log_btn)
        
        solve_btn = QPushButton("✅ 해결 완료")
        solve_btn.clicked.connect(self.solve_bug)
        btns.addWidget(solve_btn)
        layout.addLayout(btns)
        
        widget.setLayout(layout)
        return widget
    
    def create_goals_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("🎯 오늘의 목표"))
        
        # 진행률
        self.goal_progress = QProgressBar()
        self.update_goal_progress()
        layout.addWidget(self.goal_progress)
        
        # 목표 리스트
        self.goals_list = QListWidget()
        self.load_goals_list()
        layout.addWidget(self.goals_list)
        
        # 입력
        goal_input_layout = QHBoxLayout()
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("새로운 목표 입력...")
        goal_input_layout.addWidget(self.goal_input)
        
        add_goal_btn = QPushButton("➕")
        add_goal_btn.clicked.connect(self.add_goal)
        goal_input_layout.addWidget(add_goal_btn)
        layout.addLayout(goal_input_layout)
        
        # 버튼
        btns = QHBoxLayout()
        complete_btn = QPushButton("✅ 완료")
        complete_btn.clicked.connect(self.complete_goal)
        btns.addWidget(complete_btn)
        
        delete_goal_btn = QPushButton("🗑️ 삭제")
        delete_goal_btn.clicked.connect(self.delete_goal)
        btns.addWidget(delete_goal_btn)
        layout.addLayout(btns)
        
        widget.setLayout(layout)
        return widget
    
    def create_ai_review_tab(self):
        """AI 코드 리뷰 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 헤더
        header_layout = QHBoxLayout()
        header = QLabel("🤖 AI 코드 리뷰어")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # 언어 선택
        lang_label = QLabel("언어:")
        header_layout.addWidget(lang_label)
        self.review_language = QComboBox()
        self.review_language.addItems([
            "Python", "JavaScript", "Java", "C++", "C#", 
            "Go", "Rust", "TypeScript", "PHP", "Ruby"
        ])
        self.review_language.setFixedWidth(120)
        header_layout.addWidget(self.review_language)
        layout.addLayout(header_layout)
        
        # 코드 입력 영역
        input_label = QLabel("📝 리뷰할 코드:")
        input_label.setStyleSheet("margin-top: 10px; font-weight: bold;")
        layout.addWidget(input_label)
        
        self.review_code_input = QTextEdit()
        self.review_code_input.setPlaceholderText(
            "리뷰받을 코드를 여기에 붙여넣으세요...\n\n"
            "예시:\n"
            "def calculate_sum(numbers):\n"
            "    total = 0\n"
            "    for num in numbers:\n"
            "        total = total + num\n"
            "    return total"
        )
        self.review_code_input.setMinimumHeight(200)
        self.review_code_input.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(self.review_code_input)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        
        review_btn = QPushButton("🚀 AI 리뷰 받기")
        review_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        review_btn.clicked.connect(self.get_ai_review)
        btn_layout.addWidget(review_btn)
        
        quick_check_btn = QPushButton("⚡ 빠른 체크")
        quick_check_btn.clicked.connect(self.quick_code_check)
        btn_layout.addWidget(quick_check_btn)
        
        # 테스트 생성 버튼
        if TEST_GENERATOR_AVAILABLE and self.test_generator:
            test_btn = QPushButton("🧪 테스트 생성")
            test_btn.clicked.connect(self.generate_tests)
            btn_layout.addWidget(test_btn)
        
        # 코드 분석 버튼
        if CODE_ANALYZER_AVAILABLE and self.code_analyzer:
            analyze_btn = QPushButton("🔍 코드 분석")
            analyze_btn.clicked.connect(self.analyze_code_quality)
            btn_layout.addWidget(analyze_btn)
        
        clear_btn = QPushButton("🗑️ 초기화")
        clear_btn.clicked.connect(self.clear_review)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 결과 영역
        result_label = QLabel("📊 리뷰 결과:")
        result_label.setStyleSheet("margin-top: 10px; font-weight: bold;")
        layout.addWidget(result_label)
        
        self.review_result = QTextEdit()
        self.review_result.setReadOnly(True)
        self.review_result.setPlaceholderText("리뷰 결과가 여기에 표시됩니다...")
        self.review_result.setMinimumHeight(250)
        layout.addWidget(self.review_result)
        
        # 복사 버튼
        copy_layout = QHBoxLayout()
        copy_layout.addStretch()
        copy_result_btn = QPushButton("📋 결과 복사")
        copy_result_btn.clicked.connect(self.copy_review_result)
        copy_layout.addWidget(copy_result_btn)
        layout.addLayout(copy_layout)
        
        widget.setLayout(layout)
        return widget

    
    def create_shortcuts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 서브 탭 추가
        sub_tabs = QTabWidget()
        sub_tabs.addTab(self.create_ide_shortcuts(), "IDE")
        sub_tabs.addTab(self.create_python_functions(), "Python")
        sub_tabs.addTab(self.create_git_commands(), "Git")
        layout.addWidget(sub_tabs)
        
        widget.setLayout(layout)
        return widget
    
    def create_git_tab(self):
        """Git 도우미 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 헤더
        header_layout = QHBoxLayout()
        header = QLabel("📦 Git 커밋 도우미")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # 새로고침 버튼
        refresh_btn = QPushButton("🔄 새로고침")
        refresh_btn.clicked.connect(self.refresh_git_status)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)
        
        # Git 상태 표시
        status_label = QLabel("📊 저장소 상태:")
        status_label.setStyleSheet("margin-top: 10px; font-weight: bold;")
        layout.addWidget(status_label)
        
        self.git_status_display = QTextEdit()
        self.git_status_display.setReadOnly(True)
        self.git_status_display.setMaximumHeight(120)
        self.git_status_display.setStyleSheet("background-color: #2d2d30; color: #00b894; font-family: Consolas;")
        layout.addWidget(self.git_status_display)
        
        # 변경사항 (Diff)
        diff_label = QLabel("📝 변경사항 (Diff):")
        diff_label.setStyleSheet("margin-top: 10px; font-weight: bold;")
        layout.addWidget(diff_label)
        
        self.git_diff_display = QTextEdit()
        self.git_diff_display.setReadOnly(True)
        self.git_diff_display.setMinimumHeight(200)
        self.git_diff_display.setStyleSheet("font-family: Consolas; font-size: 11px;")
        layout.addWidget(self.git_diff_display)
        
        # 커밋 메시지 스타일 선택
        style_layout = QHBoxLayout()
        style_label = QLabel("메시지 스타일:")
        style_layout.addWidget(style_label)
        
        self.commit_style = QComboBox()
        self.commit_style.addItems(["Conventional Commits", "Simple", "Detailed"])
        self.commit_style.setFixedWidth(180)
        style_layout.addWidget(self.commit_style)
        style_layout.addStretch()
        layout.addLayout(style_layout)
        
        # 커밋 메시지 영역
        msg_label = QLabel("💬 커밋 메시지:")
        msg_label.setStyleSheet("margin-top: 10px; font-weight: bold;")
        layout.addWidget(msg_label)
        
        self.commit_message = QTextEdit()
        self.commit_message.setPlaceholderText("AI가 생성한 커밋 메시지가 여기 표시됩니다...")
        self.commit_message.setMinimumHeight(100)
        layout.addWidget(self.commit_message)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        
        generate_btn = QPushButton("🤖 AI 메시지 생성")
        generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #764ba2, stop:1 #667eea);
            }
        """)
        generate_btn.clicked.connect(self.generate_commit_msg)
        btn_layout.addWidget(generate_btn)
        
        commit_btn = QPushButton("✅ 커밋 실행")
        commit_btn.setStyleSheet("background-color: #00b894; color: white; font-weight: bold; padding: 10px 20px; border-radius: 5px;")
        commit_btn.clicked.connect(self.execute_commit)
        btn_layout.addWidget(commit_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 최근 커밋 히스토리
        history_label = QLabel("📜 최근 커밋:")
        history_label.setStyleSheet("margin-top: 15px; font-weight: bold;")
        layout.addWidget(history_label)
        
        self.commit_history = QListWidget()
        self.commit_history.setMaximumHeight(150)
        layout.addWidget(self.commit_history)
        
        widget.setLayout(layout)
        
        # 초기 상태 로드
        self.refresh_git_status()
        
        return widget

    
    def create_ide_shortcuts(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        shortcuts_text = """
<h3>⌨️ VS Code 단축키</h3>

<b>파일 & 편집</b>
• Ctrl+P: 파일 빠른 열기
• Ctrl+Shift+P: 명령 팔레트
• Ctrl+`: 터미널 토글
• Ctrl+B: 사이드바 토글
• Ctrl+/: 주석 토글

<b>편집</b>
• Alt+↑/↓: 줄 이동
• Ctrl+D: 다음 일치 항목 선택
• Ctrl+Shift+L: 모든 일치 항목 선택
• Alt+Click: 멀티 커서
• Ctrl+Shift+K: 줄 삭제

<b>검색 & 탐색</b>
• Ctrl+F: 찾기
• Ctrl+H: 바꾸기
• Ctrl+Shift+F: 전체 검색
• F12: 정의로 이동
• Alt+F12: 정의 미리보기
        """
        
        label = QLabel(shortcuts_text)
        label.setWordWrap(True)
        label.setStyleSheet("background-color: #2d2d30; padding: 15px; border-radius: 5px;")
        layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget
    
    def create_python_functions(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Category selector
        cat_layout = QHBoxLayout()
        cat_layout.addWidget(QLabel("📚 카테고리:"))
        self.py_category = QComboBox()
        self.py_category.addItems([
            "전체", "문자열", "리스트", "딕셔너리", "파일", 
            "내장함수", "컴프리헨션", "예외처리", "날짜/시간", "정규식"
        ])
        self.py_category.currentTextChanged.connect(self.update_python_content)
        cat_layout.addWidget(self.py_category)
        cat_layout.addStretch()
        layout.addLayout(cat_layout)
        
        # Content area
        self.python_content = QLabel()
        self.python_content.setWordWrap(True)
        self.python_content.setStyleSheet("""
            background-color: #2d2d30; 
            padding: 20px; 
            border-radius: 5px;
            line-height: 1.8;
        """)
        self.python_content.setTextFormat(Qt.TextFormat.RichText)
        
        scroll = QScrollArea()
        scroll.setWidget(self.python_content)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        layout.addWidget(scroll)
        
        # Initialize with all content
        self.update_python_content("전체")
        
        widget.setLayout(layout)
        return widget
    
    def update_python_content(self, category):
        """Update Python content based on selected category"""
        
        content_map = {
            "전체": self.get_all_python_content(),
            "문자열": self.get_string_content(),
            "리스트": self.get_list_content(),
            "딕셔너리": self.get_dict_content(),
            "파일": self.get_file_content(),
            "내장함수": self.get_builtin_content(),
            "컴프리헨션": self.get_comprehension_content(),
            "예외처리": self.get_exception_content(),
            "날짜/시간": self.get_datetime_content(),
            "정규식": self.get_regex_content()
        }
        
        self.python_content.setText(content_map.get(category, ""))
    
    def get_all_python_content(self):
        return """
<h2>🐍 Python 자주 쓰는 함수 전체</h2>
<p style='color: #888;'>왼쪽 카테고리에서 원하는 항목을 선택하세요</p>

<h3>📑 카테고리 목록</h3>
<ul style='line-height: 2.0;'>
<li><b>문자열</b> - strip, split, join, replace, format</li>
<li><b>리스트</b> - append, extend, pop, sort, reverse</li>
<li><b>딕셔너리</b> - get, keys, values, items, update</li>
<li><b>파일</b> - open, read, write, with 문</li>
<li><b>내장함수</b> - len, range, enumerate, zip, map, filter</li>
<li><b>컴프리헨션</b> - 리스트/딕셔너리/집합 컴프리헨션</li>
<li><b>예외처리</b> - try-except-finally, raise</li>
<li><b>날짜/시간</b> - datetime, timedelta, strftime</li>
<li><b>정규식</b> - re.search, findall, sub</li>
</ul>
"""
    
    def get_string_content(self):
        return """
<h2>📝 문자열 (str) 함수</h2>

<h3>🔹 공백 제거</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
text = "  hello  "
text.strip()   → "hello"      # 양쪽 공백
text.lstrip()  → "hello  "    # 왼쪽만
text.rstrip()  → "  hello"    # 오른쪽만
</pre>

<h3>🔹 분할/합치기</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# 분할
"a,b,c".split(",")        → ['a', 'b', 'c']
"a b  c".split()          → ['a', 'b', 'c']  # 공백 기준

# 합치기
",".join(['a', 'b', 'c']) → "a,b,c"
" ".join(['hello', 'world']) → "hello world"
</pre>

<h3>🔹 치환/검색</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
text = "hello world"
text.replace("world", "python")  → "hello python"
text.find("world")               → 6 (없으면 -1)
text.index("world")              → 6 (없으면 에러)
text.count("l")                  → 3
</pre>

<h3>🔹 대소문자</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
text = "hello World"
text.upper()       → "HELLO WORLD"
text.lower()       → "hello world"
text.capitalize()  → "Hello world"
text.title()       → "Hello World"
text.swapcase()    → "HELLO wORLD"
</pre>

<h3>🔹 확인</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
text.startswith("hello")  → True
text.endswith("world")    → False
text.isdigit()            → False
text.isalpha()            → False
text.isalnum()            → False
</pre>

<h3>🔹 포맷팅</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
name, age = "John", 25

# f-string (추천)
f"{name} is {age}"                    → "John is 25"
f"{name:>10}"                         → "      John"  # 오른쪽 정렬
f"{age:05d}"                          → "00025"       # 0 채우기

# format()
"{} is {}".format(name, age)          → "John is 25"
"{name} is {age}".format(name=name, age=age)
</pre>
"""
    
    def get_list_content(self):
        return """
<h2>📋 리스트 (list) 함수</h2>

<h3>🔹 추가</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
lst = [1, 2, 3]

lst.append(4)         → [1, 2, 3, 4]      # 끝에 추가
lst.extend([5, 6])    → [1, 2, 3, 4, 5, 6]  # 리스트 확장
lst.insert(0, 0)      → [0, 1, 2, 3, 4, 5, 6]  # 특정 위치
lst += [7, 8]         → [0, 1, 2, 3, 4, 5, 6, 7, 8]
</pre>

<h3>🔹 삭제</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
lst = [1, 2, 3, 2, 4]

lst.remove(2)         → [1, 3, 2, 4]  # 값으로 삭제 (첫 번째만)
lst.pop()             → 4, lst = [1, 3, 2]  # 마지막 삭제 & 반환
lst.pop(0)            → 1, lst = [3, 2]     # 인덱스로 삭제
del lst[0]            → lst = [2]
lst.clear()           → []
</pre>

<h3>🔹 정렬</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
lst = [3, 1, 4, 1, 5]

lst.sort()                    → [1, 1, 3, 4, 5]  # 원본 변경
sorted(lst)                   → [1, 1, 3, 4, 5]  # 새 리스트
lst.sort(reverse=True)        → [5, 4, 3, 1, 1]  # 내림차순
sorted(lst, key=lambda x: -x) → [5, 4, 3, 1, 1]  # 커스텀
</pre>

<h3>🔹 검색/기타</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
lst = [1, 2, 3, 2, 4]

lst.index(2)          → 1      # 인덱스 (첫 번째)
lst.count(2)          → 2      # 개수
2 in lst              → True   # 포함 여부
lst.reverse()         → [4, 2, 3, 2, 1]  # 역순
lst.copy()            → [4, 2, 3, 2, 1]  # 복사
</pre>

<h3>🔹 슬라이싱</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
lst = [0, 1, 2, 3, 4, 5]

lst[1:4]              → [1, 2, 3]
lst[:3]               → [0, 1, 2]
lst[3:]               → [3, 4, 5]
lst[::2]              → [0, 2, 4]  # 2칸씩
lst[::-1]             → [5, 4, 3, 2, 1, 0]  # 역순
</pre>
"""
    
    def get_dict_content(self):
        return """
<h2>📖 딕셔너리 (dict) 함수</h2>

<h3>🔹 접근</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
d = {'a': 1, 'b': 2}

d['a']                → 1       # 없으면 에러
d.get('a')            → 1       # 없으면 None
d.get('c', 0)         → 0       # 기본값 지정
d.setdefault('c', 3)  → 3       # 없으면 추가 & 반환
</pre>

<h3>🔹 추가/수정</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
d = {'a': 1, 'b': 2}

d['c'] = 3                    → {'a': 1, 'b': 2, 'c': 3}
d.update({'d': 4, 'e': 5})    → {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5}
d.update(f=6, g=7)            → 키워드 인자로도 가능
</pre>

<h3>🔹 삭제</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
d = {'a': 1, 'b': 2, 'c': 3}

del d['a']            → {'b': 2, 'c': 3}
d.pop('b')            → 2, d = {'c': 3}
d.popitem()           → ('c', 3), d = {}
d.clear()             → {}
</pre>

<h3>🔹 조회</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
d = {'a': 1, 'b': 2, 'c': 3}

d.keys()              → dict_keys(['a', 'b', 'c'])
d.values()            → dict_values([1, 2, 3])
d.items()             → dict_items([('a', 1), ('b', 2), ('c', 3)])

# 반복
for key in d:
    print(key, d[key])

for key, value in d.items():
    print(key, value)
</pre>

<h3>🔹 병합 (Python 3.9+)</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
d1 = {'a': 1, 'b': 2}
d2 = {'b': 3, 'c': 4}

d3 = d1 | d2          → {'a': 1, 'b': 3, 'c': 4}
d3 = {**d1, **d2}     → {'a': 1, 'b': 3, 'c': 4}  # 이전 버전
</pre>
"""
    
    def get_file_content(self):
        return """
<h2>📁 파일 입출력</h2>

<h3>🔹 읽기</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# 전체 읽기
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# 줄 단위 리스트
with open('file.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()  # ['line1\\n', 'line2\\n', ...]

# 줄 단위 반복
with open('file.txt', 'r', encoding='utf-8') as f:
    for line in f:
        print(line.strip())
</pre>

<h3>🔹 쓰기</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# 덮어쓰기
with open('file.txt', 'w', encoding='utf-8') as f:
    f.write("Hello\\n")
    f.writelines(["Line 1\\n", "Line 2\\n"])

# 추가
with open('file.txt', 'a', encoding='utf-8') as f:
    f.write("Append\\n")
</pre>

<h3>🔹 안전한 파일 처리</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
import os

# 파일 존재 확인
if os.path.exists('file.txt'):
    with open('file.txt', 'r') as f:
        content = f.read()

# 경로 조작
os.path.join('folder', 'file.txt')  → 'folder/file.txt'
os.path.dirname('/path/to/file.txt') → '/path/to'
os.path.basename('/path/to/file.txt') → 'file.txt'
</pre>

<h3>🔹 JSON 파일</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
import json

# 저장
data = {'name': 'John', 'age': 25}
with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# 읽기
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
</pre>
"""
    
    def get_builtin_content(self):
        return """
<h2>⚡ 내장 함수</h2>

<h3>🔹 길이/범위</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
len([1, 2, 3])        → 3
range(5)              → 0, 1, 2, 3, 4
range(1, 5)           → 1, 2, 3, 4
range(0, 10, 2)       → 0, 2, 4, 6, 8
</pre>

<h3>🔹 변환</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
int("10")             → 10
float("3.14")         → 3.14
str(123)              → "123"
list("abc")           → ['a', 'b', 'c']
tuple([1, 2])         → (1, 2)
set([1, 1, 2])        → {1, 2}
dict([('a', 1)])      → {'a': 1}
</pre>

<h3>🔹 수학</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
abs(-5)               → 5
max([1, 2, 3])        → 3
min([1, 2, 3])        → 1
sum([1, 2, 3])        → 6
round(3.14159, 2)     → 3.14
pow(2, 3)             → 8
divmod(10, 3)         → (3, 1)  # 몫, 나머지
</pre>

<h3>🔹 반복/변환</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# enumerate: 인덱스와 값
for i, val in enumerate(['a', 'b', 'c']):
    print(i, val)  # 0 a, 1 b, 2 c

# zip: 여러 리스트 묶기
for x, y in zip([1, 2, 3], ['a', 'b', 'c']):
    print(x, y)  # 1 a, 2 b, 3 c

# reversed: 역순
list(reversed([1, 2, 3]))  → [3, 2, 1]
</pre>

<h3>🔹 필터/맵</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# map: 함수 적용
list(map(lambda x: x*2, [1, 2, 3]))  → [2, 4, 6]

# filter: 필터링
list(filter(lambda x: x>1, [1, 2, 3]))  → [2, 3]

# any/all
any([False, True, False])  → True  # 하나라도 True
all([True, True, True])    → True  # 모두 True
</pre>

<h3>🔹 정렬</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
sorted([3, 1, 2])                    → [1, 2, 3]
sorted([3, 1, 2], reverse=True)      → [3, 2, 1]
sorted(['a', 'bb', 'ccc'], key=len)  → ['a', 'bb', 'ccc']
</pre>
"""
    
    def get_comprehension_content(self):
        return """
<h2>🔄 컴프리헨션</h2>

<h3>🔹 리스트 컴프리헨션</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# 기본
[x for x in range(5)]              → [0, 1, 2, 3, 4]
[x*2 for x in range(5)]            → [0, 2, 4, 6, 8]

# 조건
[x for x in range(10) if x % 2 == 0]  → [0, 2, 4, 6, 8]

# if-else
[x if x % 2 == 0 else -x for x in range(5)]  → [0, -1, 2, -3, 4]

# 중첩
[(x, y) for x in range(3) for y in range(3)]
→ [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)]

# 평탄화
nested = [[1, 2], [3, 4], [5]]
[item for sublist in nested for item in sublist]  → [1, 2, 3, 4, 5]
</pre>

<h3>🔹 딕셔너리 컴프리헨션</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# 기본
{x: x**2 for x in range(5)}  → {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

# 조건
{x: x**2 for x in range(10) if x % 2 == 0}
→ {0: 0, 2: 4, 4: 16, 6: 36, 8: 64}

# 키-값 뒤집기
d = {'a': 1, 'b': 2}
{v: k for k, v in d.items()}  → {1: 'a', 2: 'b'}
</pre>

<h3>🔹 집합 컴프리헨션</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
{x for x in [1, 1, 2, 2, 3]}  → {1, 2, 3}
{x % 3 for x in range(10)}    → {0, 1, 2}
</pre>

<h3>🔹 제너레이터 표현식</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# 메모리 효율적 (대용량 데이터)
gen = (x*2 for x in range(1000000))
sum(gen)  # 메모리 절약
</pre>
"""
    
    def get_exception_content(self):
        return """
<h2>⚠️ 예외 처리</h2>

<h3>🔹 기본 try-except</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
try:
    result = 10 / 0
except ZeroDivisionError:
    print("0으로 나눌 수 없습니다")
except Exception as e:
    print(f"에러: {e}")
else:
    print("성공!")  # 에러 없을 때만
finally:
    print("항상 실행")
</pre>

<h3>🔹 여러 예외 처리</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
try:
    value = int(input())
    result = 10 / value
except (ValueError, ZeroDivisionError) as e:
    print(f"에러: {e}")
</pre>

<h3>🔹 예외 발생</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# raise
if age < 0:
    raise ValueError("나이는 음수일 수 없습니다")

# assert
assert age >= 0, "나이는 음수일 수 없습니다"
</pre>

<h3>🔹 커스텀 예외</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
class MyError(Exception):
    pass

raise MyError("커스텀 에러 발생")
</pre>

<h3>🔹 주요 예외 타입</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
ValueError        # 잘못된 값
TypeError         # 잘못된 타입
KeyError          # 딕셔너리 키 없음
IndexError        # 리스트 인덱스 범위 초과
FileNotFoundError # 파일 없음
ZeroDivisionError # 0으로 나누기
AttributeError    # 속성 없음
ImportError       # 모듈 import 실패
</pre>
"""
    
    def get_datetime_content(self):
        return """
<h2>📅 날짜/시간</h2>

<h3>🔹 현재 시간</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
from datetime import datetime, timedelta

now = datetime.now()              # 2024-01-01 12:00:00
now.year, now.month, now.day      # 2024, 1, 1
now.hour, now.minute, now.second  # 12, 0, 0
now.weekday()                     # 0 (월요일)
</pre>

<h3>🔹 포맷팅</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
now = datetime.now()

# datetime → 문자열
now.strftime("%Y-%m-%d")          → "2024-01-01"
now.strftime("%Y-%m-%d %H:%M:%S") → "2024-01-01 12:00:00"
now.strftime("%Y년 %m월 %d일")     → "2024년 01월 01일"

# 문자열 → datetime
datetime.strptime("2024-01-01", "%Y-%m-%d")
</pre>

<h3>🔹 시간 계산</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
from datetime import timedelta

now = datetime.now()

# 더하기/빼기
tomorrow = now + timedelta(days=1)
week_ago = now - timedelta(weeks=1)
hour_later = now + timedelta(hours=1)

# 시간 차이
diff = datetime(2024, 12, 31) - datetime(2024, 1, 1)
diff.days                         → 364
diff.total_seconds()              → 31449600.0
</pre>

<h3>🔹 포맷 코드</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
%Y  → 2024 (년, 4자리)
%y  → 24   (년, 2자리)
%m  → 01   (월, 2자리)
%d  → 01   (일, 2자리)
%H  → 13   (시, 24시간)
%I  → 01   (시, 12시간)
%M  → 30   (분)
%S  → 45   (초)
%p  → PM   (AM/PM)
%A  → Monday (요일)
%B  → January (월 이름)
</pre>
"""
    
    def get_regex_content(self):
        return """
<h2>🔍 정규표현식 (re)</h2>

<h3>🔹 기본 사용</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
import re

text = "My email is test@example.com"

# 검색
match = re.search(r'\\w+@\\w+\\.\\w+', text)
if match:
    print(match.group())  → "test@example.com"

# 모두 찾기
re.findall(r'\\d+', "abc123def456")  → ['123', '456']

# 치환
re.sub(r'\\d+', 'X', "abc123def456")  → "abcXdefX"

# 분할
re.split(r'\\s+', "a  b   c")  → ['a', 'b', 'c']
</pre>

<h3>🔹 패턴 문자</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
.       # 모든 문자 (개행 제외)
\\d      # 숫자 [0-9]
\\D      # 숫자 아님
\\w      # 단어 문자 [a-zA-Z0-9_]
\\W      # 단어 문자 아님
\\s      # 공백 [ \\t\\n\\r\\f\\v]
\\S      # 공백 아님
^       # 문자열 시작
$       # 문자열 끝
</pre>

<h3>🔹 수량자</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
*       # 0회 이상
+       # 1회 이상
?       # 0 또는 1회
{n}     # 정확히 n회
{n,}    # n회 이상
{n,m}   # n회 이상 m회 이하
</pre>

<h3>🔹 그룹/문자 클래스</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
[abc]   # a, b, c 중 하나
[a-z]   # a부터 z까지
[^abc]  # a, b, c 제외
(abc)   # 그룹
a|b     # a 또는 b
</pre>

<h3>🔹 실전 예제</h3>
<pre style='background: #1e1e1e; padding: 10px; border-radius: 5px;'>
# 이메일
r'\\w+@\\w+\\.\\w+'

# 전화번호
r'\\d{3}-\\d{4}-\\d{4}'

# URL
r'https?://[\\w.-]+'

# IP 주소
r'\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}'

# 한글
r'[가-힣]+'
</pre>
"""
    
    def create_git_commands(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        git_text = """
<h3>🔧 Git 명령어</h3>

<b>기본</b>
• git status: 상태 확인
• git add .: 모든 변경사항 스테이징
• git commit -m "msg": 커밋
• git push: 푸시
• git pull: 풀

<b>브랜치</b>
• git branch: 브랜치 목록
• git branch name: 브랜치 생성
• git checkout name: 브랜치 전환
• git merge name: 브랜치 병합

<b>되돌리기</b>
• git reset HEAD~1: 마지막 커밋 취소
• git revert commit: 커밋 되돌리기
• git stash: 임시 저장
• git stash pop: 임시 저장 복원

<b>정규식 치트시트</b>
• \\d: 숫자 [0-9]
• \\w: 단어 문자 [a-zA-Z0-9_]
• \\s: 공백
• .: 모든 문자
• *: 0회 이상
• +: 1회 이상
• ?: 0 또는 1회
• {n}: 정확히 n회
• [abc]: a, b, c 중 하나
• ^: 시작
• $: 끝
        """
        
        label = QLabel(git_text)
        label.setWordWrap(True)
        label.setStyleSheet("background-color: #2d2d30; padding: 15px; border-radius: 5px;")
        layout.addWidget(label)
        
        widget.setLayout(layout)
        return widget
    
    def create_bookmarks_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("🔗 유용한 링크"))
        
        # 북마크 리스트
        self.bookmarks_list = QListWidget()
        self.load_bookmarks_list()
        layout.addWidget(self.bookmarks_list)
        
        # 버튼
        btns = QHBoxLayout()
        add_bookmark_btn = QPushButton("➕ 추가")
        add_bookmark_btn.clicked.connect(self.add_bookmark)
        btns.addWidget(add_bookmark_btn)
        
        open_btn = QPushButton("🌐 열기")
        open_btn.clicked.connect(self.open_bookmark)
        btns.addWidget(open_btn)
        
        delete_bookmark_btn = QPushButton("🗑️ 삭제")
        delete_bookmark_btn.clicked.connect(self.delete_bookmark)
        btns.addWidget(delete_bookmark_btn)
        layout.addLayout(btns)
        
        widget.setLayout(layout)
        return widget
    
    def create_notes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("📝 자유 노트 (코딩 중 메모, 아이디어 등)"))
        
        # 노트 에디터
        self.notes_editor = QTextEdit()
        self.notes_editor.setPlaceholderText("여기에 자유롭게 메모하세요...\n\n예시:\n- 버그 발견: 로그인 시 세션 만료 문제\n- 아이디어: 캐싱 시스템 추가\n- TODO: API 문서 업데이트")
        self.notes_editor.setText(self.notes)
        self.notes_editor.setStyleSheet("font-size: 13px; line-height: 1.5;")
        layout.addWidget(self.notes_editor)
        
        # 버튼
        btns = QHBoxLayout()
        save_btn = QPushButton("💾 저장")
        save_btn.clicked.connect(self.save_notes)
        save_btn.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #28a745, stop:1 #218838);")
        btns.addWidget(save_btn)
        
        clear_btn = QPushButton("🗑️ 전체 삭제")
        clear_btn.clicked.connect(self.clear_notes)
        clear_btn.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc3545, stop:1 #c82333);")
        btns.addWidget(clear_btn)
        
        export_btn = QPushButton("📤 텍스트 파일로 내보내기")
        export_btn.clicked.connect(self.export_notes)
        btns.addWidget(export_btn)
        layout.addLayout(btns)
        
        widget.setLayout(layout)
        return widget
    
    # 노트 메서드
    def save_notes(self):
        self.notes = self.notes_editor.toPlainText()
        self.save_data()
        QMessageBox.information(self, "저장 완료", "노트가 저장되었습니다!")
    
    def clear_notes(self):
        reply = QMessageBox.question(self, "확인", "정말 모든 노트를 삭제하시겠습니까?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.notes_editor.clear()
            self.notes = ""
            self.save_data()
    
    def export_notes(self):
        if not self.notes:
            QMessageBox.warning(self, "경고", "저장할 노트가 없습니다!")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"coding_notes_{timestamp}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.notes_editor.toPlainText())
            QMessageBox.information(self, "내보내기 완료", f"노트가 '{filename}'로 저장되었습니다!")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일 저장 실패: {e}")
    
    # 포모도로 메서드
    def start_pomodoro(self):
        self.pomodoro_running = True
        self.pomodoro_timer.start(1000)
    
    def pause_pomodoro(self):
        self.pomodoro_running = False
        self.pomodoro_timer.stop()
    
    def reset_pomodoro(self):
        self.pause_pomodoro()
        self.pomodoro_time_left = 25 * 60
        self.pomodoro_display.setText("25:00")
    
    def update_pomodoro(self):
        if self.pomodoro_running:
            self.pomodoro_time_left -= 1
            mins = self.pomodoro_time_left // 60
            secs = self.pomodoro_time_left % 60
            self.pomodoro_display.setText(f"{mins:02d}:{secs:02d}")
            
            if self.pomodoro_time_left <= 0:
                self.pause_pomodoro()
                self.pomodoro_sessions_today += 1
                self.pomodoro_time_left = 25 * 60
                self.pomodoro_display.setText("25:00")
                QMessageBox.information(self, "완료!", "25분 집중 완료! 5분 휴식! ☕")
                self.reminder_signal.emit("포모도로 완료! 5분 휴식하세요 ☕")
    
    def mark_commit(self):
        self.commits_today += 1
        self.update_stats_display()
        self.save_data()
        QMessageBox.information(self, "커밋!", f"오늘 {self.commits_today}번째 커밋! 🎯")
    
    def take_break(self):
        QMessageBox.information(self, "휴식", "10분 휴식! 🧘")
        self.reminder_signal.emit("10분 휴식 시작! 🧘")
    
    # 스니펫 메서드
    def load_snippets_list(self):
        self.snippets_list.clear()
        category = self.snippet_category.currentText()
        if category in self.code_snippets:
            for snippet in self.code_snippets[category]:
                self.snippets_list.addItem(snippet['name'])
    
    def show_snippet(self, item):
        category = self.snippet_category.currentText()
        name = item.text()
        if category in self.code_snippets:
            for snippet in self.code_snippets[category]:
                if snippet['name'] == name:
                    self.snippet_content.setText(snippet['code'])
                    break
    
    def add_snippet(self):
        name, ok = QInputDialog.getText(self, "스니펫 추가", "스니펫 이름:")
        if ok and name:
            code = self.snippet_content.toPlainText()
            category = self.snippet_category.currentText()
            
            if category not in self.code_snippets:
                self.code_snippets[category] = []
            
            self.code_snippets[category].append({"name": name, "code": code})
            self.load_snippets_list()
            self.save_data()
            QMessageBox.information(self, "완료", "스니펫이 저장되었습니다!")
    
    def copy_snippet(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.snippet_content.toPlainText())
        QMessageBox.information(self, "복사", "클립보드에 복사되었습니다!")
    
    def delete_snippet(self):
        current_item = self.snippets_list.currentItem()
        if current_item:
            category = self.snippet_category.currentText()
            name = current_item.text()
            if category in self.code_snippets:
                self.code_snippets[category] = [s for s in self.code_snippets[category] if s['name'] != name]
                self.load_snippets_list()
                self.snippet_content.clear()
                self.save_data()
    
    # 디버그 로그 메서드
    def add_debug_log(self):
        bug, ok = QInputDialog.getText(self, "버그 기록", "버그 설명:")
        if ok and bug:
            log = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "bug": bug,
                "solution": "",
                "solved": False
            }
            self.debug_logs.append(log)
            self.debug_list.addItem(f"[{log['time']}] {bug[:50]}")
            self.save_data()
    
    def show_debug_log(self, item):
        index = self.debug_list.row(item)
        if index < len(self.debug_logs):
            log = self.debug_logs[index]
            text = f"버그: {log['bug']}\n\n해결: {log['solution']}\n\n상태: {'✅ 해결됨' if log['solved'] else '❌ 미해결'}"
            self.debug_detail.setText(text)
    
    def solve_bug(self):
        current_row = self.debug_list.currentRow()
        if current_row >= 0:
            solution, ok = QInputDialog.getText(self, "해결 방법", "해결 방법:")
            if ok:
                self.debug_logs[current_row]['solution'] = solution
                self.debug_logs[current_row]['solved'] = True
                self.save_data()
                QMessageBox.information(self, "완료", "버그가 해결되었습니다! 🎉")
    
    # 목표 메서드
    def load_goals_list(self):
        self.goals_list.clear()
        for goal in self.daily_goals:
            prefix = "✅ " if goal['completed'] else "⬜ "
            item = QListWidgetItem(prefix + goal['goal'])
            self.goals_list.addItem(item)
    
    def add_goal(self):
        goal_text = self.goal_input.text().strip()
        if goal_text:
            self.daily_goals.append({"goal": goal_text, "completed": False})
            self.goal_input.clear()
            self.load_goals_list()
            self.update_goal_progress()
            self.save_data()
    
    def complete_goal(self):
        current_row = self.goals_list.currentRow()
        if current_row >= 0:
            self.daily_goals[current_row]['completed'] = True
            self.load_goals_list()
            self.update_goal_progress()
            self.save_data()
            QMessageBox.information(self, "완료!", "목표 달성! 🎉")
    
    def delete_goal(self):
        current_row = self.goals_list.currentRow()
        if current_row >= 0:
            del self.daily_goals[current_row]
            self.load_goals_list()
            self.update_goal_progress()
            self.save_data()
    
    def update_goal_progress(self):
        if not self.daily_goals:
            self.goal_progress.setValue(0)
            return
        completed = sum(1 for g in self.daily_goals if g['completed'])
        progress = int((completed / len(self.daily_goals)) * 100)
        self.goal_progress.setValue(progress)
        self.goal_progress.setFormat(f"{completed}/{len(self.daily_goals)} 완료 ({progress}%)")
    
    # 북마크 메서드
    def load_bookmarks_list(self):
        self.bookmarks_list.clear()
        for bookmark in self.bookmarks:
            self.bookmarks_list.addItem(f"{bookmark['name']} - {bookmark['url']}")
    
    def add_bookmark(self):
        name, ok1 = QInputDialog.getText(self, "북마크 추가", "이름:")
        if ok1 and name:
            url, ok2 = QInputDialog.getText(self, "북마크 추가", "URL:")
            if ok2 and url:
                self.bookmarks.append({"name": name, "url": url})
                self.load_bookmarks_list()
                self.save_data()
    
    def open_bookmark(self):
        current_row = self.bookmarks_list.currentRow()
        if current_row >= 0:
            import webbrowser
            webbrowser.open(self.bookmarks[current_row]['url'])
    
    def delete_bookmark(self):
        current_row = self.bookmarks_list.currentRow()
        if current_row >= 0:
            del self.bookmarks[current_row]
            self.load_bookmarks_list()
            self.save_data()
    
    def update_stats_display(self):
        hours = int(self.total_coding_time // 60)
        mins = int(self.total_coding_time % 60)
        
        stats_text = f"""
<h3>📊 오늘의 통계</h3>
⏰ 코딩 시간: {hours}시간 {mins}분<br>
🍅 포모도로: {self.pomodoro_sessions_today}회<br>
✅ 커밋: {self.commits_today}회<br>
🎯 목표: {sum(1 for g in self.daily_goals if g['completed'])}/{len(self.daily_goals)}
        """
        self.stats_label.setText(stats_text)
    
    def check_reminders(self):
        pass  # 기존 알림 로직
    
    def save_data(self):
        data = {
            "total_coding_time": self.total_coding_time,
            "commits_today": self.commits_today,
            "pomodoro_sessions": self.pomodoro_sessions_today,
            "code_snippets": self.code_snippets,
            "debug_logs": self.debug_logs,
            "daily_goals": self.daily_goals,
            "bookmarks": self.bookmarks,
            "notes": self.notes,
            "date": datetime.now().date().isoformat()
        }
        try:
            with open("enhanced_coding_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[EnhancedCoding] Save failed: {e}")
    
    def load_data(self):
        if not os.path.exists("enhanced_coding_data.json"):
            return
        
        try:
            with open("enhanced_coding_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            saved_date = data.get("date", "")
            if saved_date == datetime.now().date().isoformat():
                self.total_coding_time = data.get("total_coding_time", 0)
                self.commits_today = data.get("commits_today", 0)
                self.pomodoro_sessions_today = data.get("pomodoro_sessions", 0)
                self.daily_goals = data.get("daily_goals", [])
            
            # 영구 데이터
            self.code_snippets = data.get("code_snippets", {})
            self.debug_logs = data.get("debug_logs", [])
            self.bookmarks = data.get("bookmarks", [])
            self.notes = data.get("notes", "")
        except Exception as e:
            print(f"[EnhancedCoding] Load failed: {e}")
    
    # ===== AI Code Review Methods =====
    
    def get_ai_review(self):
        """AI 코드 리뷰 수행"""
        if not self.ai_reviewer:
            QMessageBox.warning(
                self,
                "AI 리뷰 불가",
                "AI 코드 리뷰어를 사용할 수 없습니다.\n\n"
                "다음을 확인해주세요:\n"
                "1. ai_code_reviewer.py 파일이 있는지\n"
                "2. .env 파일에 GEMINI_API_KEY가 설정되어 있는지\n"
                "3. google-generativeai 패키지가 설치되어 있는지"
            )
            return
        
        code = self.review_code_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "입력 필요", "리뷰할 코드를 입력해주세요.")
            return
        
        language = self.review_language.currentText().lower()
        
        # 로딩 표시
        self.review_result.setText("🔄 AI가 코드를 분석 중입니다...\n잠시만 기다려주세요.")
        QApplication.processEvents()  # UI 업데이트
        
        try:
            # AI 리뷰 수행
            result = self.ai_reviewer.review_code(code, language)
            
            # 결과 포맷팅
            review_text = self._format_review_result(result)
            self.review_result.setText(review_text)
            
            # 성공 메시지
            QMessageBox.information(
                self,
                "리뷰 완료",
                f"코드 품질 점수: {result['score']}/10\n\n"
                "리뷰가 완료되었습니다!"
            )
            
        except Exception as e:
            error_msg = f"❌ AI 리뷰 중 오류가 발생했습니다:\n\n{str(e)}\n\n"
            error_msg += "다음을 확인해주세요:\n"
            error_msg += "1. 인터넷 연결 상태\n"
            error_msg += "2. Gemini API 키가 유효한지\n"
            error_msg += "3. API 사용 한도를 초과하지 않았는지"
            
            self.review_result.setText(error_msg)
            QMessageBox.critical(self, "오류", str(e))
    
    def _format_review_result(self, result):
        """리뷰 결과를 보기 좋게 포맷팅"""
        text = f"{'='*60}\n"
        text += f"  🤖 AI 코드 리뷰 결과\n"
        text += f"{'='*60}\n\n"
        
        # 점수
        score = result.get('score', 0)
        text += f"📊 코드 품질 점수: {score}/10\n"
        
        # 점수에 따른 이모지
        if score >= 8:
            text += "   평가: 우수합니다! ⭐⭐⭐\n"
        elif score >= 6:
            text += "   평가: 양호합니다 ⭐⭐\n"
        elif score >= 4:
            text += "   평가: 개선이 필요합니다 ⭐\n"
        else:
            text += "   평가: 많은 개선이 필요합니다 ⚠️\n"
        
        text += "\n" + "-"*60 + "\n\n"
        
        # 문제점
        issues = result.get('issues', [])
        if issues:
            text += "🐛 발견된 문제점:\n\n"
            for i, issue in enumerate(issues, 1):
                if issue.strip():
                    text += f"  {i}. {issue}\n"
            text += "\n" + "-"*60 + "\n\n"
        
        # 개선 제안
        suggestions = result.get('suggestions', [])
        if suggestions:
            text += "💡 개선 제안:\n\n"
            for i, suggestion in enumerate(suggestions, 1):
                if suggestion.strip():
                    text += f"  {i}. {suggestion}\n"
            text += "\n" + "-"*60 + "\n\n"
        
        # 리팩토링된 코드
        refactored = result.get('refactored_code', '')
        if refactored:
            text += "✨ 리팩토링된 코드:\n\n"
            text += refactored + "\n\n"
            text += "-"*60 + "\n\n"
        
        # 요약
        summary = result.get('summary', '')
        if summary:
            text += "📝 요약:\n\n"
            text += summary + "\n\n"
        
        text += "="*60 + "\n"
        
        return text
    
    def quick_code_check(self):
        """빠른 코드 체크"""
        if not self.ai_reviewer:
            QMessageBox.warning(self, "AI 리뷰 불가", "AI 코드 리뷰어를 사용할 수 없습니다.")
            return
        
        code = self.review_code_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "입력 필요", "체크할 코드를 입력해주세요.")
            return
        
        language = self.review_language.currentText().lower()
        
        self.review_result.setText("⚡ 빠른 체크 중...")
        QApplication.processEvents()
        
        try:
            feedback = self.ai_reviewer.quick_check(code, language)
            self.review_result.setText(f"⚡ 빠른 체크 결과:\n\n{feedback}")
        except Exception as e:
            self.review_result.setText(f"❌ 체크 실패: {str(e)}")
    
    def clear_review(self):
        """리뷰 입력/출력 초기화"""
        self.review_code_input.clear()
        self.review_result.clear()
    
    def copy_review_result(self):
        """리뷰 결과 클립보드에 복사"""
        result_text = self.review_result.toPlainText()
        if result_text:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(result_text)
            QMessageBox.information(self, "복사 완료", "리뷰 결과가 클립보드에 복사되었습니다!")
        else:
            QMessageBox.warning(self, "복사 불가", "복사할 내용이 없습니다.")
    
    # ===== Git Assistant Methods =====
    
    def refresh_git_status(self):
        """Git 상태 새로고침"""
        if not self.git_assistant:
            self.git_status_display.setText("Git Assistant를 사용할 수 없습니다.")
            return
        
        if not self.git_assistant.is_git_repo:
            self.git_status_display.setText("❌ 현재 디렉토리는 Git 저장소가 아닙니다.")
            self.git_diff_display.clear()
            self.commit_history.clear()
            return
        
        # 상태 가져오기
        status = self.git_assistant.get_status()
        
        # 상태 표시
        status_text = f"📌 브랜치: {status['branch']}\n\n"
        
        if status['clean']:
            status_text += "✅ 변경사항 없음 (Clean)\n"
        else:
            if status['staged']:
                status_text += f"📝 스테이징됨: {len(status['staged'])}개 파일\n"
                for f in status['staged'][:5]:  # 최대 5개만 표시
                    status_text += f"   • {f}\n"
            
            if status['modified']:
                status_text += f"📝 수정됨: {len(status['modified'])}개 파일\n"
                for f in status['modified'][:5]:
                    status_text += f"   • {f}\n"
            
            if status['untracked']:
                status_text += f"❓ 추적 안 됨: {len(status['untracked'])}개 파일\n"
        
        self.git_status_display.setText(status_text)
        
        # Diff 가져오기
        diff = self.git_assistant.get_diff(staged_only=True)
        if diff and diff.strip():
            self.git_diff_display.setText(diff)
        else:
            # 스테이징된 게 없으면 전체 diff
            diff = self.git_assistant.get_diff(staged_only=False)
            if diff and diff.strip():
                self.git_diff_display.setText("(스테이징되지 않은 변경사항)\n\n" + diff)
            else:
                self.git_diff_display.setText("변경사항이 없습니다.")
        
        # 커밋 히스토리 가져오기
        self.commit_history.clear()
        commits = self.git_assistant.get_recent_commits(10)
        for commit in commits:
            item_text = f"{commit['hash']} - {commit['message']} ({commit['date']})"
            self.commit_history.addItem(item_text)
    
    def generate_commit_msg(self):
        """AI 커밋 메시지 생성"""
        if not self.git_assistant:
            QMessageBox.warning(self, "Git 불가", "Git Assistant를 사용할 수 없습니다.")
            return
        
        if not self.git_assistant.ai_available:
            QMessageBox.warning(
                self,
                "AI 불가",
                "AI 기능을 사용할 수 없습니다.\n\n"
                "Gemini API 키를 확인해주세요."
            )
            return
        
        # 스타일 선택
        style_map = {
            "Conventional Commits": "conventional",
            "Simple": "simple",
            "Detailed": "detailed"
        }
        style = style_map[self.commit_style.currentText()]
        
        # 로딩 표시
        self.commit_message.setText("🔄 AI가 커밋 메시지를 생성 중입니다...")
        QApplication.processEvents()
        
        try:
            # 커밋 메시지 생성
            message = self.git_assistant.generate_commit_message(style=style)
            self.commit_message.setText(message)
            
            if "실패" in message or "오류" in message:
                QMessageBox.warning(self, "생성 실패", message)
            else:
                QMessageBox.information(self, "생성 완료", "커밋 메시지가 생성되었습니다!")
        
        except Exception as e:
            error_msg = f"커밋 메시지 생성 중 오류:\n{str(e)}"
            self.commit_message.setText(error_msg)
            QMessageBox.critical(self, "오류", error_msg)
    
    def execute_commit(self):
        """커밋 실행"""
        if not self.git_assistant:
            QMessageBox.warning(self, "Git 불가", "Git Assistant를 사용할 수 없습니다.")
            return
        
        message = self.commit_message.toPlainText().strip()
        if not message:
            QMessageBox.warning(self, "메시지 필요", "커밋 메시지를 입력해주세요.")
            return
        
        # 확인 대화상자
        reply = QMessageBox.question(
            self,
            "커밋 확인",
            f"다음 메시지로 커밋하시겠습니까?\n\n{message[:100]}...",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        try:
            # 커밋 실행
            success, result = self.git_assistant.commit(message)
            
            if success:
                QMessageBox.information(self, "커밋 성공", result)
                self.commit_message.clear()
                self.refresh_git_status()
            else:
                QMessageBox.critical(self, "커밋 실패", result)
        
        except Exception as e:
            QMessageBox.critical(self, "오류", f"커밋 실행 중 오류:\n{str(e)}")
    
    # ===== Clipboard Monitor Methods =====
    
    def toggle_clipboard_monitor(self):
        """클립보드 모니터링 토글"""
        if not self.clipboard_monitor:
            return
        
        self.clipboard_enabled = not self.clipboard_enabled
        
        if self.clipboard_enabled:
            self.clipboard_monitor.enable()
            self.clipboard_toggle_btn.setText("📋 클립보드 모니터 ON")
            QMessageBox.information(
                self,
                "모니터링 시작",
                "클립보드 모니터링이 활성화되었습니다!\n\n"
                "코드를 복사하면 자동으로 감지하고 분석합니다."
            )
        else:
            self.clipboard_monitor.disable()
            self.clipboard_toggle_btn.setText("📋 클립보드 모니터 OFF")
    
    def on_code_detected(self, code: str, language: str):
        """코드 감지 시 호출되는 핸들러"""
        if not self.clipboard_analyzer:
            return
        
        # 빠른 분석 수행
        result = self.clipboard_analyzer.quick_analyze(code, language)
        
        # 알림 표시
        formatted_result = self.clipboard_analyzer.format_analysis_result(result)
        
        # 메시지 박스로 알림
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("📋 코드 감지!")
        msg_box.setText(f"클립보드에서 {language} 코드를 감지했습니다!")
        msg_box.setDetailedText(formatted_result)
        msg_box.setIcon(QMessageBox.Icon.Information)
        
        # 버튼 추가
        review_btn = msg_box.addButton("AI 리뷰 받기", QMessageBox.ButtonRole.ActionRole)
        close_btn = msg_box.addButton("닫기", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        
        # AI 리뷰 버튼 클릭 시
        if msg_box.clickedButton() == review_btn:
            if self.ai_reviewer:
                # AI 리뷰 탭으로 이동하고 코드 자동 입력
                if hasattr(self, 'review_code_input'):
                    self.review_code_input.setText(code)
                    # 언어 설정
                    if hasattr(self, 'review_language'):
                        index = self.review_language.findText(language, Qt.MatchFlag.MatchFixedString)
                        if index >= 0:
                            self.review_language.setCurrentIndex(index)
                    
                    QMessageBox.information(
                        self,
                        "준비 완료",
                        "AI 리뷰 탭에 코드가 입력되었습니다.\n"
                        "'AI 리뷰 받기' 버튼을 클릭하세요!"
                    )
    
    def closeEvent(self, event):
        """창 닫기 시 클립보드 모니터 정리"""
        if self.clipboard_monitor:
            self.clipboard_monitor.stop()
        event.accept()
    
    # ===== Test Generator Methods =====
    
    def generate_tests(self):
        """pytest 테스트 생성"""
        if not self.test_generator:
            QMessageBox.warning(self, "테스트 생성 불가", "Test Generator를 사용할 수 없습니다.")
            return
        
        code = self.review_code_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "입력 필요", "테스트를 생성할 코드를 입력해주세요.")
            return
        
        # 로딩 표시
        self.review_result.setText("🧪 pytest 테스트를 생성 중입니다...\n잠시만 기다려주세요.")
        QApplication.processEvents()
        
        try:
            # 테스트 생성
            test_code = self.test_generator.generate_test(code)
            
            # 결과 표시
            result_text = "🧪 생성된 pytest 테스트\n"
            result_text += "=" * 60 + "\n\n"
            result_text += test_code
            
            self.review_result.setText(result_text)
            QMessageBox.information(self, "생성 완료", "pytest 테스트가 생성되었습니다!")
        
        except Exception as e:
            error_msg = f"테스트 생성 중 오류:\n{str(e)}"
            self.review_result.setText(error_msg)
            QMessageBox.critical(self, "오류", error_msg)
    
    # ===== Code Analyzer Methods =====
    
    def analyze_code_quality(self):
        """코드 품질 분석"""
        if not self.code_analyzer:
            QMessageBox.warning(self, "분석 불가", "Code Analyzer를 사용할 수 없습니다.")
            return
        
        code = self.review_code_input.toPlainText().strip()
        if not code:
            QMessageBox.warning(self, "입력 필요", "분석할 코드를 입력해주세요.")
            return
        
        language = self.review_language.currentText().lower()
        
        # 로딩 표시
        self.review_result.setText("🔍 코드를 분석 중입니다...")
        QApplication.processEvents()
        
        try:
            # 코드 분석
            result = self.code_analyzer.analyze_code(code, language)
            
            # 결과 포맷팅
            formatted_result = self.code_analyzer.format_analysis_result(result)
            self.review_result.setText(formatted_result)
            
            # 요약 메시지
            summary = f"복잡도: {result['complexity']['level']}\n"
            if result['style_issues']:
                summary += f"스타일 이슈: {len(result['style_issues'])}개\n"
            if result['security_issues']:
                summary += f"⚠️ 보안 이슈: {len(result['security_issues'])}개"
            
            QMessageBox.information(self, "분석 완료", summary)
        
        except Exception as e:
            error_msg = f"코드 분석 중 오류:\n{str(e)}"
            self.review_result.setText(error_msg)
            QMessageBox.critical(self, "오류", error_msg)
