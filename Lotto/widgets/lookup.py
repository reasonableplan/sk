from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QComboBox, 
    QDateEdit, QHeaderView
)
from PyQt6.QtCore import QDate
from PyQt6.QtGui import QIntValidator

class LookupWidget(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout() # 메인 레이아웃 가로 배치

        # --- Left Panel: Search Conditions ---
        left_panel = QGroupBox("조회 조건")
        left_layout = QVBoxLayout()

        # 회차 검색
        draw_no_group = QVBoxLayout()
        draw_no_group.addWidget(QLabel("회차 검색:"))
        self.draw_no_input = QLineEdit()
        self.draw_no_input.setPlaceholderText("예: 1201")
        self.draw_no_input.setValidator(QIntValidator(1, 9999))
        draw_no_group.addWidget(self.draw_no_input)
        left_layout.addLayout(draw_no_group)
        
        left_layout.addSpacing(10)

        # 날짜 검색
        date_group = QVBoxLayout()
        date_group.addWidget(QLabel("날짜 범위 검색:"))
        date_selection_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1)) # 기본 1년 전
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())
        date_selection_layout.addWidget(self.start_date_edit)
        date_selection_layout.addWidget(QLabel("~"))
        date_selection_layout.addWidget(self.end_date_edit)
        date_group.addLayout(date_selection_layout)
        left_layout.addLayout(date_group)

        left_layout.addSpacing(10)

        # 번호 포함 검색
        numbers_group = QVBoxLayout()
        numbers_group.addWidget(QLabel("번호 포함 검색:"))
        self.search_numbers_input = QLineEdit()
        self.search_numbers_input.setPlaceholderText("예: 7, 15, 22")
        numbers_group.addWidget(self.search_numbers_input)

        self.match_type_combo = QComboBox()
        self.match_type_combo.addItems(["모든 번호 포함", "하나라도 포함"])
        numbers_group.addWidget(self.match_type_combo)

        self.include_bonus_combo = QComboBox()
        self.include_bonus_combo.addItems(["보너스 번호 포함 검색", "보너스 번호 제외 검색"])
        numbers_group.addWidget(self.include_bonus_combo)

        left_layout.addLayout(numbers_group)
        
        left_layout.addSpacing(20)

        self.search_button = QPushButton("조회하기")
        self.search_button.clicked.connect(self.perform_search)
        left_layout.addWidget(self.search_button)

        left_layout.addStretch(1)
        left_panel.setLayout(left_layout)

        # --- Right Panel: Results ---
        right_panel = QGroupBox("조회 결과")
        right_layout = QVBoxLayout()
        
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(9)
        self.result_table.setHorizontalHeaderLabels(['회차', '날짜', '당첨1', '당첨2', '당첨3', '당첨4', '당첨5', '당첨6', '보너스'])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents) # 내용에 맞춰 크기 자동 조절
        right_layout.addWidget(self.result_table)
        
        right_panel.setLayout(right_layout)

        # --- Add to Main Layout ---
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 3) # 결과창을 더 넓게

        self.setLayout(main_layout)

    def parse_number_input(self, text_input):
        """쉼표로 구분된 숫자 문자열을 파싱하여 정수 리스트로 반환"""
        numbers = []
        if text_input:
            try:
                for s in text_input.split(','):
                    num = int(s.strip())
                    if 1 <= num <= 45:
                        numbers.append(num)
                    else:
                        QMessageBox.warning(self, "입력 오류", f"번호는 1에서 45 사이여야 합니다: {num}")
                        return []
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "번호는 쉼표로 구분된 숫자 형식이어야 합니다.")
                return []
        return sorted(list(set(numbers)))

    def perform_search(self):
        self.result_table.setRowCount(0) # 기존 결과 초기화
        
        draw_no_text = self.draw_no_input.text()
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()
        search_numbers_text = self.search_numbers_input.text()
        
        results = []

        if draw_no_text: # 회차 검색
            try:
                draw_no = int(draw_no_text)
                result = self.data_manager.get_draw_by_no(draw_no)
                if result:
                    results.append(result)
                else:
                    QMessageBox.information(self, "조회 결과", f"{draw_no}회차 정보를 찾을 수 없습니다.")
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "회차는 숫자여야 합니다.")
                return
        elif search_numbers_text: # 번호 포함 검색
            search_numbers = self.parse_number_input(search_numbers_text)
            if not search_numbers:
                return # 파싱 오류 발생 시 중단
            
            match_all = (self.match_type_combo.currentIndex() == 0) # 0: 모든 번호 포함, 1: 하나라도 포함
            include_bonus = (self.include_bonus_combo.currentIndex() == 0) # 0: 보너스 포함, 1: 보너스 제외

            results = self.data_manager.get_draws_by_numbers(search_numbers, match_all, include_bonus)

        else: # 날짜 범위 검색
            if start_date > end_date:
                QMessageBox.warning(self, "입력 오류", "시작 날짜는 종료 날짜보다 빠르거나 같아야 합니다.")
                return
            results = self.data_manager.get_draws_by_date_range(start_date, end_date)

        self.display_results(results)

    def display_results(self, results):
        self.result_table.setRowCount(len(results))
        for row_idx, data in enumerate(results):
            self.result_table.setItem(row_idx, 0, QTableWidgetItem(str(data['draw_no'])))
            self.result_table.setItem(row_idx, 1, QTableWidgetItem(data['draw_date'].strftime('%Y-%m-%d')))
            for i in range(1, 7):
                self.result_table.setItem(row_idx, i+1, QTableWidgetItem(str(data[f'num{i}'])))
            self.result_table.setItem(row_idx, 8, QTableWidgetItem(str(data['bonus_num'])))
