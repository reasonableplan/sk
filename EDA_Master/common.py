# common.py
import sys
import platform
import pandas as pd
from PyQt6.QtCore import Qt, QAbstractTableModel, QThread, pyqtSignal
from PyQt6.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# --- [Worker Thread with Progress] ---
class Worker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)  # 진행률 시그널 추가
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
    
    def update_progress(self, value):
        """진행률 업데이트 (0-100)"""
        self.progress.emit(value)

# --- [Enhanced Pandas Model with Sorting] ---
class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super(PandasModel, self).__init__()
        self._data = data
        self._sort_column = None
        self._sort_order = Qt.SortOrder.AscendingOrder
    
    def rowCount(self, parent=None):
        return self._data.shape[0]
    
    def columnCount(self, parent=None):
        return self._data.shape[1]
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                val = self._data.iloc[index.row(), index.column()]
                if isinstance(val, float): 
                    return f"{val:.4f}"
                return str(val)
        return None
    
    def headerData(self, col, orientation, role):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.columns[col])
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return str(self._data.index[col])
        return None
    
    def sort(self, column, order=Qt.SortOrder.AscendingOrder):
        """컬럼 정렬 기능"""
        self.layoutAboutToBeChanged.emit()
        col_name = self._data.columns[column]
        ascending = (order == Qt.SortOrder.AscendingOrder)
        self._data = self._data.sort_values(by=col_name, ascending=ascending)
        self._sort_column = column
        self._sort_order = order
        self.layoutChanged.emit()

# --- [Optimized MplCanvas with Static Font Config] ---
class MplCanvas(FigureCanvas):
    _font_configured = False  # 클래스 변수로 한 번만 설정
    
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # 폰트 설정을 한 번만 실행
        if not MplCanvas._font_configured:
            system_name = platform.system()
            if system_name == 'Windows':
                plt.rcParams['font.family'] = 'Malgun Gothic'
            elif system_name == 'Darwin':
                plt.rcParams['font.family'] = 'AppleGothic'
            else:
                plt.rcParams['font.family'] = 'NanumGothic'
            plt.rcParams['axes.unicode_minus'] = False
            MplCanvas._font_configured = True
        
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        fig.tight_layout()
        super(MplCanvas, self).__init__(fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.updateGeometry()
