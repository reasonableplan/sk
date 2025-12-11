import sys
import os
import json
import logging
import pandas as pd
import seaborn as sns
from io import StringIO
from dotenv import load_dotenv
from datetime import datetime

# PyQt6 모듈
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QPushButton, QLabel, QFrame, 
                             QStackedWidget, QFileDialog, QTextEdit, QMessageBox,
                             QListWidget, QScrollArea, QTabWidget, QTableView, 
                             QHeaderView, QAbstractItemView, QProgressDialog,
                             QListWidgetItem, QComboBox, QCheckBox, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont

# ML & 전처리
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder, MinMaxScaler, RobustScaler, MaxAbsScaler
import google.generativeai as genai

# --- [모듈 임포트] ---
from common import Worker, PandasModel, MplCanvas
from ui_pages import UIPages
from data_processor import DataProcessor
from config_manager import ConfigManager
import ai_engine
import ml_engine

# --- [로깅 설정] ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('eda_master.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- [API 키 설정 및 검증] ---
basedir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(basedir, '.env')

# .env 파일 존재 여부 확인
if not os.path.exists(env_path):
    logger.warning(f".env file not found at {env_path}")
    logger.info("Please create a .env file based on .env.example template")
    GEMINI_API_KEY = None
else:
    load_dotenv(env_path)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# API 키 검증 및 설정
API_CONFIGURED = False
if GEMINI_API_KEY:
    # API 키 형식 검증 (기본적인 체크)
    if len(GEMINI_API_KEY) < 20 or GEMINI_API_KEY == "your_gemini_api_key_here":
        logger.error("Invalid GEMINI_API_KEY format. Please check your .env file.")
        logger.info("Get your API key from: https://makersuite.google.com/app/apikey")
    else:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            API_CONFIGURED = True
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            logger.info("Please verify your API key is valid")
else:
    logger.warning("GEMINI_API_KEY not found in environment variables")
    logger.info("AI features will be disabled. Please configure .env file to enable AI features.")

class DashboardApp(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.info("Initializing EDA Master Application")
        
        # 설정 관리자 초기화
        self.config = ConfigManager()
        
        # 히스토리 관리
        self.history = []      
        self.max_history = 10
        self.last_ai_insight = "이전 AI 분석 결과가 없습니다."
        
        # 데이터 프로세서
        self.processor = DataProcessor()

        # 초기 샘플 데이터
        self.df = pd.DataFrame({
            'Age': [22, 38, 26, 35, 35, 54, 2, 27, 14, 4, None, 38, 22, 26, 35],
            'Fare': [7.25, 71.28, 7.92, 53.1, 8.05, 51.86, 21.07, 11.13, 30.07, 16.7, 7.25, None, 7.92, 53.1, 8.05],
            'Class': ['Third', 'First', 'Third', 'First', 'Third', 'First', 'Third', 'Third', 'Second', 'Third', 'Third', 'First', 'Third', 'First', 'Third'],
            'Who': ['man', 'woman', 'woman', 'woman', 'man', 'man', 'child', 'child', 'child', 'child', 'man', 'woman', 'woman', 'woman', 'man'],
            'Embarked': ['S', 'C', 'S', 'S', 'S', 'Q', 'S', 'S', 'S', 'S', 'C', 'S', 'S', 'S', 'S'],
            'Survived': [0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0],
            'Date': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06', '2023-01-07', '2023-01-08', '2023-01-09', '2023-01-10', '2023-01-11', '2023-01-12', '2023-01-13', '2023-01-14', '2023-01-15'])
        })

        self.init_ui()
        self.update_dashboard()
        self.update_col_list()
        
        # 설정에서 윈도우 크기 복원
        if self.config.get('window.maximized', True):
            self.showMaximized()
        else:
            width = self.config.get('window.width', 1200)
            height = self.config.get('window.height', 800)
            self.resize(width, height) 

    def save_state(self, description="Action"):
        if self.df is not None:
            if len(self.history) >= self.max_history:
                self.history.pop(0)
            self.history.append((self.df.copy(deep=True), description))
            if hasattr(self, 'btn_undo'):
                self.btn_undo.setEnabled(True)
                self.btn_undo.setText(f"↩ Undo ({len(self.history)})")

    def undo_last_action(self):
        if not self.history:
            QMessageBox.information(self, "Info", "No more actions to undo.")
            return
        prev_df, desc = self.history.pop()
        self.df = prev_df
        self.update_dashboard()
        self.update_data_tables()
        self.process_log.append(f"↩ Undone: Reverted before '{desc}'")
        if hasattr(self, 'btn_undo'):
            self.btn_undo.setText(f"↩ Undo ({len(self.history)})")
            if not self.history:
                self.btn_undo.setEnabled(False)
                self.btn_undo.setText("↩ Undo")

    def highlight_checked_item(self, item):
        if item.checkState() == Qt.CheckState.Checked:
            # 체크됨: 배경 민트색, 글씨 진하게
            item.setBackground(QBrush(QColor("#d1f2eb"))) 
            item.setForeground(QBrush(QColor("#000000")))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        else:
            # 해제됨: 배경 흰색, 글씨 회색
            item.setBackground(QBrush(QColor("#ffffff")))
            item.setForeground(QBrush(QColor("#7f8c8d")))
            font = item.font()
            font.setBold(False)
            item.setFont(font)

    # [추가] 텍스트 클릭 시 체크박스 토글 기능
    def on_list_item_clicked(self, item):
        # 현재 상태를 반대로 토글 (체크 <-> 해제)
        if item.checkState() == Qt.CheckState.Checked:
            item.setCheckState(Qt.CheckState.Unchecked)
        else:
            item.setCheckState(Qt.CheckState.Checked)

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_widget.setLayout(main_layout)

        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e0e0e0;")
        sidebar_layout = QVBoxLayout(sidebar)
        
        lbl_title = QLabel("EDA Master")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 20px; padding: 20px; color: #6c5ce7;")
        sidebar_layout.addWidget(lbl_title)

        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_data = QPushButton("Data View")
        self.btn_assist = QPushButton("AI Analyst")
        self.btn_ai_pre = QPushButton("AI Data Engineer") 
        self.btn_preprocess = QPushButton("Preprocessing") 
        self.btn_model = QPushButton("ML Modeling")     
        
        self.btn_style_normal = """
            QPushButton { background-color: transparent; text-align: left; padding: 12px 20px; border: none; font-size: 14px; color: #555; }
            QPushButton:hover { background-color: #f0f2f5; color: #000; font-weight: bold; border-left: 4px solid #6c5ce7; }
        """
        self.btn_style_active = """
            QPushButton { background-color: #e3e6f0; text-align: left; padding: 12px 20px; border: none; font-size: 14px; color: #000; font-weight: bold; border-left: 4px solid #6c5ce7; }
        """
        
        self.sidebar_buttons = [self.btn_dashboard, self.btn_data, self.btn_assist, self.btn_ai_pre, self.btn_preprocess, self.btn_model]
        
        for i, btn in enumerate(self.sidebar_buttons):
            btn.setStyleSheet(self.btn_style_normal)
            sidebar_layout.addWidget(btn)
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))

        sidebar_layout.addStretch()
        
        self.btn_undo = QPushButton("↩ Undo")
        self.btn_undo.setStyleSheet("background-color: #fab1a0; color: #d63031; font-weight: bold; border-radius: 5px; margin: 10px 20px;")
        self.btn_undo.clicked.connect(self.undo_last_action)
        self.btn_undo.setEnabled(False) 
        sidebar_layout.addWidget(self.btn_undo)

        export_btn = QPushButton("Export Data")
        export_btn.setStyleSheet("background-color: #00b894; color: white; font-weight: bold; border-radius: 5px; margin: 0px 20px 10px 20px;")
        export_btn.clicked.connect(self.export_data)
        sidebar_layout.addWidget(export_btn)

        load_btn = QPushButton("Load Data")
        load_btn.setStyleSheet("background-color: #6c5ce7; color: white; font-weight: bold; border-radius: 5px; margin: 0px 20px 20px 20px;")
        load_btn.clicked.connect(self.load_file)
        sidebar_layout.addWidget(load_btn)
        
        main_layout.addWidget(sidebar)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        self.page_dashboard = QWidget(); UIPages.setup_dashboard_ui(self, self.page_dashboard)
        self.stacked_widget.addWidget(self.page_dashboard)
        self.page_data_view = QWidget(); UIPages.setup_data_view_ui(self, self.page_data_view)
        self.stacked_widget.addWidget(self.page_data_view)
        self.page_ai_assist = QWidget(); UIPages.setup_ai_assist_ui(self, self.page_ai_assist)
        self.stacked_widget.addWidget(self.page_ai_assist)
        self.page_ai_pre = QWidget(); UIPages.setup_ai_preprocessing_ui(self, self.page_ai_pre)
        self.stacked_widget.addWidget(self.page_ai_pre)
        self.page_preprocess = QWidget(); UIPages.setup_preprocessing_ui(self, self.page_preprocess)
        self.stacked_widget.addWidget(self.page_preprocess)
        self.page_ml = QWidget(); UIPages.setup_ml_ui(self, self.page_ml)
        self.stacked_widget.addWidget(self.page_ml)
        
        self.switch_page(0)

    def create_card(self, title, value, color_border=None):
        card = QFrame()
        card.setObjectName("CardFrame")
        style = "QFrame#CardFrame { background-color: white; border-radius: 12px; border: 1px solid #e0e0e0; padding: 10px; }"
        if color_border: style += f"QFrame#CardFrame {{ border-top: 5px solid {color_border}; }}"
        card.setStyleSheet(style)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; color: #555;")
        layout.addWidget(title_lbl)
        val_lbl = QLabel(value)
        val_lbl.setObjectName("value_label")
        val_lbl.setStyleSheet("font-size: 26px; font-weight: bold; color: #222; margin-top: 5px;")
        layout.addWidget(val_lbl)
        layout.addStretch()
        return card

    def switch_page(self, idx):
        self.stacked_widget.setCurrentIndex(idx)
        for i, btn in enumerate(self.sidebar_buttons):
            if i == idx:
                btn.setStyleSheet(self.btn_style_active)
            else:
                btn.setStyleSheet(self.btn_style_normal)

    def update_ml_target_list(self):
        self.ml_target_combo.clear()
        if self.df is not None:
            numeric_cols = self.df.select_dtypes(include=['number']).columns
            self.ml_target_combo.addItems(numeric_cols)

    def toggle_all_columns(self, state):
        if state == 2:
            self.col_combo.selectAll()
        else:
            self.col_combo.clearSelection()

    def show_loading(self, message="Processing..."):
        self.progress = QProgressDialog(message, None, 0, 0, self)
        self.progress.setWindowTitle("Please Wait")
        self.progress.setWindowModality(Qt.WindowModality.WindowModal) 
        self.progress.setCancelButton(None) 
        self.progress.show()

    def hide_loading(self):
        if hasattr(self, 'progress'):
            self.progress.cancel()

    def load_file(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "A task is already running.")
            return
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Data File", "", "Data Files (*.csv *.xlsx *.xls);;All (*)")
        if not file_name: return
        self.show_loading("Loading Data File...")
        def load_task(fname):
            if fname.lower().endswith('.csv'): return pd.read_csv(fname)
            else: return pd.read_excel(fname)
        self.worker = Worker(load_task, file_name)
        self.worker.finished.connect(lambda df: self.on_load_finished(df, file_name))
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_load_finished(self, df, fname):
        self.hide_loading()
        self.df = df
        self.header_label.setText(f"Data Overview - {fname.split('/')[-1]}")
        self.update_dashboard()
        self.update_col_list()
        self.update_ml_target_list()
        self.ai_text_area.clear()
        self.ai_plots_tabs.clear()
        self.action_list_widget.clear()
        self.process_log.append(f"Loaded: {fname}")
        QMessageBox.information(self, "Success", "Data Loaded Successfully!")

    def on_worker_error(self, err_msg):
        self.hide_loading()
        QMessageBox.critical(self, "Error", f"An error occurred:\n{err_msg}")

    def export_data(self):
        if self.df is None or self.df.empty:
            QMessageBox.warning(self, "Warning", "No data to export.")
            return
        file_name, filter_str = QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv);;Excel Files (*.xlsx)")
        if file_name:
            try:
                if file_name.lower().endswith('.csv'):
                    self.df.to_csv(file_name, index=False, encoding='utf-8-sig') 
                elif file_name.lower().endswith('.xlsx'):
                    self.df.to_excel(file_name, index=False)
                logger.info(f"Data exported to {file_name}")
                QMessageBox.information(self, "Success", f"Data saved to {file_name}")
            except Exception as e:
                logger.error(f"Failed to export data: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save:\n{str(e)}")
    
    def export_chart(self, canvas, default_name="chart"):
        """차트를 이미지 파일로 내보내기"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Chart", 
            f"{default_name}.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg)"
        )
        if file_name:
            try:
                canvas.figure.savefig(file_name, dpi=300, bbox_inches='tight')
                logger.info(f"Chart exported to {file_name}")
                QMessageBox.information(self, "Success", f"Chart saved to {file_name}")
            except Exception as e:
                logger.error(f"Failed to export chart: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save chart:\n{str(e)}")
    
    def closeEvent(self, event):
        """애플리케이션 종료 시 설정 저장"""
        # 윈도우 크기 저장
        self.config.set('window.maximized', self.isMaximized())
        if not self.isMaximized():
            self.config.set('window.width', self.width())
            self.config.set('window.height', self.height())
        self.config.save()
        logger.info("Application closed, settings saved")
        event.accept()

    def update_col_list(self):
        self.col_combo.clear()
        if self.df is not None:
            self.col_combo.addItems(self.df.columns)


    def update_dashboard(self):
        if self.df is None: return
        self.card_rows.findChild(QLabel, "value_label").setText(f"{self.df.shape[0]:,}")
        self.card_cols.findChild(QLabel, "value_label").setText(f"{self.df.shape[1]}")
        total_missing = self.df.isnull().sum().sum()
        self.card_missing.findChild(QLabel, "value_label").setText(f"{total_missing:,}")
        self.card_dups.findChild(QLabel, "value_label").setText(f"{self.df.duplicated().sum():,}")

        self.num_list_widget.clear(); self.cat_list_widget.clear()
        self.update_col_list() 

        numeric_cols = self.df.select_dtypes(include=['number']).columns
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns

        if len(numeric_cols) > 0:
            for col in numeric_cols: self.num_list_widget.addItem(QListWidgetItem(col))
            if self.num_list_widget.count() > 0:
                self.num_list_widget.setCurrentRow(0) 
                self.on_numeric_col_selected(self.num_list_widget.currentItem())
        else:
            self.canvas_hist.axes.clear(); self.canvas_hist.draw()
            self.canvas_box.axes.clear(); self.canvas_box.draw()

        if len(cat_cols) > 0:
            for col in cat_cols: self.cat_list_widget.addItem(QListWidgetItem(col))
            if self.cat_list_widget.count() > 0:
                self.cat_list_widget.setCurrentRow(0) 
                self.on_categorical_col_selected(self.cat_list_widget.currentItem())
        else:
            self.canvas_bar.axes.clear(); self.canvas_bar.draw()
            self.canvas_pie.axes.clear(); self.canvas_pie.draw()

        self.plot_correlation()
        self.update_data_tables()

    def update_data_tables(self):
        self.model_raw = PandasModel(self.df)
        self.view_raw.setModel(self.model_raw)
        self.view_raw.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        try:
            stats_df = self.df.describe(include='all').T.fillna('')
            self.model_stats = PandasModel(stats_df)
            self.view_stats.setModel(self.model_stats)
            self.view_stats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

    def get_plot_data(self, data, threshold=10000):
        if isinstance(data, pd.Series) or isinstance(data, pd.DataFrame):
            if len(data) > threshold:
                return data.sample(n=threshold, random_state=42), True
        return data, False

    def on_numeric_col_selected(self, item):
        if not item: return
        col_name = item.text()
        if self.df is None or col_name not in self.df.columns or not pd.api.types.is_numeric_dtype(self.df[col_name]): return

        plot_data, is_sampled = self.get_plot_data(self.df[col_name].dropna(), threshold=10000)
        suffix = " (Sampled 10k)" if is_sampled else ""

        self.canvas_hist.axes.clear()
        sns.histplot(plot_data, kde=True, bins='auto', ax=self.canvas_hist.axes, color='#6c5ce7', edgecolor='white', linewidth=0.5)
        self.canvas_hist.axes.set_title(f"Distribution: {col_name}{suffix}", fontsize=10, fontweight='bold')
        self.canvas_hist.axes.grid(True, linestyle='--', alpha=0.5)
        self.canvas_hist.draw()

        self.canvas_box.axes.clear()
        sns.boxplot(x=plot_data, ax=self.canvas_box.axes, color='#fab1a0') 
        self.canvas_box.axes.set_title(f"Boxplot: {col_name}{suffix}", fontsize=10, fontweight='bold')
        self.canvas_box.axes.grid(True, axis='x', linestyle='--', alpha=0.5)
        self.canvas_box.draw()

    def on_categorical_col_selected(self, item):
        if not item: return
        col_name = item.text()
        if self.df is None or col_name not in self.df.columns: return

        counts = self.df[col_name].value_counts().head(10)
        self.canvas_bar.axes.clear()
        sns.barplot(x=counts.values, y=counts.index.astype(str), ax=self.canvas_bar.axes, palette="viridis")
        self.canvas_bar.axes.set_title(f"Frequency: {col_name}", fontsize=10, fontweight='bold')
        self.canvas_bar.figure.tight_layout()
        self.canvas_bar.draw()

        self.canvas_pie.axes.clear()
        if counts.sum() > 0: 
            self.canvas_pie.axes.pie(counts, labels=None, autopct='%1.1f%%', startangle=90, pctdistance=0.85)
            self.canvas_pie.axes.legend(counts.index, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)
        self.canvas_pie.axes.set_title(f"Proportion: {col_name}", fontsize=10, fontweight='bold')
        self.canvas_pie.draw()

    def plot_correlation(self):
        self.canvas_corr.figure.clear()
        self.canvas_corr.figure.patch.set_facecolor('white')
        numeric_df = self.df.select_dtypes(include=['number'])
        
        if numeric_df.shape[1] > 1:
            ax = self.canvas_corr.figure.add_subplot(111)
            calc_df, is_sampled = self.get_plot_data(numeric_df, threshold=20000) 
            corr = calc_df.corr()
            sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm', ax=ax, cbar=False, square=False)
            ax.set_title(f"Numeric Feature Correlation", fontweight='bold', fontsize=14)
            ax.tick_params(axis='x', labelrotation=45)
        self.canvas_corr.figure.tight_layout()
        self.canvas_corr.draw()

    def update_ui_for_preprocessing_action(self, index=None):
        """스케일링 옵션이 선택되었을 때만 Scaler Type 선택 UI를 표시"""
        if hasattr(self, 'preprocess_combo') and hasattr(self, 'lbl_scaler_type') and hasattr(self, 'scaler_combo'):
            action_text = self.preprocess_combo.currentText()
            is_scaling = "스케일링" in action_text
            self.lbl_scaler_type.setVisible(is_scaling)
            self.scaler_combo.setVisible(is_scaling)
    
    def execute_preprocessing_task(self):
        if self.df is None or self.df.empty:
            QMessageBox.warning(self, "Warning", "No data loaded.")
            return

        action_text = self.preprocess_combo.currentText()
        selected_items = self.col_combo.selectedItems()
        target_cols = [item.text() for item in selected_items]
        
        if not target_cols and "제거" not in action_text:
             if "결측치 포함" not in action_text and "중복 데이터" not in action_text and "낮은 분산" not in action_text:
                QMessageBox.warning(self, "Warning", "Please select columns.")
                return

        self.save_state(f"Manual Preprocessing: {action_text}")
        self.process_log.append(f"\n>>> Running: '{action_text}'")
        
        df_original_state = self.df.copy(deep=True) 

        try:
            if "결측치 처리: 평균" in action_text:
                for col in target_cols:
                    if pd.api.types.is_numeric_dtype(self.df[col]): self.df[col].fillna(self.df[col].mean(), inplace=True)
            elif "결측치 처리: 중앙값" in action_text:
                for col in target_cols:
                    if pd.api.types.is_numeric_dtype(self.df[col]): self.df[col].fillna(self.df[col].median(), inplace=True)
            elif "결측치 처리: 최빈값" in action_text:
                for col in target_cols:
                    if not self.df[col].empty: self.df[col].fillna(self.df[col].mode()[0], inplace=True)
            elif "결측치 포함 행 제거" in action_text:
                if target_cols: self.df.dropna(subset=target_cols, inplace=True)
                else: self.df.dropna(inplace=True)
            elif "결측치 포함 열 제거" in action_text:
                if target_cols: self.df.drop(columns=target_cols, inplace=True)
                else: self.df.dropna(axis=1, how='all', inplace=True)
            elif "IQR 방식으로 제거" in action_text:
                for col in target_cols:
                    if pd.api.types.is_numeric_dtype(self.df[col]):
                        Q1 = self.df[col].quantile(0.25); Q3 = self.df[col].quantile(0.75); IQR = Q3 - Q1
                        self.df = self.df[~((self.df[col] < (Q1 - 1.5 * IQR)) | (self.df[col] > (Q3 + 1.5 * IQR)))]
            elif "IQR 방식으로 상/하한" in action_text:
                for col in target_cols:
                    if pd.api.types.is_numeric_dtype(self.df[col]):
                        Q1 = self.df[col].quantile(0.25); Q3 = self.df[col].quantile(0.75); IQR = Q3 - Q1
                        self.df[col] = self.df[col].clip(lower=Q1 - 1.5 * IQR, upper=Q3 + 1.5 * IQR)
            elif "레이블 인코딩" in action_text:
                for col in target_cols:
                    self.df[col] = LabelEncoder().fit_transform(self.df[col].astype(str))
            elif "원-핫 인코딩" in action_text:
                self.df = pd.get_dummies(self.df, columns=target_cols, prefix=target_cols, dtype=int)
            elif "제곱" in action_text:
                for col in target_cols:
                     if pd.api.types.is_numeric_dtype(self.df[col]): self.df[f"{col}_squared"] = self.df[col] ** 2
            elif "시계열" in action_text:
                for col in target_cols:
                    self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
                    if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                        self.df[f"{col}_year"] = self.df[col].dt.year
                        self.df[f"{col}_month"] = self.df[col].dt.month
                        self.df[f"{col}_day"] = self.df[col].dt.day
            elif "스케일링" in action_text:
                scaler_type = self.scaler_combo.currentText()
                scaler = None
                if "MinMax" in scaler_type: scaler = MinMaxScaler()
                elif "Standard" in scaler_type: scaler = StandardScaler()
                elif "Robust" in scaler_type: scaler = RobustScaler()
                elif "MaxAbs" in scaler_type: scaler = MaxAbsScaler()
                num_cols = [c for c in target_cols if pd.api.types.is_numeric_dtype(self.df[c])]
                if scaler and num_cols:
                    self.df[num_cols] = scaler.fit_transform(self.df[num_cols].fillna(0))
            elif "숫자로" in action_text:
                for col in target_cols: self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            elif "텍스트" in action_text:
                for col in target_cols: self.df[col] = self.df[col].astype(str).str.strip().str.lower()
            elif "중복 데이터" in action_text:
                if target_cols: self.df.drop_duplicates(subset=target_cols, inplace=True)
                else: self.df.drop_duplicates(inplace=True)
            elif "낮은 분산" in action_text:
                cols = [c for c in self.df.columns if self.df[c].nunique() <= 1]
                self.df.drop(columns=cols, inplace=True)
            elif "음수값" in action_text:
                for col in target_cols:
                    if pd.api.types.is_numeric_dtype(self.df[col]):
                        cnt = (self.df[col] < 0).sum()
                        self.process_log.append(f"Column {col}: {cnt} negative values.")

            self.update_dashboard()
            self.update_data_tables()
            self.process_log.append("Processing finished.")

        except Exception as e:
            self.df = df_original_state
            self.process_log.append(f"Error: {e}")
            QMessageBox.critical(self, "Error", f"Error during preprocessing: {e}")

    def start_ai_preprocessing_scan(self):
        # API 키 확인
        if not API_CONFIGURED:
            QMessageBox.warning(
                self, 
                "API Not Configured", 
                "Gemini API is not configured.\n\n"
                "Please set up your API key in the .env file.\n"
                "See .env.example for instructions."
            )
            return
        
        if hasattr(self, 'worker') and self.worker.isRunning():
            QMessageBox.warning(self, "Busy", "Working...")
            return

        if self.df is None or self.df.empty: return
        self.show_loading("AI Scanning (with previous insights)...")
        
        df_for_ai = self.df.copy(deep=True)
        buf = StringIO(); df_for_ai.info(buf=buf)
        
        # [추가] 수치형 데이터의 왜도(Skewness) 계산
        try:
            skew_info = df_for_ai.select_dtypes(include='number').skew().to_string()
        except:
            skew_info = "왜도 계산 불가 (수치형 데이터 부족)"

        # [수정] 인자 5개 전달 (기존 3개 + 왜도 + 이전 분석)
        self.worker = Worker(
            ai_engine.ai_preprocess_task, 
            buf.getvalue(),                                         # info
            df_for_ai.describe(include='all').round(2).to_string(), # describe
            df_for_ai.head().to_string(),                           # head
            skew_info,                                              # [New] 왜도 정보
            self.last_ai_insight                                    # [New] AI Analyst의 분석글
        )
        self.worker.finished.connect(self.on_ai_scan_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_ai_scan_finished(self, res):
        self.hide_loading()
        try:
            data = json.loads(res)
            self.diagnosis_text.setText(data.get("report", ""))
            self.action_list_widget.clear()
            
            # 신호 연결을 잠시 끊어야 대량 추가 시 성능 저하 방지
            self.action_list_widget.itemChanged.disconnect(self.highlight_checked_item)
            
            for act in data.get("actions", []):
                item = QListWidgetItem(f"[{act['action']}] {act['column']}\n └ {act.get('reason', '')}")
                item.setData(Qt.ItemDataRole.UserRole, act)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                
                # [수정됨] 기본값 해제 (Unchecked)
                item.setCheckState(Qt.CheckState.Unchecked)
                
                # 초기 스타일 적용 (회색/비활성 느낌)
                self.highlight_checked_item(item)
                
                self.action_list_widget.addItem(item)
            
            # 신호 다시 연결
            self.action_list_widget.itemChanged.connect(self.highlight_checked_item)
                
        except Exception as e: QMessageBox.warning(self, "Error", str(e))

    def execute_ai_actions(self):
        # 1. 체크된 항목 가져오기
        checked_items = []
        for i in range(self.action_list_widget.count()):
            item = self.action_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_items.append(item)

        if not checked_items:
            QMessageBox.warning(self, "알림", "선택된 작업이 없습니다.")
            return

        # 2. 사용자 확인
        reply = QMessageBox.question(self, '작업 확인', 
                                     f"선택한 {len(checked_items)}개의 작업을 적용하시겠습니까?\n(데이터가 변경됩니다.)", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        # 3. 상태 저장 (Undo용)
        self.save_state("AI Automated Actions")

        applied_count = 0
        
        try:
            for item in checked_items:
                act = item.data(Qt.ItemDataRole.UserRole)
                col_name = act.get('column', '').strip()
                action_type = act.get('action', '').strip()

                # 컬럼 존재 여부 확인 (DataFrame 전체 대상이 아닐 경우)
                if col_name != 'DataFrame' and col_name not in self.df.columns:
                    continue

                # --- [실제 데이터 처리 로직] ---
                if action_type == "drop_column_all_nan":
                    self.df.drop(columns=[col_name], inplace=True)
                    applied_count += 1
                elif action_type == "drop_rows_any_nan":
                    initial_rows = self.df.shape[0]
                    if col_name == 'DataFrame':
                        self.df.dropna(inplace=True)
                    else:
                        self.df.dropna(subset=[col_name], inplace=True)
                    if self.df.shape[0] < initial_rows: applied_count += 1
                elif action_type == "fill_mean":
                    if pd.api.types.is_numeric_dtype(self.df[col_name]):
                        self.df[col_name].fillna(self.df[col_name].mean(), inplace=True)
                        applied_count += 1
                elif action_type == "fill_median":
                    if pd.api.types.is_numeric_dtype(self.df[col_name]):
                        self.df[col_name].fillna(self.df[col_name].median(), inplace=True)
                        applied_count += 1
                elif action_type == "fill_mode":
                    if not self.df[col_name].empty:
                        self.df[col_name].fillna(self.df[col_name].mode()[0], inplace=True)
                        applied_count += 1
                elif action_type == "remove_outliers_iqr":
                    if pd.api.types.is_numeric_dtype(self.df[col_name]):
                        Q1 = self.df[col_name].quantile(0.25)
                        Q3 = self.df[col_name].quantile(0.75)
                        IQR = Q3 - Q1
                        self.df = self.df[~((self.df[col_name] < (Q1 - 1.5 * IQR)) | (self.df[col_name] > (Q3 + 1.5 * IQR)))]
                        applied_count += 1
                elif action_type == "cap_outliers_iqr":
                    if pd.api.types.is_numeric_dtype(self.df[col_name]):
                        Q1 = self.df[col_name].quantile(0.25)
                        Q3 = self.df[col_name].quantile(0.75)
                        IQR = Q3 - Q1
                        lower = Q1 - 1.5 * IQR
                        upper = Q3 + 1.5 * IQR
                        self.df[col_name] = self.df[col_name].clip(lower=lower, upper=upper)
                        applied_count += 1
                elif action_type == "label_encode":
                    le = LabelEncoder()
                    self.df[col_name] = le.fit_transform(self.df[col_name].astype(str))
                    applied_count += 1
                elif action_type == "one_hot_encode":
                    self.df = pd.get_dummies(self.df, columns=[col_name], prefix=[col_name], dtype=int)
                    applied_count += 1
                elif action_type == "convert_to_numeric":
                    self.df[col_name] = pd.to_numeric(self.df[col_name], errors='coerce')
                    applied_count += 1
                elif action_type == "strip_lower_text":
                    self.df[col_name] = self.df[col_name].astype(str).str.strip().str.lower()
                    applied_count += 1
                elif action_type == "drop_duplicates_all_cols":
                    initial_rows = self.df.shape[0]
                    self.df.drop_duplicates(inplace=True)
                    if self.df.shape[0] < initial_rows: applied_count += 1
                elif action_type == "create_squared_feature":
                    if pd.api.types.is_numeric_dtype(self.df[col_name]):
                        self.df[f"{col_name}_squared"] = self.df[col_name] ** 2
                        applied_count += 1
                elif action_type == "extract_datetime_features":
                    self.df[col_name] = pd.to_datetime(self.df[col_name], errors='coerce')
                    if pd.api.types.is_datetime64_any_dtype(self.df[col_name]):
                        self.df[f"{col_name}_year"] = self.df[col_name].dt.year
                        self.df[f"{col_name}_month"] = self.df[col_name].dt.month
                        self.df[f"{col_name}_day"] = self.df[col_name].dt.day
                        applied_count += 1

            # 4. 결과 업데이트
            self.update_dashboard()
            self.update_data_tables()
            QMessageBox.information(self, "완료", f"총 {applied_count}개의 작업이 적용되었습니다.")

        except Exception as e:
            self.undo_last_action() # 에러 발생 시 원상복구
            QMessageBox.critical(self, "오류", f"작업 적용 중 오류 발생:\n{str(e)}")

    def start_ai_analysis_thread(self):
        # API 키 확인
        if not API_CONFIGURED:
            QMessageBox.warning(
                self, 
                "API Not Configured", 
                "Gemini API is not configured.\n\n"
                "Please set up your API key in the .env file.\n"
                "See .env.example for instructions."
            )
            return
        
        if hasattr(self, 'worker') and self.worker.isRunning(): return
        if self.df is None: return
        
        self.show_loading("AI Analysing (Random 10 Samples)...")
        
        # 1. 기본 정보 추출
        buf = StringIO(); self.df.info(buf=buf)
        info_str = buf.getvalue()
        desc_str = self.df.describe(include='all').round(2).to_string()
        
        # [수정됨] 오직 무작위 10개 행만 추출
        try:
            # 데이터가 10개보다 적으면 전체 사용, 아니면 10개 랜덤 추출
            sample_n = min(10, len(self.df))
            sample_df = self.df.sample(n=sample_n, random_state=42) # random_state 고정으로 결과 재현성 확보
            
            # 인덱스 없이 값만 깔끔하게 문자열로 변환
            data_sample_str = sample_df.to_string(index=False)
        except Exception:
            # 에러 발생 시(거의 없겠지만) 그냥 앞에서 10개
            data_sample_str = self.df.head(10).to_string()
        
        # 2. 심층 정보 생성 (상관관계 + 범주형 분포)
        extra_lines = []
        try:
            num_df = self.df.select_dtypes(include='number')
            if num_df.shape[1] > 1:
                corr_matrix = num_df.corr().abs()
                mask = pd.DataFrame(True, index=corr_matrix.index, columns=corr_matrix.columns)
                for i in range(len(mask.columns)):
                    for j in range(i + 1, len(mask.columns)):
                        mask.iloc[i, j] = False
                corr_unstacked = corr_matrix.where(~mask).stack().sort_values(ascending=False)
                top_corr = corr_unstacked.head(5)
                extra_lines.append("\n[Top 5 Correlations]")
                for idx, val in top_corr.items():
                    extra_lines.append(f"{idx[0]} - {idx[1]}: {val:.2f}")
        except: pass
            
        try:
            cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                extra_lines.append("\n[Categorical Distributions (Top 3)]")
                for col in cat_cols[:5]: 
                    counts = self.df[col].value_counts(normalize=True).head(3)
                    dist_str = ", ".join([f"{k}({v:.1%})" for k, v in counts.items()])
                    extra_lines.append(f"{col}: {dist_str}")
        except: pass
            
        extra_info_str = "\n".join(extra_lines)

        # 3. AI 엔진 호출
        self.worker = Worker(ai_engine.gemini_analysis_task, 
                             info_str, 
                             data_sample_str, # 무작위 10개 데이터
                             desc_str, 
                             extra_info_str)
        
        self.worker.finished.connect(self.on_ai_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_ai_finished(self, res):
        self.hide_loading()
        try:
            data = json.loads(res)
            insight_text = data.get("insight", "")
            self.ai_text_area.setText(insight_text)
            
            # [추가] 분석 결과를 메모리에 저장 (Data Engineer가 참고하도록)
            if insight_text:
                self.last_ai_insight = insight_text
                
            self.ai_plots_tabs.clear()
            # ... (이하 그래프 그리는 코드 기존과 동일) ...
            for plot in data.get("plots", []):
                cv = MplCanvas(self)
                try:
                    x = plot['x']; y = plot.get('y')
                    if x not in self.df.columns: continue
                    ax = cv.axes
                    if plot['type'] == 'histogram' and pd.api.types.is_numeric_dtype(self.df[x]): sns.histplot(self.df[x].dropna(), kde=True, ax=ax)
                    elif plot['type'] == 'boxplot':
                        if y and y in self.df.columns: sns.boxplot(x=self.df[x], y=self.df[y], ax=ax)
                        elif pd.api.types.is_numeric_dtype(self.df[x]): sns.boxplot(x=self.df[x], ax=ax)
                    elif plot['type'] == 'scatterplot' and y and y in self.df.columns: sns.scatterplot(x=self.df[x], y=self.df[y], ax=ax)
                    elif plot['type'] == 'barplot': 
                        c = self.df[x].value_counts().head(10)
                        sns.barplot(x=c.values, y=c.index.astype(str), ax=ax)
                    ax.set_title(plot.get('title', 'Plot'))
                    cv.draw(); self.ai_plots_tabs.addTab(cv, plot.get('title', 'Plot'))
                except: pass
        except Exception as e: self.ai_text_area.setText(f"Error: {e}")

    def prepare_training(self):
        if hasattr(self, 'worker') and self.worker.isRunning(): return
        if self.df is None: return
        target = self.ml_target_combo.currentText()
        if not target or target not in self.df.columns: return

        df_ml = self.df.copy()
        X = df_ml.drop(columns=[target])
        y = df_ml[target]
        
        task = self.ml_task_combo.currentText()
        is_cls = "Classification" in task
        if "Auto" in task:
             if pd.api.types.is_object_dtype(y) or (pd.api.types.is_numeric_dtype(y) and y.nunique() < 20): is_cls = True

        params = {
            'n_estimators': int(self.hp_estimators.currentText()),
            'max_depth': int(self.hp_depth.currentText()),
            'learning_rate': float(self.hp_lr.currentText()),
            'subsample': float(self.hp_subsample.currentText()),
            'random_state': 42,
            'n_jobs': -1
        }

        self.show_loading(f"Training ({'CLS' if is_cls else 'REG'})...")
        self.worker = Worker(ml_engine.run_xgboost_pipeline, X, y, is_cls, params)
        self.worker.finished.connect(self.on_train_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.start()

    def on_train_finished(self, result):
        self.hide_loading()
        model, res, feats = result
        txt = f"Type: {res['type']}\n"
        if res['type'] == 'Classification':
            txt += f"Acc: {res['accuracy']:.4f}\n{pd.DataFrame(res['report']).T.to_string()}"
        else:
            txt += f"MSE: {res['mse']:.4f}\nR2: {res['r2']:.4f}"
        self.ml_result_text.setText(txt)
        
        self.ml_canvas.axes.clear()
        try:
            if hasattr(model, 'feature_importances_'):
                imps = pd.Series(model.feature_importances_, index=feats).nlargest(10)
                sns.barplot(x=imps.values, y=imps.index.astype(str), ax=self.ml_canvas.axes, palette='viridis')
                self.ml_canvas.axes.set_title("Top 10 Features")
        except: pass
        self.ml_canvas.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DashboardApp()
    window.show()
    sys.exit(app.exec())
