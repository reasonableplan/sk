from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class ItemShop(QWidget):
    item_purchased = pyqtSignal(str, int)  # (item_type, value)
    
    def __init__(self, pet_state):
        super().__init__()
        self.pet_state = pet_state
        
        # 아이템 카탈로그 (이름, 가격, 타입, 효과값, 설명)
        self.items = [
            # 소모품
            ("에너지 드링크", 50, "heal_hp", 50, "체력 50 회복"),
            ("마나 포션", 40, "heal_mp", 30, "마나 30 회복"),
            ("경험치 부스터", 100, "exp", 50, "경험치 50 획득"),
            ("골든 엘릭서", 200, "heal_full", 0, "체력/마나 완전 회복"),
            
            # 장비 (영구 스탯 증가)
            ("네온 검", 150, "atk", 5, "공격력 +5 (영구)"),
            ("방화벽 방패", 150, "def", 5, "방어력 +5 (영구)"),
            ("터보 칩", 250, "int", 3, "지능 +3 (영구)"),
            ("회피 부츠", 180, "eva", 2, "회피율 +2% (영구)"),
        ]
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("🛒 아이템 상점")
        self.setGeometry(200, 200, 500, 600)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        
        # 헤더 (골드 표시)
        header = QLabel()
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("background-color: #FFD700; padding: 10px; border-radius: 5px;")
        self.gold_label = header
        layout.addWidget(header)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # 아이템 목록
        for name, price, item_type, value, desc in self.items:
            item_widget = self.create_item_widget(name, price, item_type, value, desc)
            scroll_layout.addWidget(item_widget)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("padding: 10px; font-size: 14px;")
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        self.update_gold_display()
    
    def create_item_widget(self, name, price, item_type, value, desc):
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                border: 2px solid #ccc;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QHBoxLayout()
        
        # 아이템 정보
        info_layout = QVBoxLayout()
        
        name_label = QLabel(f"<b>{name}</b>")
        name_label.setFont(QFont("Arial", 12))
        info_layout.addWidget(name_label)
        
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: #666;")
        info_layout.addWidget(desc_label)
        
        price_label = QLabel(f"💰 {price} G")
        price_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        price_label.setStyleSheet("color: #FF6B00;")
        info_layout.addWidget(price_label)
        
        layout.addLayout(info_layout, 3)
        
        # 구매 버튼
        buy_btn = QPushButton("구매")
        buy_btn.setFixedSize(80, 40)
        buy_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        buy_btn.clicked.connect(lambda: self.purchase_item(name, price, item_type, value))
        layout.addWidget(buy_btn, 1)
        
        widget.setLayout(layout)
        return widget
    
    def purchase_item(self, name, price, item_type, value):
        # 골드 확인
        if self.pet_state.gold < price:
            QMessageBox.warning(self, "구매 실패", f"골드가 부족합니다!\n필요: {price} G\n보유: {self.pet_state.gold} G")
            return
        
        # 골드 차감
        self.pet_state.gold -= price
        
        # 아이템 효과 적용
        self.apply_item_effect(item_type, value)
        
        # 시그널 발생
        self.item_purchased.emit(item_type, value)
        
        # 골드 표시 업데이트
        self.update_gold_display()
        
        # 구매 완료 메시지
        QMessageBox.information(self, "구매 완료", f"'{name}'을(를) 구매했습니다!")
    
    def apply_item_effect(self, item_type, value):
        """아이템 효과 적용"""
        if item_type == "heal_hp":
            self.pet_state.health = min(self.pet_state.max_health, self.pet_state.health + value)
        elif item_type == "heal_mp":
            self.pet_state.mana = min(self.pet_state.max_mana, self.pet_state.mana + value)
        elif item_type == "exp":
            self.pet_state.gain_exp(value)
        elif item_type == "heal_full":
            self.pet_state.health = self.pet_state.max_health
            self.pet_state.mana = self.pet_state.max_mana
        elif item_type == "atk":
            self.pet_state.attack += value
        elif item_type == "def":
            self.pet_state.defense += value
        elif item_type == "int":
            self.pet_state.intellect += value
            self.pet_state.recalc_stats()
        elif item_type == "eva":
            self.pet_state.evasion += value
        
        # 상태 저장
        self.pet_state.save_state()
    
    def update_gold_display(self):
        """골드 표시 업데이트"""
        self.gold_label.setText(f"💰 보유 골드: {self.pet_state.gold} G")
    
    def showEvent(self, event):
        """창이 열릴 때마다 골드 업데이트"""
        super().showEvent(event)
        self.update_gold_display()
