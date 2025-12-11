import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QStatusBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

# 모듈 임포트
from data_manager import LottoDataManager
from styles import apply_styles
from widgets.prediction import PredictionWidget
from widgets.lookup import LookupWidget
from widgets.analysis import AnalysisWidget
from widgets.mynumbers import MyNumbersWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 로또 분석 및 예측")
        self.setGeometry(100, 100, 1200, 800)

        # 스크립트 파일이 있는 경로를 기준으로 CSV 파일 경로 설정
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, '로또.csv')
        self.data_manager = LottoDataManager(csv_path)
        self.init_ui()
        self.status_bar.showMessage("로또 데이터 로드 완료.")

    def init_ui(self):
        # 메뉴 바
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&파일')

        exit_action = QAction('종료', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 탭 위젯
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 각 위젯 인스턴스 생성
        self.prediction_widget = PredictionWidget(self.data_manager)
        self.lookup_widget = LookupWidget(self.data_manager)
        self.analysis_widget = AnalysisWidget(self.data_manager)
        # MyNumbersWidget에 PredictionWidget의 시그널 전달
        self.my_numbers_widget = MyNumbersWidget(self.data_manager, self.prediction_widget.load_numbers_to_prediction)

        self.tab_widget.addTab(self.prediction_widget, "로또 번호 예측")
        self.tab_widget.addTab(self.lookup_widget, "로또 번호 조회")
        self.tab_widget.addTab(self.analysis_widget, "로또 번호 분석")
        self.tab_widget.addTab(self.my_numbers_widget, "나의 로또 번호")

        # 상태 바
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

if __name__ == '__main__':
    # 한글 인코딩 문제 해결 (Windows 환경에서 console 출력시)
    # Qt.HighDpiScaleFactorRoundingPolicy.PassThrough is often good for ensuring crisp text on High DPI
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    
    # 스타일 적용
    apply_styles(app)
    
    # 스크립트 경로 기준 절대 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, '로또.csv')
    
    example_csv_content = """회차,날짜,1,2,3,4,5,6,보너스
1205,2025-12-27,8,15,22,23,31,40,43
1204,2025-12-20,1,10,17,25,33,39,12
1203,2025-12-13,5,11,18,24,35,42,2
1202,2025-12-06,7,9,24,27,35,36,37
1201,2025-11-29,1,2,4,16,20,32,45
1200,2025-11-22,16,24,25,30,31,32,7
1199,2025-11-15,3,13,23,33,43,44,11
1198,2025-11-08,1,5,10,15,20,25,30
1197,2025-11-01,2,12,22,32,42,45,1
1196,2025-10-25,4,8,16,24,30,38,10
1195,2025-10-18,6,14,21,28,34,41,9
1194,2025-10-11,1,7,13,19,26,37,4
1193,2025-10-04,10,20,30,35,40,45,5
1192,2025-09-27,11,12,13,14,15,16,17
1191,2025-09-20,1,2,3,4,5,6,7
"""
    # '로또.csv' 파일이 없으면 생성
    try:
        with open(csv_path, 'x', encoding='utf-8') as f:
            f.write(example_csv_content)
        print(f"'{csv_path}' 파일이 생성되었습니다. 실제 데이터를 넣어주세요.")
    except FileExistsError:
        pass # 파일이 이미 존재하면 생성하지 않음

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
