from PyQt6.QtWidgets import QWidget, QMessageBox
from PyQt6.QtCore import QTimer, pyqtSignal

class PostureGuard(QWidget):
    # 휴식 완료 시그널 (체력 회복량)
    rest_finished = pyqtSignal(int)

    def __init__(self, interval_minutes=30):
        super().__init__()
        self.interval_minutes = interval_minutes
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.alert_posture)
        
        # 타이머 시작 (60초 * 분)
        # 타이머 시작 (20분 = 20 * 60 * 1000 ms)
        self.timer.start(20 * 60 * 1000)

    def alert_posture(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("거북목 경비원")
        msg.setText("허리를 펴고 스트레칭을 하세요!\n잠시 눈을 감고 휴식을 취할까요?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        ret = msg.exec()

        if ret == QMessageBox.StandardButton.Yes:
            self.rest_finished.emit(10) # 휴식하면 체력 10 회복
        else:
            self.rest_finished.emit(-5) # 무시하면 체력 5 감소 (패널티)
