from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # 다크 테마 설정을 위해 facecolor 지정
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_facecolor('#2b2b2b') # Figure 배경색
        self.ax.set_facecolor('#2b2b2b') # Axes 배경색
        
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax.tick_params(axis='x', labelsize=8, colors='white') # x축 라벨 크기 및 색상
        self.ax.tick_params(axis='y', colors='white')
        self.ax.spines['bottom'].set_color('#888')
        self.ax.spines['top'].set_color('#888') 
        self.ax.spines['left'].set_color('#888')
        self.ax.spines['right'].set_color('#888')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.title.set_color('white')

        self.fig.tight_layout() # 여백 자동 조절

    def clear(self):
        self.ax.clear()
        self.draw()

    def plot_bar(self, x_data, y_data, title, x_label, y_label):
        self.ax.clear()
        self.ax.bar(x_data, y_data)
        self.ax.set_title(title)
        self.ax.set_xlabel(x_label)
        self.ax.set_ylabel(y_label)
        self.draw_idle() # UI가 멈추지 않도록 다시 그리기
