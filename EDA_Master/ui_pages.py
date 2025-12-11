from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QFrame, 
                             QTextEdit, QListWidget, QTabWidget, QTableView, QHeaderView, QAbstractItemView,
                             QListWidgetItem, QComboBox, QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt
from common import MplCanvas, PandasModel
import seaborn as sns
import pandas as pd

class UIPages:
    @staticmethod
    def setup_dashboard_ui(app, parent_widget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        scroll.setWidget(content_widget)

        parent_layout = QVBoxLayout()
        parent_layout.setContentsMargins(0,0,0,0)
        parent_layout.addWidget(scroll)
        parent_widget.setLayout(parent_layout)

        app.header_label = QLabel("Data Overview")
        app.header_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        layout.addWidget(app.header_label)

        card_layout = QHBoxLayout()
        card_layout.setSpacing(20) 
        app.card_rows = app.create_card("Total Rows", "0", "#6c5ce7")
        app.card_cols = app.create_card("Total Columns", "0")
        app.card_missing = app.create_card("Missing Values", "0")
        app.card_dups = app.create_card("Duplicates", "0", "#e74c3c")
        for card in [app.card_rows, app.card_cols, app.card_missing, app.card_dups]:
            card_layout.addWidget(card)
        layout.addLayout(card_layout)

        split_layout = QHBoxLayout()
        layout.addLayout(split_layout)

        left_frame = QFrame()
        left_frame.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #ddd;")
        left_frame.setMinimumHeight(500) 
        left_layout = QVBoxLayout(left_frame)
        split_layout.addWidget(left_frame, stretch=1)
        
        left_layout.addWidget(QLabel("<b>🔢 Numeric Analysis (Sampled if > 10k)</b>"))
        app.num_list_widget = QListWidget()
        app.num_list_widget.setMaximumHeight(100)
        app.num_list_widget.itemClicked.connect(app.on_numeric_col_selected)
        left_layout.addWidget(app.num_list_widget)
        
        app.canvas_hist = MplCanvas(app, width=4, height=3)
        app.canvas_box = MplCanvas(app, width=4, height=3)
        left_layout.addWidget(app.canvas_hist)
        left_layout.addWidget(app.canvas_box)

        right_frame = QFrame()
        right_frame.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #ddd;")
        right_frame.setMinimumHeight(500)
        right_layout = QVBoxLayout(right_frame)
        split_layout.addWidget(right_frame, stretch=1)
        
        right_layout.addWidget(QLabel("<b>🔤 Categorical Analysis</b>"))
        app.cat_list_widget = QListWidget()
        app.cat_list_widget.setMaximumHeight(100)
        app.cat_list_widget.itemClicked.connect(app.on_categorical_col_selected)
        right_layout.addWidget(app.cat_list_widget)
        
        app.canvas_bar = MplCanvas(app, width=4, height=3)
        app.canvas_pie = MplCanvas(app, width=4, height=3)
        right_layout.addWidget(app.canvas_bar)
        right_layout.addWidget(app.canvas_pie)

        layout.addWidget(QLabel("<b>🔥 Correlation Matrix (Numeric Only)</b>"))
        
        # 차트 내보내기 버튼 추가
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        app.btn_export_corr = QPushButton("📥 Export Chart")
        app.btn_export_corr.setStyleSheet("background-color: #00b894; color: white; padding: 5px 15px; border-radius: 3px; font-size: 12px;")
        if hasattr(app, 'export_chart'):
            app.btn_export_corr.clicked.connect(lambda: app.export_chart(app.canvas_corr, "correlation_matrix"))
        export_layout.addWidget(app.btn_export_corr)
        layout.addLayout(export_layout)
        
        app.chart_corr_frame = QFrame()
        app.chart_corr_frame.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #ddd;")
        corr_layout = QVBoxLayout(app.chart_corr_frame)
        
        app.canvas_corr = MplCanvas(app, width=12, height=10)
        app.canvas_corr.setMinimumHeight(700) 
        corr_layout.addWidget(app.canvas_corr)
        
        layout.addWidget(app.chart_corr_frame)
        layout.addStretch()

    @staticmethod
    def setup_data_view_ui(app, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        title = QLabel("Detailed Data View")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(title)
        app.tabs = QTabWidget()
        layout.addWidget(app.tabs)
        app.tab_raw = QWidget()
        raw_layout = QVBoxLayout(app.tab_raw)
        app.view_raw = QTableView()
        app.view_raw.setAlternatingRowColors(True)
        raw_layout.addWidget(app.view_raw)
        app.tabs.addTab(app.tab_raw, "Raw Data")
        app.tab_stats = QWidget()
        stats_layout = QVBoxLayout(app.tab_stats)
        app.view_stats = QTableView()
        app.view_stats.setAlternatingRowColors(True)
        stats_layout.addWidget(app.view_stats)
        app.tabs.addTab(app.tab_stats, "Descriptive Statistics")

    @staticmethod
    def setup_ai_assist_ui(app, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        header = QHBoxLayout()
        title = QLabel("AI Data Analyst")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333;")
        app.ai_btn = QPushButton("Run AI Analysis")
        app.ai_btn.setStyleSheet("background-color: #0984e3; color: white; padding: 10px 20px; font-weight: bold; border-radius: 5px;")
        app.ai_btn.clicked.connect(app.start_ai_analysis_thread)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(app.ai_btn)
        layout.addLayout(header)
        app.ai_text_area = QTextEdit()
        app.ai_text_area.setReadOnly(True)
        app.ai_text_area.setStyleSheet("font-size: 14px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        app.ai_text_area.setPlaceholderText("Click 'Run AI Analysis' to get insights.")
        app.ai_text_area.setMaximumHeight(150)
        layout.addWidget(app.ai_text_area)
        layout.addWidget(QLabel("AI Generated Visualizations"))
        app.ai_plots_tabs = QTabWidget()
        layout.addWidget(app.ai_plots_tabs)

    @staticmethod
    def setup_ai_preprocessing_ui(app, parent_widget):
        layout = QVBoxLayout(parent_widget)
        header = QHBoxLayout()
        app.scan_btn = QPushButton("🚀 Scan & Suggest")
        app.scan_btn.setStyleSheet("background-color: #6c5ce7; color: white; padding: 10px; font-weight: bold;")
        app.scan_btn.clicked.connect(app.start_ai_preprocessing_scan)
        header.addWidget(QLabel("AI Data Engineer")); header.addStretch(); header.addWidget(app.scan_btn)
        layout.addLayout(header)
        
        layout.addWidget(QLabel("Diagnosis Report:"))
        app.diagnosis_text = QTextEdit(); app.diagnosis_text.setMaximumHeight(100)
        layout.addWidget(app.diagnosis_text)
        
        layout.addWidget(QLabel("Suggested Actions:"))
        app.action_list_widget = QListWidget()
        app.action_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        app.action_list_widget.itemClicked.connect(app.on_list_item_clicked)
        app.action_list_widget.itemChanged.connect(app.highlight_checked_item)
        layout.addWidget(app.action_list_widget)
        app.apply_actions_btn = QPushButton("Run Selected Actions")
        app.apply_actions_btn.clicked.connect(app.execute_ai_actions)
        layout.addWidget(app.apply_actions_btn)

    @staticmethod
    def setup_preprocessing_ui(app, parent_widget):
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        title = QLabel("Advanced Data Preprocessing Tool")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px;")
        layout.addWidget(title)
        
        control_group = QFrame()
        control_group.setObjectName("ControlPanel") 
        control_group.setStyleSheet("#ControlPanel { background: white; border-radius: 10px; border: 1px solid #ddd; }")
        
        control_layout = QGridLayout(control_group)
        control_layout.setContentsMargins(20, 20, 20, 20) 
        control_layout.setSpacing(15)
        layout.addWidget(control_group)
        
        lbl_col = QLabel("<b>1. Select Columns (Target for Action):</b>")
        lbl_col.setStyleSheet("border: none; padding: 0;") 
        control_layout.addWidget(lbl_col, 0, 0)

        app.chk_select_all = QCheckBox("Select All Columns")
        app.chk_select_all.setStyleSheet("margin-left: 10px; font-weight: bold; color: #0984e3;")
        app.chk_select_all.stateChanged.connect(app.toggle_all_columns)
        control_layout.addWidget(app.chk_select_all, 0, 1)
        
        app.col_combo = QListWidget() 
        app.col_combo.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        app.col_combo.setMaximumHeight(150)
        app.col_combo.setStyleSheet("QListWidget { border: 1px solid #ccc; border-radius: 5px; padding: 5px; background-color: #fcfcfc; }")
        control_layout.addWidget(app.col_combo, 1, 0, 1, 2)
        
        lbl_act = QLabel("<b>2. Select Preprocessing Action:</b>")
        lbl_act.setStyleSheet("border: none; padding: 0;")
        control_layout.addWidget(lbl_act, 2, 0)

        app.preprocess_combo = QComboBox()
        app.preprocess_options = [
            "결측치 처리: 평균으로 채우기 (Fill Mean)",
            "결측치 처리: 중앙값으로 채우기 (Fill Median)",
            "결측치 처리: 최빈값으로 채우기 (Fill Mode)",
            "결측치 포함 행 제거 (Drop Rows with NaNs)",
            "결측치 포함 열 제거 (Drop Columns with NaNs)",
            "이상치 처리: IQR 방식으로 제거 (Remove Outliers - IQR)",
            "이상치 처리: IQR 방식으로 상/하한 적용 (Cap Outliers - IQR)",
            "인코딩: 레이블 인코딩 (Label Encoding)",
            "인코딩: 원-핫 인코딩 (One-Hot Encoding)",
            "특성 공학: 파생 변수 생성 (제곱 - Squared Feature)",
            "특성 공학: 시계열 특성 추출 (년/월/일)",
            "스케일링 적용 (Apply Scaler)",
            "데이터 타입 변환: 숫자로 (Convert to Numeric)",
            "텍스트 데이터 전처리 (공백 제거/소문자)",
            "중복 데이터 제거 (Drop Duplicates)",
            "낮은 분산 변수 제거 (Remove Low Variance Features)",
            "데이터 일관성 검사 (음수값 체크)"
        ]
        app.preprocess_combo.addItems(app.preprocess_options)
        app.preprocess_combo.setStyleSheet("QComboBox { padding: 8px; border: 1px solid #ccc; border-radius: 5px; background-color: white; }")
        app.preprocess_combo.currentIndexChanged.connect(app.update_ui_for_preprocessing_action)
        control_layout.addWidget(app.preprocess_combo, 3, 0, 1, 2)

        app.lbl_scaler_type = QLabel("<b>3. Scaler Type (for 'Scaling' action):</b>")
        app.lbl_scaler_type.setStyleSheet("border: none; padding: 0; color: #2d3436;")
        control_layout.addWidget(app.lbl_scaler_type, 4, 0)

        app.scaler_combo = QComboBox()
        app.scaler_combo.addItems(["MinMaxScaler (0~1)", "StandardScaler (Mean=0, Std=1)", "RobustScaler (Outlier Robust)", "MaxAbsScaler (-1~1)"])
        app.scaler_combo.setStyleSheet("QComboBox { padding: 8px; border: 1px solid #ccc; border-radius: 5px; background-color: white; }")
        control_layout.addWidget(app.scaler_combo, 5, 0, 1, 2)
        
        app.update_ui_for_preprocessing_action()

        app.btn_run_process = QPushButton("Apply Selected Action")
        app.btn_run_process.setCursor(Qt.CursorShape.PointingHandCursor)
        app.btn_run_process.setStyleSheet("""
            QPushButton { background-color: #6c5ce7; color: white; font-weight: bold; padding: 12px; border-radius: 5px; border: none; }
            QPushButton:hover { background-color: #5f27cd; }
        """)
        app.btn_run_process.clicked.connect(app.execute_preprocessing_task)
        control_layout.addWidget(app.btn_run_process, 6, 0, 1, 2)
        
        layout.addStretch()
        layout.addWidget(QLabel("<b>Processing Log:</b>"))
        app.process_log = QTextEdit()
        app.process_log.setReadOnly(True)
        app.process_log.setMaximumHeight(200)
        app.process_log.setStyleSheet("background-color: #2d3436; color: #dfe6e9; font-family: Consolas; padding: 10px; border-radius: 5px;")
        layout.addWidget(app.process_log)

    @staticmethod
    def setup_ml_ui(app, parent_widget):
        layout = QHBoxLayout(parent_widget) 
        layout.setContentsMargins(20, 20, 20, 20)
        left_panel = QFrame()
        left_panel.setStyleSheet("background: white; border-radius: 10px; border: 1px solid #ddd;")
        left_panel.setFixedWidth(350)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        
        left_layout.addWidget(QLabel("<b>1. Target Variable (y):</b>"))
        app.ml_target_combo = QComboBox()
        app.ml_target_combo.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 4px;")
        left_layout.addWidget(app.ml_target_combo)
        
        left_layout.addWidget(QLabel("<b>2. Model Type:</b>"))
        app.ml_task_combo = QComboBox()
        app.ml_task_combo.addItems(["Auto Detect", "Classification (분류)", "Regression (회귀)"])
        left_layout.addWidget(app.ml_task_combo)
        
        # ML 알고리즘 선택 추가
        left_layout.addWidget(QLabel("<b>3. ML Algorithm:</b>"))
        app.ml_algorithm_combo = QComboBox()
        app.ml_algorithm_combo.addItems(["XGBoost", "RandomForest", "LightGBM"])
        app.ml_algorithm_combo.setStyleSheet("padding: 5px; border: 1px solid #ccc; border-radius: 4px;")
        left_layout.addWidget(app.ml_algorithm_combo)
        
        # 교차 검증 옵션 추가
        app.ml_use_cv = QCheckBox("Use Cross-Validation (5-fold)")
        app.ml_use_cv.setStyleSheet("margin: 5px 0;")
        left_layout.addWidget(app.ml_use_cv)

        left_layout.addWidget(QLabel("<b>4. Hyperparameters:</b>"))
        form_layout = QGridLayout()
        app.hp_estimators = QComboBox(); app.hp_estimators.addItems(["100", "200", "500", "1000"])
        app.hp_depth = QComboBox(); app.hp_depth.addItems(["3", "5", "7", "9", "10"])
        app.hp_lr = QComboBox(); app.hp_lr.addItems(["0.01", "0.05", "0.1", "0.2"])
        app.hp_subsample = QComboBox(); app.hp_subsample.addItems(["0.8", "1.0", "0.6"])
        
        form_layout.addWidget(QLabel("n_estimators:"), 0, 0); form_layout.addWidget(app.hp_estimators, 0, 1)
        form_layout.addWidget(QLabel("max_depth:"), 1, 0); form_layout.addWidget(app.hp_depth, 1, 1)
        form_layout.addWidget(QLabel("learning_rate:"), 2, 0); form_layout.addWidget(app.hp_lr, 2, 1)
        form_layout.addWidget(QLabel("subsample:"), 3, 0); form_layout.addWidget(app.hp_subsample, 3, 1)
        left_layout.addLayout(form_layout)
        left_layout.addStretch()
        
        app.btn_train = QPushButton("🚀 Train Model")
        app.btn_train.setStyleSheet("QPushButton { background-color: #d63031; color: white; font-weight: bold; padding: 15px; border-radius: 5px; font-size: 14px; } QPushButton:hover { background-color: #c0392b; }")
        app.btn_train.clicked.connect(app.prepare_training)
        left_layout.addWidget(app.btn_train)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("<b>📊 Training Results:</b>"))
        app.ml_result_text = QTextEdit()
        app.ml_result_text.setReadOnly(True)
        app.ml_result_text.setMaximumHeight(200)
        app.ml_result_text.setStyleSheet("background: #2d3436; color: #00b894; font-family: Consolas; padding: 10px;")
        right_layout.addWidget(app.ml_result_text)
        right_layout.addWidget(QLabel("<b>📈 Feature Importance:</b>"))
        app.ml_canvas = MplCanvas(app, width=5, height=4)
        right_layout.addWidget(app.ml_canvas)
        layout.addWidget(left_panel); layout.addWidget(right_panel)
