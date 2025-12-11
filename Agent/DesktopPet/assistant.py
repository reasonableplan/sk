from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QListWidget, QListWidgetItem,
                             QMessageBox, QTimeEdit, QTextEdit)
from PyQt6.QtCore import Qt, QTimer, QTime, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
import json
import os

class AIAssistant(QWidget):
    """AI 비서 - 일정 관리, 생산성 트래킹, 스마트 알림"""
    
    task_reminder = pyqtSignal(str)  # 작업 알림
    break_reminder = pyqtSignal()    # 휴식 알림
    
    def __init__(self):
        super().__init__()
        self.tasks = []  # 할 일 목록
        self.work_sessions = []  # 작업 세션 기록
        self.current_session_start = None
        self.total_work_time = 0  # 오늘 총 작업 시간 (분)
        
        self.load_data()
        self.init_ui()
        
        # 스마트 알림 타이머
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.check_notifications)
        self.notification_timer.start(60000)  # 1분마다 체크
    
    def init_ui(self):
        self.setWindowTitle("🤖 AI 비서 대시보드")
        self.setGeometry(150, 150, 600, 700)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        
        # 헤더
        header = QLabel("📊 생산성 대시보드")
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #667eea, stop:1 #764ba2); color: white; padding: 15px; border-radius: 8px;")
        layout.addWidget(header)
        
        # 오늘의 통계
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;")
        self.update_stats_display()
        layout.addWidget(self.stats_label)
        
        # 할 일 관리
        task_header = QLabel("✅ 오늘의 할 일")
        task_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(task_header)
        
        # 할 일 입력
        task_input_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("새로운 할 일을 입력하세요...")
        self.task_input.returnPressed.connect(self.add_task)
        task_input_layout.addWidget(self.task_input)
        
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_task)
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px; border-radius: 3px;")
        task_input_layout.addWidget(add_btn)
        layout.addLayout(task_input_layout)
        
        # 할 일 목록
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("border: 1px solid #ddd; border-radius: 5px;")
        layout.addWidget(self.task_list)
        
        # 할 일 버튼들
        task_btn_layout = QHBoxLayout()
        complete_btn = QPushButton("✓ 완료")
        complete_btn.clicked.connect(self.complete_task)
        complete_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        task_btn_layout.addWidget(complete_btn)
        
        delete_btn = QPushButton("✗ 삭제")
        delete_btn.clicked.connect(self.delete_task)
        delete_btn.setStyleSheet("background-color: #f44336; color: white; padding: 5px;")
        task_btn_layout.addWidget(delete_btn)
        layout.addLayout(task_btn_layout)
        
        # 작업 세션 트래킹
        session_header = QLabel("⏱️ 작업 시간 트래킹")
        session_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(session_header)
        
        session_layout = QHBoxLayout()
        self.start_work_btn = QPushButton("🚀 작업 시작")
        self.start_work_btn.clicked.connect(self.start_work_session)
        self.start_work_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 10px; font-weight: bold;")
        session_layout.addWidget(self.start_work_btn)
        
        self.end_work_btn = QPushButton("🛑 작업 종료")
        self.end_work_btn.clicked.connect(self.end_work_session)
        self.end_work_btn.setEnabled(False)
        self.end_work_btn.setStyleSheet("background-color: #9E9E9E; color: white; padding: 10px; font-weight: bold;")
        session_layout.addWidget(self.end_work_btn)
        layout.addLayout(session_layout)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("padding: 8px; margin-top: 10px;")
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        self.refresh_task_list()
    
    def add_task(self):
        task_text = self.task_input.text().strip()
        if not task_text:
            return
        
        task = {
            "text": task_text,
            "created": datetime.now().isoformat(),
            "completed": False
        }
        self.tasks.append(task)
        self.task_input.clear()
        self.refresh_task_list()
        self.save_data()
    
    def complete_task(self):
        current_item = self.task_list.currentRow()
        if current_item >= 0 and current_item < len(self.tasks):
            self.tasks[current_item]["completed"] = True
            self.refresh_task_list()
            self.save_data()
    
    def delete_task(self):
        current_item = self.task_list.currentRow()
        if current_item >= 0:
            del self.tasks[current_item]
            self.refresh_task_list()
            self.save_data()
    
    def refresh_task_list(self):
        self.task_list.clear()
        for task in self.tasks:
            prefix = "✓ " if task["completed"] else "○ "
            item = QListWidgetItem(prefix + task["text"])
            if task["completed"]:
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
                item.setForeground(Qt.GlobalColor.gray)
            self.task_list.addItem(item)
    
    def start_work_session(self):
        self.current_session_start = datetime.now()
        self.start_work_btn.setEnabled(False)
        self.end_work_btn.setEnabled(True)
        self.end_work_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px; font-weight: bold;")
        QMessageBox.information(self, "작업 시작", "집중 모드 시작! 화이팅! 💪")
    
    def end_work_session(self):
        if self.current_session_start:
            duration = (datetime.now() - self.current_session_start).total_seconds() / 60
            self.total_work_time += duration
            self.work_sessions.append({
                "start": self.current_session_start.isoformat(),
                "duration": duration
            })
            self.current_session_start = None
            self.start_work_btn.setEnabled(True)
            self.end_work_btn.setEnabled(False)
            self.end_work_btn.setStyleSheet("background-color: #9E9E9E; color: white; padding: 10px; font-weight: bold;")
            self.update_stats_display()
            self.save_data()
            QMessageBox.information(self, "작업 종료", f"수고하셨습니다! {int(duration)}분 동안 집중했어요! 🎉")
    
    def update_stats_display(self):
        pending_tasks = sum(1 for t in self.tasks if not t["completed"])
        completed_tasks = sum(1 for t in self.tasks if t["completed"])
        work_hours = int(self.total_work_time // 60)
        work_mins = int(self.total_work_time % 60)
        
        stats_text = f"""
        <b>📈 오늘의 통계</b><br>
        ⏰ 작업 시간: {work_hours}시간 {work_mins}분<br>
        ✅ 완료한 일: {completed_tasks}개<br>
        📝 남은 일: {pending_tasks}개
        """
        self.stats_label.setText(stats_text)
    
    def check_notifications(self):
        """스마트 알림 체크"""
        now = datetime.now()
        
        # 점심시간 알림 (12:00)
        if now.hour == 12 and now.minute == 0:
            self.task_reminder.emit("점심시간이에요! 🍱 뭐 먹을까요?")
        
        # 저녁시간 알림 (18:00)
        if now.hour == 18 and now.minute == 0:
            self.task_reminder.emit("퇴근 시간이에요! 오늘도 수고하셨습니다! 🌆")
        
        # 작업 중이면 1시간마다 휴식 권장
        if self.current_session_start:
            duration = (now - self.current_session_start).total_seconds() / 60
            if duration >= 60 and int(duration) % 60 == 0:
                self.break_reminder.emit()
    
    def get_summary(self):
        """오늘의 요약 반환"""
        pending = sum(1 for t in self.tasks if not t["completed"])
        completed = sum(1 for t in self.tasks if t["completed"])
        hours = int(self.total_work_time // 60)
        mins = int(self.total_work_time % 60)
        
        return f"오늘 {hours}시간 {mins}분 작업, {completed}개 완료, {pending}개 남음"
    
    def save_data(self):
        data = {
            "tasks": self.tasks,
            "work_sessions": self.work_sessions,
            "total_work_time": self.total_work_time,
            "date": datetime.now().date().isoformat()
        }
        try:
            with open("assistant_data.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Assistant] Save failed: {e}")
    
    def load_data(self):
        if not os.path.exists("assistant_data.json"):
            return
        
        try:
            with open("assistant_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 날짜 체크 - 오늘 데이터만 로드
            saved_date = data.get("date", "")
            if saved_date == datetime.now().date().isoformat():
                self.tasks = data.get("tasks", [])
                self.work_sessions = data.get("work_sessions", [])
                self.total_work_time = data.get("total_work_time", 0)
            else:
                # 새로운 날이면 초기화
                self.tasks = []
                self.work_sessions = []
                self.total_work_time = 0
        except Exception as e:
            print(f"[Assistant] Load failed: {e}")
    
    def showEvent(self, event):
        super().showEvent(event)
        self.update_stats_display()
        self.refresh_task_list()
