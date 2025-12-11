from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QListWidget, QMessageBox, QGroupBox, QComboBox, QSpinBox, QFormLayout
)
from PyQt6.QtCore import pyqtSignal
from predictor import LottoPredictor
import numpy as np

class PredictionWidget(QWidget):
    # '내 번호' 탭에서 번호를 가져올 때 사용될 시그널
    load_numbers_to_prediction = pyqtSignal(list)

    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.predictor = LottoPredictor(data_manager) # ML 예측기 초기화
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout() # 메인 레이아웃을 가로 배치로 변경

        # --- Left Panel: Settings ---
        left_panel = QGroupBox("예측 설정")
        left_layout = QVBoxLayout()
        
        form_layout = QFormLayout()

        self.num_sets_spinbox = QSpinBox()
        self.num_sets_spinbox.setRange(1, 10)
        self.num_sets_spinbox.setValue(5)
        form_layout.addRow("예측 세트 수:", self.num_sets_spinbox)

        self.prediction_method_combo = QComboBox()
        self.prediction_method_combo.addItems(["독립 시행 (순수 랜덤)", "통계 기반 예측", "머신러닝 예측 (XGBoost)"])
        form_layout.addRow("예측 방식:", self.prediction_method_combo)

        # 제외/포함 번호 설정
        self.exclude_numbers_input = QLineEdit()
        self.exclude_numbers_input.setPlaceholderText("예: 44, 45 (쉼표로 구분)")
        form_layout.addRow("제외할 번호:", self.exclude_numbers_input)

        self.include_numbers_input = QLineEdit()
        self.include_numbers_input.setPlaceholderText("예: 7, 15 (쉼표로 구분)")
        form_layout.addRow("포함할 번호:", self.include_numbers_input)

        left_layout.addLayout(form_layout)

        self.predict_button = QPushButton("예측하기")
        self.predict_button.clicked.connect(self.predict_numbers)
        left_layout.addWidget(self.predict_button)
        
        left_layout.addStretch(1) # 하단 여백 채우기
        left_panel.setLayout(left_layout)
        
        # --- Right Panel: Results ---
        right_panel = QGroupBox("예측 결과")
        right_layout = QVBoxLayout()
        
        self.result_list_widget = QListWidget()
        right_layout.addWidget(self.result_list_widget)
        
        right_panel.setLayout(right_layout)

        # --- Add to Main Layout ---
        main_layout.addWidget(left_panel, 1) # 비율 1
        main_layout.addWidget(right_panel, 2) # 비율 2 (결과 영역을 더 넓게)

        self.setLayout(main_layout)
        
        # 시그널 연결 (MyNumbersWidget에서 번호를 가져올 때 사용)
        self.load_numbers_to_prediction.connect(self.set_include_numbers)

    def set_include_numbers(self, numbers):
        """'내 번호' 탭에서 전달된 번호를 포함할 번호 입력 필드에 설정합니다."""
        self.include_numbers_input.setText(', '.join(map(str, numbers)))
        QMessageBox.information(self, "번호 불러오기", f"'{', '.join(map(str, numbers))}' 번호가 예측에 포함될 번호로 설정되었습니다.")

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
        return sorted(list(set(numbers))) # 중복 제거 및 정렬

    def predict_numbers(self):
        num_sets = self.num_sets_spinbox.value()
        method = self.prediction_method_combo.currentText()
        exclude_numbers = self.parse_number_input(self.exclude_numbers_input.text())
        include_numbers = self.parse_number_input(self.include_numbers_input.text())

        # 제외 번호와 포함 번호의 충돌 확인
        if set(exclude_numbers).intersection(set(include_numbers)):
            QMessageBox.warning(self, "입력 오류", "제외할 번호와 포함할 번호에 중복이 있습니다.")
            return
        
        # 포함할 번호가 6개를 초과하는 경우
        if len(include_numbers) > 6:
            QMessageBox.warning(self, "입력 오류", f"포함할 번호가 6개({len(include_numbers)}개)를 초과할 수 없습니다. 처음 6개만 사용됩니다.")
            include_numbers = include_numbers[:6]

        self.result_list_widget.clear()
        
        for i in range(num_sets):
            predicted_nums = []
            if method == "독립 시행 (순수 랜덤)":
                predicted_nums = self.data_manager.generate_random_numbers(
                    exclude_numbers=exclude_numbers, include_numbers=include_numbers
                )
            elif method == "통계 기반 예측":
                predicted_nums = self.data_manager.generate_statistical_numbers(
                    exclude_numbers=exclude_numbers, include_numbers=include_numbers
                )
            elif method == "머신러닝 예측 (XGBoost)":
                # ML 모델 학습 (필요한 경우)
                if not self.predictor.is_trained:
                    self.result_list_widget.addItem("모델 학습 중... 잠시만 기다려주세요.")
                    QMessageBox.information(self, "학습 시작", "머신러닝 모델(XGBoost) 학습을 시작합니다. 데이터 양에 따라 시간이 소요될 수 있습니다.")
                    success = self.predictor.train()
                    if not success:
                        QMessageBox.critical(self, "오류", "모델 학습에 실패했습니다. 데이터 부족 등의 이유일 수 있습니다.")
                        self.result_list_widget.clear()
                        return

                # 최근 5회차 데이터 준비
                window_size = 5
                if len(self.data_manager.df) < window_size:
                     QMessageBox.warning(self, "데이터 부족", "예측을 위한 최근 데이터가 부족합니다.")
                     predicted_nums = []
                else:
                    # 최신순 정렬이므로 앞에서부터가 아니라, 날짜 정렬 후 뒤에서 가져와야 함
                    recent_df = self.data_manager.df.head(window_size).sort_values(by='draw_no', ascending=True)
                    number_cols = [f'num{i}' for i in range(1, 7)]
                    recent_data = recent_df[number_cols].values # shape (5, 6)
                    
                    # diversity를 위해 noise_level 주입
                    # 0.0 ~ 0.2 사이의 노이즈를 주어 확률 분포를 약간씩 흔듦
                    predicted_nums = self.predictor.predict(
                        recent_data, 
                        top_n=6, 
                        exclude_numbers=exclude_numbers, 
                        include_numbers=include_numbers,
                        noise_level=0.15 # 15% 정도의 변동성
                    )

            if predicted_nums:
                self.result_list_widget.addItem(f"예측 {i+1}: {', '.join(map(str, predicted_nums))}")
            else:
                self.result_list_widget.addItem(f"예측 {i+1}: 번호 생성 실패 (설정을 확인하세요)")
