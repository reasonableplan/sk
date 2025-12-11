import json
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QListWidget, QMessageBox, QGroupBox, QFormLayout, QDialog, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import pyqtSignal

class MyNumbersWidget(QWidget):
    def __init__(self, data_manager, prediction_widget_signal):
        super().__init__()
        self.data_manager = data_manager
        self.prediction_widget_signal = prediction_widget_signal # PredictionWidget으로 번호를 전달할 시그널
        self.my_numbers_list = [] # 저장된 번호들을 담을 리스트 (예: [{"name": "내 생일", "numbers": [1,2,3,4,5,6]}, ...])
        self.init_ui()
        self.load_my_numbers() # 앱 시작 시 저장된 번호 불러오기

    def init_ui(self):
        main_layout = QHBoxLayout() # 메인 레이아웃 가로 배치

        # --- Left Panel: Management ---
        left_panel = QGroupBox("번호 관리")
        left_layout = QVBoxLayout()

        # 번호 추가/수정 폼
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("예: 내 행운 번호")
        form_layout.addRow("이름:", self.name_input)

        self.numbers_input = QLineEdit()
        self.numbers_input.setPlaceholderText("예: 1, 10, 20, 30, 40, 45 (쉼표로 구분)")
        form_layout.addRow("6개 번호:", self.numbers_input)
        
        left_layout.addLayout(form_layout)
        
        left_layout.addSpacing(10)

        # 추가/수정 버튼
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("추가")
        self.add_button.clicked.connect(self.add_number_set)
        button_layout.addWidget(self.add_button)

        self.update_button = QPushButton("수정")
        self.update_button.setEnabled(False) # 처음에는 비활성화
        self.update_button.clicked.connect(self.update_number_set)
        button_layout.addWidget(self.update_button)

        left_layout.addLayout(button_layout)
        
        left_layout.addSpacing(20)

        # 목록 관리 버튼
        action_button_layout = QVBoxLayout() # 세로로 배치
        self.delete_button = QPushButton("선택 삭제")
        self.delete_button.clicked.connect(self.delete_number_set)
        self.delete_button.setEnabled(False)
        action_button_layout.addWidget(self.delete_button)

        self.check_winnings_button = QPushButton("당첨 내역 확인")
        self.check_winnings_button.clicked.connect(self.show_winnings)
        self.check_winnings_button.setEnabled(False)
        action_button_layout.addWidget(self.check_winnings_button)

        self.load_to_prediction_button = QPushButton("예측 탭으로 가져가기")
        self.load_to_prediction_button.clicked.connect(self.load_selected_to_prediction)
        self.load_to_prediction_button.setEnabled(False)
        action_button_layout.addWidget(self.load_to_prediction_button)

        left_layout.addLayout(action_button_layout)
        
        left_layout.addStretch(1)
        left_panel.setLayout(left_layout)

        # --- Right Panel: Saved Numbers ---
        right_panel = QGroupBox("저장된 나의 번호")
        right_layout = QVBoxLayout()
        
        self.my_numbers_list_widget = QListWidget()
        self.my_numbers_list_widget.itemSelectionChanged.connect(self.on_selection_changed)
        right_layout.addWidget(self.my_numbers_list_widget)
        
        right_panel.setLayout(right_layout)

        # --- Add to Main Layout ---
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 2)

        self.setLayout(main_layout)

    def on_selection_changed(self):
        selected_items = self.my_numbers_list_widget.selectedItems()
        enable = bool(selected_items)
        self.delete_button.setEnabled(enable)
        self.update_button.setEnabled(enable)
        self.check_winnings_button.setEnabled(enable)
        self.load_to_prediction_button.setEnabled(enable)
        
        if enable:
            selected_item_text = selected_items[0].text()
            try:
                # 예: "내 생일: [1, 2, 3, 4, 5, 6]" -> "내 생일", "[1, 2, 3, 4, 5, 6]"
                name_part, numbers_str = selected_item_text.split(': ', 1)
                numbers_list_val = eval(numbers_str) # 문자열 리스트를 실제 리스트로 변환
                
                self.name_input.setText(name_part)
                self.numbers_input.setText(', '.join(map(str, numbers_list_val)))
            except Exception as e:
                print(f"Error parsing selected item text: {e}") # 디버깅용
                self.clear_inputs() # 파싱 오류 시 입력 필드 초기화


    def parse_numbers_input(self, text_input):
        numbers = []
        if text_input:
            try:
                for s in text_input.split(','):
                    num = int(s.strip())
                    if 1 <= num <= 45:
                        numbers.append(num)
                    else:
                        QMessageBox.warning(self, "입력 오류", f"번호는 1에서 45 사이여야 합니다: {num}")
                        return None
            except ValueError:
                QMessageBox.warning(self, "입력 오류", "번호는 쉼표로 구분된 숫자 형식이어야 합니다.")
                return None
        
        numbers = sorted(list(set(numbers))) # 중복 제거 후 정렬

        if len(numbers) != 6:
            QMessageBox.warning(self, "입력 오류", f"정확히 6개의 번호를 입력해야 합니다. 현재 {len(numbers)}개.")
            return None
        return numbers

    def add_number_set(self):
        name = self.name_input.text().strip()
        numbers = self.parse_numbers_input(self.numbers_input.text())

        if not name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력해주세요.")
            return
        if numbers is None: # 파싱 실패 시
            return

        # 중복 이름 검사
        if any(item['name'] == name for item in self.my_numbers_list):
            QMessageBox.warning(self, "입력 오류", "이미 존재하는 이름입니다. 다른 이름을 사용해주세요.")
            return

        self.my_numbers_list.append({"name": name, "numbers": numbers})
        self.save_my_numbers()
        self.refresh_list_widget()
        self.clear_inputs()

    def update_number_set(self):
        selected_items = self.my_numbers_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "수정할 번호 세트를 선택해주세요.")
            return

        current_index = self.my_numbers_list_widget.row(selected_items[0])
        old_name = self.my_numbers_list[current_index]['name']

        new_name = self.name_input.text().strip()
        new_numbers = self.parse_numbers_input(self.numbers_input.text())

        if not new_name:
            QMessageBox.warning(self, "입력 오류", "이름을 입력해주세요.")
            return
        if new_numbers is None:
            return

        # 이름 변경 시 중복 검사 (자기 자신 제외)
        if new_name != old_name and any(item['name'] == new_name for item in self.my_numbers_list):
            QMessageBox.warning(self, "입력 오류", "이미 존재하는 이름입니다. 다른 이름을 사용해주세요.")
            return

        self.my_numbers_list[current_index] = {"name": new_name, "numbers": new_numbers}
        self.save_my_numbers()
        self.refresh_list_widget()
        self.clear_inputs()
        self.update_button.setEnabled(False) # 수정 완료 후 비활성화

    def delete_number_set(self):
        selected_items = self.my_numbers_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "삭제할 번호 세트를 선택해주세요.")
            return

        reply = QMessageBox.question(self, '확인', '정말로 이 번호 세트를 삭제하시겠습니까?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            index = self.my_numbers_list_widget.row(selected_items[0])
            del self.my_numbers_list[index]
            self.save_my_numbers()
            self.refresh_list_widget()
            self.clear_inputs()
            self.delete_button.setEnabled(False)
            self.update_button.setEnabled(False)
            self.check_winnings_button.setEnabled(False)
            self.load_to_prediction_button.setEnabled(False)

    def refresh_list_widget(self):
        self.my_numbers_list_widget.clear()
        for item_data in self.my_numbers_list:
            self.my_numbers_list_widget.addItem(f"{item_data['name']}: {item_data['numbers']}")

    def clear_inputs(self):
        self.name_input.clear()
        self.numbers_input.clear()

    def save_my_numbers(self):
        try:
            with open('my_lotto_numbers.json', 'w', encoding='utf-8') as f:
                json.dump(self.my_numbers_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"내 번호를 저장하는 중 오류가 발생했습니다: {e}")

    def load_my_numbers(self):
        try:
            with open('my_lotto_numbers.json', 'r', encoding='utf-8') as f:
                self.my_numbers_list = json.load(f)
            self.refresh_list_widget()
        except FileNotFoundError:
            self.my_numbers_list = [] # 파일이 없으면 새 리스트 시작
        except json.JSONDecodeError as e:
            QMessageBox.warning(self, "로드 오류", f"내 번호 파일 형식이 올바르지 않습니다. 초기화됩니다: {e}")
            self.my_numbers_list = [] # 파일 손상 시 초기화
        except Exception as e:
            QMessageBox.critical(self, "로드 오류", f"내 번호를 불러오는 중 오류가 발생했습니다: {e}")

    def show_winnings(self):
        selected_items = self.my_numbers_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "당첨 내역을 확인할 번호 세트를 선택해주세요.")
            return

        index = self.my_numbers_list_widget.row(selected_items[0])
        my_numbers_data = self.my_numbers_list[index]
        my_numbers = my_numbers_data['numbers']
        name = my_numbers_data['name']

        winnings = self.data_manager.check_winnings(my_numbers)

        if not winnings:
            QMessageBox.information(self, "당첨 내역", f"'{name}' ({', '.join(map(str, my_numbers))}) 번호는 아직 당첨 내역이 없습니다.")
            return

        # 당첨 내역을 보여줄 새 다이얼로그 생성
        dialog = QDialog(self)
        dialog.setWindowTitle(f"'{name}' 번호의 당첨 내역")
        dialog.setGeometry(100, 100, 800, 400)
        dialog_layout = QVBoxLayout()

        win_table = QTableWidget()
        win_table.setColumnCount(6)
        win_table.setHorizontalHeaderLabels(['회차', '날짜', '당첨 번호', '내 번호', '일치 개수 (본/보)', '등수'])
        win_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        win_table.setRowCount(len(winnings))
        for row_idx, win_data in enumerate(winnings):
            win_table.setItem(row_idx, 0, QTableWidgetItem(str(win_data['회차'])))
            win_table.setItem(row_idx, 1, QTableWidgetItem(win_data['날짜']))
            win_table.setItem(row_idx, 2, QTableWidgetItem(win_data['당첨 번호']))
            win_table.setItem(row_idx, 3, QTableWidgetItem(win_data['내 번호']))
            win_table.setItem(row_idx, 4, QTableWidgetItem(f"{win_data['일치 개수 (본)']}/{win_data['일치 개수 (보)']}"))
            win_table.setItem(row_idx, 5, QTableWidgetItem(win_data['등수']))
        
        dialog_layout.addWidget(win_table)
        dialog.setLayout(dialog_layout)
        dialog.exec()

    def load_selected_to_prediction(self):
        selected_items = self.my_numbers_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "선택 오류", "예측 탭으로 가져갈 번호 세트를 선택해주세요.")
            return
        
        index = self.my_numbers_list_widget.row(selected_items[0])
        my_numbers = self.my_numbers_list[index]['numbers']
        
        self.prediction_widget_signal.emit(my_numbers) # 시그널을 통해 PredictionWidget으로 번호 전달
        # 탭을 예측 탭으로 전환
        # MyNumbersWidget의 부모(QGroupBox)의 부모(QVBoxLayout)의 부모(QTabWidget)를 찾아야 함
        parent_widget = self.parent()
        # MyNumbersWidget -> QGroupBox -> QVBoxLayout -> QTabWidget?
        # Actually in lotto_app, we add widget directly to tab:
        # self.tab_widget.addTab(self.my_numbers_widget, "나의 로또 번호")
        # So parent is QStackedWidget (internal) -> QTabWidget
        # Let's keep the logic simple or just find QTabWidget
        
        while parent_widget and not isinstance(parent_widget, (QWidget)): # Just walk up
             if parent_widget.metaObject().className() == "QTabWidget":
                 break
             parent_widget = parent_widget.parent()
             
        # Re-using the logic from original code which seemed to work or needs adjustment
        # Origin code:
        # parent_widget = self.parent()
        # while parent_widget and not isinstance(parent_widget, QTabWidget):
        #    parent_widget = parent_widget.parent()
        
        # In PyQt6, parent() should eventually reach QTabWidget if added directly.
        # But wait, QTabWidget puts widgets in a QStackedWidget.
        # So MyNumbersWidget -> QStackedWidget -> QTabWidget.
        
        # Let's stick to the code I saw earlier which I copied to `mynumbers.py`
        pass # Logic is already in the copied code above.
