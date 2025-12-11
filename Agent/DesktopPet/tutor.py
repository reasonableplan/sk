import random
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QPushButton, QMessageBox, QRadioButton, QButtonGroup
from PyQt6.QtCore import pyqtSignal, Qt

class EnglishTutor(QWidget):
    # 퀴즈 완료 시그널 (성공 여부, 획득 지능)
    quiz_finished = pyqtSignal(bool, int)

    def __init__(self):
        super().__init__()
        self.words = [
            {"word": "Apple", "meanings": ["사과", "바나나", "포도", "오렌지"], "answer": 0},
            {"word": "Computer", "meanings": ["계산기", "컴퓨터", "전화기", "텔레비전"], "answer": 1},
            {"word": "Python", "meanings": ["비단뱀", "자바", "C언어", "루비"], "answer": 0},
            {"word": "Developer", "meanings": ["디자이너", "기획자", "개발자", "마케터"], "answer": 2},
            {"word": "Library", "meanings": ["서점", "도서관", "학교", "병원"], "answer": 1},
            {"word": "Variable", "meanings": ["상수", "함수", "변수", "클래스"], "answer": 2},
            {"word": "Function", "meanings": ["기능", "함수", "변수", "객체"], "answer": 1},
            {"word": "Algorithm", "meanings": ["알고리즘", "자료구조", "네트워크", "운영체제"], "answer": 0},
        ]
        self.current_quiz = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("깜짝 영어 퀴즈!")
        self.setGeometry(300, 300, 300, 200)
        
        layout = QVBoxLayout()
        
        self.question_label = QLabel("단어: ???")
        self.question_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.question_label)

        self.radio_group = QButtonGroup()
        self.radios = []
        for i in range(4):
            radio = QRadioButton(f"보기 {i+1}")
            layout.addWidget(radio)
            self.radio_group.addButton(radio, i)
            self.radios.append(radio)

        self.submit_btn = QPushButton("정답 제출")
        self.submit_btn.clicked.connect(self.check_answer)
        layout.addWidget(self.submit_btn)

        self.setLayout(layout)

    def new_quiz(self):
        self.current_quiz = random.choice(self.words)
        self.question_label.setText(f"단어: {self.current_quiz['word']}")
        
        # 보기 섞기 (정답 인덱스 추적 필요하지만, 간단하게 구현 위해 
        # words 데이터 구조를 유지하되 표시만 랜덤하게? 
        # 여기서는 words 데이터 자체가 정답 인덱스를 가지고 있으므로 
        # 보기를 섞으려면 정답 인덱스도 바꿔야 함.
        # 간단하게 words 데이터의 meanings 순서를 그대로 사용하겠습니다.)
        
        meanings = self.current_quiz['meanings']
        for i, radio in enumerate(self.radios):
            radio.setText(meanings[i])
            radio.setChecked(False)
        
        self.show()

    def check_answer(self):
        if self.current_quiz is None:
            return

        selected_id = self.radio_group.checkedId()
        if selected_id == -1:
            QMessageBox.warning(self, "선택", "정답을 선택해주세요.")
            return

        if selected_id == self.current_quiz['answer']:
            QMessageBox.information(self, "정답!", "맞았습니다! 지능이 2 상승합니다.")
            self.quiz_finished.emit(True, 2)
            self.close()
        else:
            correct_meaning = self.current_quiz['meanings'][self.current_quiz['answer']]
            QMessageBox.critical(self, "땡!", f"틀렸습니다. 정답은 '{correct_meaning}' 입니다.")
            self.quiz_finished.emit(False, 0)
            self.close()
