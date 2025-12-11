from PyQt6.QtWidgets import QApplication

def apply_styles(app: QApplication):
    dark_stylesheet = """
    /* Global Styles */
    QWidget {
        background-color: #2b2b2b;
        color: #f0f0f0;
        font-family: 'Segoe UI', 'Malgun Gothic', sans-serif;
        font-size: 14px;
    }
    
    /* Group Box */
    QGroupBox {
        border: 1px solid #555;
        border-radius: 6px;
        margin-top: 10px;
        font-weight: bold;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }

    /* Labels */
    QLabel {
        color: #e0e0e0;
    }
    QLabel[heading="true"] {
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
        margin-bottom: 10px;
    }

    /* Input Fields */
    QLineEdit, QComboBox, QSpinBox, QDateEdit, QDoubleSpinBox {
        background-color: #3b3b3b;
        border: 1px solid #555;
        border-radius: 4px;
        padding: 6px;
        color: #ffffff;
        selection-background-color: #3daee9;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
        border: 1px solid #3daee9;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left-width: 1px;
        border-left-color: #555;
        border-left-style: solid;
    }

    /* Buttons */
    QPushButton {
        background-color: #3daee9;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 8px 16px;
        font-weight: bold;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #3182ce;
    }
    QPushButton:pressed {
        background-color: #2b6cb0;
    }
    QPushButton:disabled {
        background-color: #555555;
        color: #888888;
    }

    /* Tables */
    QTableWidget {
        background-color: #2b2b2b;
        alternate-background-color: #333333;
        gridline-color: #444;
        border: 1px solid #444;
        selection-background-color: #3daee9;
        selection-color: white;
    }
    QHeaderView::section {
        background-color: #1e1e1e;
        color: #ffffff;
        border: 1px solid #444;
        padding: 6px;
        font-weight: bold;
    }
    
    /* List Widget */
    QListWidget {
        background-color: #2b2b2b;
        border: 1px solid #444;
        border-radius: 4px;
    }
    QListWidget::item {
        padding: 5px;
    }
    QListWidget::item:selected {
        background-color: #3daee9;
        color: white;
    }

    /* Tab Widget */
    QTabWidget::pane {
        border: 1px solid #444;
        top: -1px;
        background-color: #2b2b2b;
    }
    QTabBar::tab {
        background: #1e1e1e;
        color: #aaaaaa;
        padding: 10px 15px;
        border: 1px solid #444;
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background: #2b2b2b;
        color: white;
        font-weight: bold;
        border-bottom: 2px solid #3daee9;
    }
    QTabBar::tab:hover {
        background: #333333;
    }

    /* Scrollbars */
    QScrollBar:vertical {
        border: none;
        background: #2b2b2b;
        width: 10px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background: #555;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        border: none;
        background: #2b2b2b;
        height: 10px;
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:horizontal {
        background: #555;
        min-width: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    """
    app.setStyleSheet(dark_stylesheet)
