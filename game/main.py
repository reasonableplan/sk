"""
Main Application Entry Point.
"""
import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, QWidget, 
                             QVBoxLayout, QPushButton, QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

# Ensure game package is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.ui.blackjack_screen import BlackjackGameWidget
from game.ui.poker_screen import PokerGameWidget


class GameSelectionWidget(QWidget):
    """Widget to select game mode."""
    
    def __init__(self, start_blackjack_callback, start_poker_callback, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("PyQt Casino")
        title.setStyleSheet("font-size: 48px; color: gold; font-weight: bold; font-family: 'Georgia';")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Choose Your Game")
        subtitle.setStyleSheet("font-size: 24px; color: white;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        bj_btn = QPushButton("♠ BLACKJACK")
        bj_btn.setFixedSize(200, 150)
        bj_btn.clicked.connect(start_blackjack_callback)
        
        poker_btn = QPushButton("♥ POKER")
        poker_btn.setFixedSize(200, 150)
        poker_btn.clicked.connect(start_poker_callback)
        
        # Common button style
        base_style = """
            QPushButton {
                color: white;
                border-radius: 15px;
                font-size: 20px;
                font-weight: bold;
                border: 2px solid #555;
            }
            QPushButton:hover { transform: scale(1.05); border: 2px solid gold; }
        """
        bj_btn.setStyleSheet(base_style + "background-color: #2c3e50;")
        poker_btn.setStyleSheet(base_style + "background-color: #c0392b;")
        
        btn_layout.addWidget(bj_btn)
        btn_layout.addWidget(poker_btn)
        
        layout.addLayout(btn_layout)
        
        # Exit button
        exit_btn = QPushButton("Exit Game")
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #aaa;
                font-size: 16px;
                border: 1px solid #555;
                padding: 10px 30px;
                border-radius: 5px;
            }
            QPushButton:hover { color: white; border-color: white; }
        """)
        exit_btn.clicked.connect(QApplication.instance().quit)
        layout.addWidget(exit_btn)
        
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Main Window Application."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("PyQt6 Casino - Advanced Integration")
        self.resize(1200, 800)
        
        # Styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
        """)
        
        # Central Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Screens
        self.menu_screen = GameSelectionWidget(self.show_blackjack, self.show_poker)
        self.stack.addWidget(self.menu_screen)
        
        self.blackjack_screen = None # Lazy load
        self.poker_screen = None # Lazy load
        
        # Add a "Back to Menu" button overlay or toolbar if needed
        # For now, we will add a back button in the game screens or a toolbar
        
        self.toolbar = self.addToolBar("Navigation")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("QToolBar { background: #333; border-bottom: 2px solid #555; }")
        
        back_action = self.toolbar.addAction("Back to Menu")
        back_action.triggered.connect(self.show_menu)
        self.toolbar.hide() # Hide initially
        
    def show_menu(self):
        """Switch to menu."""
        self.stack.setCurrentWidget(self.menu_screen)
        self.toolbar.hide()
        
    def show_blackjack(self):
        """Switch to Blackjack."""
        if not self.blackjack_screen:
            self.blackjack_screen = BlackjackGameWidget()
            self.stack.addWidget(self.blackjack_screen)
        
        self.stack.setCurrentWidget(self.blackjack_screen)
        self.toolbar.show()
        
    def show_poker(self):
        """Switch to Poker."""
        if not self.poker_screen:
            self.poker_screen = PokerGameWidget()
            self.stack.addWidget(self.poker_screen)
            
        self.stack.setCurrentWidget(self.poker_screen)
        self.toolbar.show()


def main():
    app = QApplication(sys.argv)
    
    # Global Font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
