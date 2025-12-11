import random
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QInputDialog, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt

class MenuMaster(QWidget):
    # (음식 이름, 기분 변화량, 체력 변화량, 배고픔 변화량)
    # User가 추천해준 경우 -> 펫의 반응 결과 리턴
    feed_finished = pyqtSignal(str, int, int, int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("오늘 뭐 먹지?")
        self.setGeometry(400, 400, 300, 200)

        # 간단한 음식 데이터베이스
        self.foods = {
            "샐러드": {"health": 10, "mood": 5, "hunger": 20, "type": "healthy"},
            "피자": {"health": -5, "mood": 20, "hunger": 50, "type": "tasty"},
            "치킨": {"health": -5, "mood": 25, "hunger": 60, "type": "tasty"},
            "삼겹살": {"health": -2, "mood": 20, "hunger": 50, "type": "tasty"},
            "김치찌개": {"health": 5, "mood": 15, "hunger": 40, "type": "korean"},
            "파전": {"health": 0, "mood": 15, "hunger": 30, "type": "rainy"},
            "비빔밥": {"health": 10, "mood": 10, "hunger": 40, "type": "korean"},
            "햄버거": {"health": -5, "mood": 15, "hunger": 40, "type": "fastfood"},
        }
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("배고파요... 뭐 먹을까요?")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        btn_recommend = QPushButton("펫에게 메뉴 추천받기")
        btn_recommend.clicked.connect(self.get_recommendation)
        layout.addWidget(btn_recommend)

        btn_suggest = QPushButton("내가 메뉴 추천해주기 (밥 주기)")
        btn_suggest.clicked.connect(self.suggest_food)
        layout.addWidget(btn_suggest)

        self.setLayout(layout)

    def get_recommendation(self):
        # 간단한 추천 로직 (랜덤)
        # 날씨 API 연동 가능 (비오면 파전 등)
        food_name = random.choice(list(self.foods.keys()))
        QMessageBox.information(self, "추천 메뉴", f"오늘의 추천 메뉴는 '{food_name}' 어떠세요?")
        self.close()

    def suggest_food(self):
        # 사용자가 펫에게 밥을 주는 기능 (입력받기)
        items = list(self.foods.keys())
        item, ok = QInputDialog.getItem(self, "밥 주기", "어떤 음식을 줄까요?", items, 0, False)
        
        if ok and item:
            data = self.foods[item]
            
            # 펫의 반응 (간단한 메시지 박스)
            reaction = ""
            if data['health'] > 0:
                reaction = "건강해지는 맛이에요! (체력 증가)"
            elif data['health'] < 0:
                reaction = "너무 맛있어요! 근데 살찔 것 같아요... (기분 좋음, 체력 소폭 감소)"
            else:
                reaction = "잘 먹겠습니다! (배부름)"

            QMessageBox.information(self, "냠냠", f"{item}을(를) 먹었습니다.\n{reaction}")
            
            # 메인 앱에 신호 전달
            self.feed_finished.emit(item, data['mood'], data['health'], data['hunger'])
            self.close()
