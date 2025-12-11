from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QComboBox, 
    QSpinBox, QTabWidget, QHeaderView
)
from PyQt6.QtGui import QIntValidator
from .mpl_canvas import MplCanvas

class AnalysisWidget(QWidget):
    def __init__(self, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.init_ui()
        self.load_analysis_data()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h2>로또 번호 분석</h2>"))

        # 분석 결과 표시를 위한 탭 위젯 (번호 빈도, 간격, 번호쌍, 시각화 등)
        self.analysis_tab_widget = QTabWidget()
        layout.addWidget(self.analysis_tab_widget)

        # --- 번호별 빈도 탭 ---
        freq_tab = QWidget()
        freq_layout = QHBoxLayout() # 가로 배치
        freq_tab.setLayout(freq_layout)
        self.analysis_tab_widget.addTab(freq_tab, "번호별 빈도")

        # Left Panel: Settings
        freq_left_panel = QGroupBox("분석 설정")
        freq_left_layout = QVBoxLayout()
        
        # 특정 번호 검색
        search_specific_layout = QVBoxLayout()
        search_specific_layout.addWidget(QLabel("특정 번호 검색 (1~45):"))
        self.specific_num_input = QLineEdit()
        self.specific_num_input.setValidator(QIntValidator(1, 45))
        search_specific_layout.addWidget(self.specific_num_input)
        self.search_specific_button = QPushButton("검색")
        self.search_specific_button.clicked.connect(self.search_specific_number)
        search_specific_layout.addWidget(self.search_specific_button)
        self.specific_num_result_label = QLabel("결과:")
        search_specific_layout.addWidget(self.specific_num_result_label)
        freq_left_layout.addLayout(search_specific_layout)
        
        freq_left_layout.addSpacing(20)

        # 상위/하위 N개
        top_bottom_layout = QVBoxLayout()
        top_bottom_layout.addWidget(QLabel("상위/하위 N개 표시:"))
        self.top_bottom_spinbox = QSpinBox()
        self.top_bottom_spinbox.setRange(1, 45)
        self.top_bottom_spinbox.setValue(10)
        top_bottom_layout.addWidget(self.top_bottom_spinbox)
        
        self.show_top_button = QPushButton("상위 N개 보기")
        self.show_top_button.clicked.connect(lambda: self.display_frequency_table(top_n=self.top_bottom_spinbox.value()))
        top_bottom_layout.addWidget(self.show_top_button)
        
        self.show_bottom_button = QPushButton("하위 N개 보기")
        self.show_bottom_button.clicked.connect(lambda: self.display_frequency_table(bottom_n=self.top_bottom_spinbox.value()))
        top_bottom_layout.addWidget(self.show_bottom_button)
        
        freq_left_layout.addLayout(top_bottom_layout)
        freq_left_layout.addStretch(1)
        freq_left_panel.setLayout(freq_left_layout)

        # Right Panel: Table
        freq_right_panel = QGroupBox("빈도 분석 결과")
        freq_right_layout = QVBoxLayout()
        self.freq_table = QTableWidget()
        self.freq_table.setColumnCount(3)
        self.freq_table.setHorizontalHeaderLabels(['번호', '출현 횟수', '비율(%)'])
        self.freq_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        freq_right_layout.addWidget(self.freq_table)
        freq_right_panel.setLayout(freq_right_layout)

        # Add to Tab Layout
        freq_layout.addWidget(freq_left_panel, 1)
        freq_layout.addWidget(freq_right_panel, 3)

        # --- 미출현 기간 분석 탭 ---
        gap_tab = QWidget()
        gap_layout = QHBoxLayout()
        gap_tab.setLayout(gap_layout)
        self.analysis_tab_widget.addTab(gap_tab, "미출현 기간 분석")
        
        # Left Panel (Description/Info)
        gap_left_panel = QGroupBox("분석 정보")
        gap_left_layout = QVBoxLayout()
        gap_left_layout.addWidget(QLabel("<h3>미출현 기간 분석</h3>"))
        gap_left_layout.addWidget(QLabel("각 번호가 마지막으로 출현한 이후\n현재까지 경과한 회차를 보여줍니다.\n\n오랫동안 나오지 않은 번호를\n'장기 미출현 번호'라고 합니다."))
        gap_left_layout.addStretch(1)
        gap_left_panel.setLayout(gap_left_layout)

        # Right Panel (Table)
        gap_right_panel = QGroupBox("분석 결과")
        gap_right_layout = QVBoxLayout()
        self.gap_table = QTableWidget()
        self.gap_table.setColumnCount(3)
        self.gap_table.setHorizontalHeaderLabels(['번호', '마지막 출현 회차', '미출현 기간 (회차)'])
        self.gap_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        gap_right_layout.addWidget(self.gap_table)
        gap_right_panel.setLayout(gap_right_layout)

        gap_layout.addWidget(gap_left_panel, 1)
        gap_layout.addWidget(gap_right_panel, 3)

        # --- 번호쌍 분석 탭 ---
        pair_tab = QWidget()
        pair_layout = QHBoxLayout()
        pair_tab.setLayout(pair_layout)
        self.analysis_tab_widget.addTab(pair_tab, "번호쌍 분석")

        # Left Panel: Settings
        pair_left_panel = QGroupBox("분석 설정")
        pair_left_layout = QVBoxLayout()

        # 2쌍 분석 설정
        pair_left_layout.addWidget(QLabel("<b>[2쌍 번호 분석]</b>"))
        pair_left_layout.addWidget(QLabel("표시할 2쌍 개수:"))
        self.pair2_spinbox = QSpinBox()
        self.pair2_spinbox.setRange(5, 50)
        self.pair2_spinbox.setValue(10)
        pair_left_layout.addWidget(self.pair2_spinbox)
        self.pair2_button = QPushButton("2쌍 분석 실행")
        self.pair2_button.clicked.connect(self.analyze_pairs_2)
        pair_left_layout.addWidget(self.pair2_button)
        
        pair_left_layout.addSpacing(20)

        # 3쌍 분석 설정
        pair_left_layout.addWidget(QLabel("<b>[3쌍 번호 분석]</b>"))
        pair_left_layout.addWidget(QLabel("표시할 3쌍 개수:"))
        self.pair3_spinbox = QSpinBox()
        self.pair3_spinbox.setRange(5, 50)
        self.pair3_spinbox.setValue(10)
        pair_left_layout.addWidget(self.pair3_spinbox)
        self.pair3_button = QPushButton("3쌍 분석 실행")
        self.pair3_button.clicked.connect(self.analyze_pairs_3)
        pair_left_layout.addWidget(self.pair3_button)
        
        pair_left_layout.addStretch(1)
        pair_left_panel.setLayout(pair_left_layout)

        # Right Panel: Tables (Stacked vertically)
        pair_right_panel = QGroupBox("분석 결과")
        pair_right_layout = QVBoxLayout()
        
        pair_right_layout.addWidget(QLabel("<b>가장 많이 나온 2쌍</b>"))
        self.pair2_table = QTableWidget()
        self.pair2_table.setColumnCount(2)
        self.pair2_table.setHorizontalHeaderLabels(['번호 2쌍', '출현 횟수'])
        self.pair2_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pair_right_layout.addWidget(self.pair2_table)
        
        pair_right_layout.addSpacing(10)

        pair_right_layout.addWidget(QLabel("<b>가장 많이 나온 3쌍</b>"))
        self.pair3_table = QTableWidget()
        self.pair3_table.setColumnCount(2)
        self.pair3_table.setHorizontalHeaderLabels(['번호 3쌍', '출현 횟수'])
        self.pair3_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        pair_right_layout.addWidget(self.pair3_table)
        
        pair_right_panel.setLayout(pair_right_layout)

        pair_layout.addWidget(pair_left_panel, 1)
        pair_layout.addWidget(pair_right_panel, 2)
        
        # --- 시각화 탭 ---
        viz_tab = QWidget()
        viz_layout = QHBoxLayout()
        viz_tab.setLayout(viz_layout)
        self.analysis_tab_widget.addTab(viz_tab, "시각화")

        # Left Panel (Controls)
        viz_left_panel = QGroupBox("그래프 설정")
        viz_left_layout = QVBoxLayout()
        
        self.plot_button = QPushButton("번호별 출현 빈도 그래프")
        self.plot_button.clicked.connect(self.plot_frequency_chart)
        viz_left_layout.addWidget(self.plot_button)
        
        viz_left_layout.addStretch(1)
        viz_left_panel.setLayout(viz_left_layout)

        # Right Panel (Canvas)
        viz_right_panel = QGroupBox("시각화 결과")
        viz_right_layout = QVBoxLayout()
        self.canvas = MplCanvas(self, width=8, height=6, dpi=100)
        viz_right_layout.addWidget(self.canvas)
        viz_right_panel.setLayout(viz_right_layout)

        viz_layout.addWidget(viz_left_panel, 1)
        viz_layout.addWidget(viz_right_panel, 3)

        layout.addStretch(1)
        self.setLayout(layout)

    def load_analysis_data(self):
        # 이 함수는 초기화 시 한 번만 호출되어 모든 분석 데이터를 로드하고 UI에 표시합니다.
        self.all_freq_data = self.data_manager.get_number_frequency()
        self.gap_analysis_data = self.data_manager.get_gap_analysis()
        self.display_frequency_table() # 초기 로드 시 전체 빈도 표시
        self.display_gap_analysis() # 초기 로드 시 미출현 기간 분석 표시
        self.analyze_pairs_2()
        self.analyze_pairs_3()
        self.plot_frequency_chart()

    def display_frequency_table(self, top_n=None, bottom_n=None):
        if top_n:
            data = self.data_manager.get_top_n_frequencies(top_n, ascending=False)
        elif bottom_n:
            data = self.data_manager.get_top_n_frequencies(bottom_n, ascending=True)
        else:
            data = self.all_freq_data # 전체 데이터

        self.freq_table.setRowCount(len(data))
        for row_idx, item in enumerate(data):
            self.freq_table.setItem(row_idx, 0, QTableWidgetItem(str(item['number'])))
            self.freq_table.setItem(row_idx, 1, QTableWidgetItem(str(item['count'])))
            self.freq_table.setItem(row_idx, 2, QTableWidgetItem(str(item['percentage'])))

    def search_specific_number(self):
        num_str = self.specific_num_input.text()
        try:
            num = int(num_str)
            if not (1 <= num <= 45):
                raise ValueError
            
            found_count = 0
            for item in self.all_freq_data:
                if item['number'] == num:
                    found_count = item['count']
                    break
            
            self.specific_num_result_label.setText(f"결과: 번호 {num}은(는) 총 {found_count}회 출현했습니다.")

        except ValueError:
            QMessageBox.warning(self, "입력 오류", "1에서 45 사이의 유효한 숫자를 입력하세요.")
            self.specific_num_result_label.setText("결과:")

    def display_gap_analysis(self):
        data = self.gap_analysis_data
        self.gap_table.setRowCount(len(data))
        for row_idx, item in enumerate(data):
            self.gap_table.setItem(row_idx, 0, QTableWidgetItem(str(item['number'])))
            self.gap_table.setItem(row_idx, 1, QTableWidgetItem(str(item['last_seen_draw'])))
            self.gap_table.setItem(row_idx, 2, QTableWidgetItem(str(item['gap'])))

    def analyze_pairs_2(self):
        top_n = self.pair2_spinbox.value()
        data = self.data_manager.get_pair_frequencies(pair_size=2, top_n=top_n)
        self.pair2_table.setRowCount(len(data))
        for row_idx, item in enumerate(data):
            self.pair2_table.setItem(row_idx, 0, QTableWidgetItem(item['pair']))
            self.pair2_table.setItem(row_idx, 1, QTableWidgetItem(str(item['count'])))

    def analyze_pairs_3(self):
        top_n = self.pair3_spinbox.value()
        data = self.data_manager.get_pair_frequencies(pair_size=3, top_n=top_n)
        self.pair3_table.setRowCount(len(data))
        for row_idx, item in enumerate(data):
            self.pair3_table.setItem(row_idx, 0, QTableWidgetItem(item['pair']))
            self.pair3_table.setItem(row_idx, 1, QTableWidgetItem(str(item['count'])))

    def plot_frequency_chart(self):
        freq_data_for_plot = self.data_manager.get_number_frequency(include_bonus=True)
        x_data = [item['number'] for item in freq_data_for_plot]
        y_data = [item['count'] for item in freq_data_for_plot]
        
        self.canvas.plot_bar(x_data, y_data, "번호별 총 출현 횟수 (보너스 포함)", "로또 번호", "출현 횟수")
