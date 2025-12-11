from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, 
                             QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal

class PetChat(QWidget):
    # 특수 명령 시그널 (예: 밥 줘 -> 메뉴 열기)
    command_triggered = pyqtSignal(str)

    def __init__(self, pet_state):
        super().__init__()
        self.pet_state = pet_state
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("펫과 대화하기")
        self.setGeometry(500, 500, 300, 400)
        
        layout = QVBoxLayout()
        
        # 채팅 내역 표시
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("background-color: #f0f8ff; font-size: 14px;")
        layout.addWidget(self.chat_history)
        
        # 입력창 및 전송 버튼
        input_layout = QHBoxLayout()
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("말을 걸어보세요... (예: 안녕, 배고파?)")
        self.msg_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.msg_input)
        
        send_btn = QPushButton("전송")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        self.setLayout(layout)
        
        # 펫의 첫 인사
        self.pet_reply("안녕! 무슨 일이야? 😊")

    def send_message(self):
        msg = self.msg_input.text().strip()
        if not msg:
            return
        
        # 내 메시지 표시
        self.append_chat("나", msg)
        self.msg_input.clear()
        
        # 펫 응답 생성
        response = self.generate_response(msg)
        self.pet_reply(response)

    def append_chat(self, sender, text):
        color = "blue" if sender == "나" else "green"
        self.chat_history.append(f"<b style='color:{color}'>{sender}:</b> {text}")

    def pet_reply(self, text):
        self.append_chat(self.pet_state.name, text)

    def generate_response(self, text):
        # 간단한 키워드 매칭 로직
        text = text.lower() # 소문자 변환 (영어인 경우)
        
        # 기분에 따른 어조 변화
        mood_prefix = ""
        mood_suffix = ""
        if self.pet_state.mood < 30:
            mood_prefix = "(귀찮은 듯) "
            mood_suffix = "..."
        elif self.pet_state.mood > 80:
            mood_prefix = "(신나서) "
            mood_suffix = "!! ✨"
        
        # 배고픔 체크
        if self.pet_state.hunger < 20:
             return f"배고파서 힘이 없어... 밥 좀 줘... {mood_suffix}"

        # 키워드 처리
        if "안녕" in text or "hello" in text:
            return f"{mood_prefix}반가워! 오늘도 힘차게 보내자! {mood_suffix}"
        
        if "힘들어" in text or "피곤해" in text:
            return "잠시 쉬어가면서 해. 스트레칭 한 번 어때?"
            
        if "메뉴" in text or "밥" in text:
            self.command_triggered.emit("open_menu")
            return "메뉴를 열어줄게! 맛있는거 사줘."
        
        if "날씨" in text:
            self.command_triggered.emit("weather")
            return "잠시만, 날씨 확인해볼게..."
        
        if "뉴스" in text or "경제" in text:
            self.command_triggered.emit("news_eco")
            return "최신 경제 뉴스를 가져올게."
        
        if "환율" in text:
             self.command_triggered.emit("exchange")
             return "환율 정보를 조회중이야."
        
        if "놀자" in text or "심심해" in text:
             return "영어 퀴즈 풀래? 아니면 미니 던전 한 판? ⚔️"
        
        if "사랑해" in text or "좋아해" in text:
            self.pet_state.mood = min(100, self.pet_state.mood + 5)
            return "나도 정말 좋아해! ❤️ (기분이 좋아졌다)"
            
        if "바보" in text or "멍청이" in text:
            self.pet_state.mood = max(0, self.pet_state.mood - 10)
            return "너무해... 😢 (상처받았다)"
        
        if "상태" in text:
            return f"현재 내 상태야:\n체력: {int(self.pet_state.health)}\n지능: {int(self.pet_state.intellect)}\n기분: {int(self.pet_state.mood)}"

        # 기본 응답
        return f"{mood_prefix}무슨 말인지 잘 모르겠지만, 네가 있어 좋아! {mood_suffix}"
