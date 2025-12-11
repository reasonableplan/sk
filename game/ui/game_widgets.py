"""
Common game UI widgets.
"""
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QSpinBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List
from .card_widget import CardWidget


class HandWidget(QWidget):
    """Widget to display a hand of cards."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setSpacing(5)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        self.card_widgets: List[CardWidget] = []
    
    def add_card(self, card, face_up: bool = True):
        """Add a card to the hand."""
        card_widget = CardWidget(card, face_up)
        self.card_widgets.append(card_widget)
        self.layout.addWidget(card_widget)
    
    def clear_hand(self):
        """Remove all cards from the hand."""
        for card_widget in self.card_widgets:
            self.layout.removeWidget(card_widget)
            card_widget.deleteLater()
        self.card_widgets = []
    
    def flip_card(self, index: int):
        """Flip a specific card."""
        if 0 <= index < len(self.card_widgets):
            self.card_widgets[index].flip()
    
    def get_card_count(self) -> int:
        """Get number of cards in hand."""
        return len(self.card_widgets)


class BettingControls(QWidget):
    """Widget for betting controls."""
    
    bet_placed = pyqtSignal(int)  # Signal emitted when bet is placed
    
    def __init__(self, min_bet: int = 10, max_bet: int = 1000, parent=None):
        super().__init__(parent)
        self.min_bet = min_bet
        self.max_bet = max_bet
        
        layout = QHBoxLayout()
        
        # Bet amount label
        self.bet_label = QLabel("Bet Amount:")
        layout.addWidget(self.bet_label)
        
        # Bet spinner
        self.bet_spinner = QSpinBox()
        self.bet_spinner.setMinimum(min_bet)
        self.bet_spinner.setMaximum(max_bet)
        self.bet_spinner.setValue(min_bet)
        self.bet_spinner.setSingleStep(10)
        self.bet_spinner.setMinimumWidth(100)
        # Fix for black text on black background
        self.bet_spinner.setStyleSheet("""
            QSpinBox {
                background-color: white; 
                color: black; 
                padding: 5px; 
                font-size: 14px; 
                font-weight: bold;
                border-radius: 4px;
            }
            QSpinBox::up-button, QSpinBox::down-button { width: 20px; }
        """)
        layout.addWidget(self.bet_spinner)
        
        # Bet button
        self.bet_button = QPushButton("Place Bet")
        self.bet_button.clicked.connect(self._on_bet_clicked)
        self.bet_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #27ae60; }
        """)
        layout.addWidget(self.bet_button)
        
        self.setLayout(layout)
    
    def _on_bet_clicked(self):
        """Handle bet button click."""
        amount = self.bet_spinner.value()
        self.bet_placed.emit(amount)
    
    def set_max_bet(self, max_bet: int):
        """Update maximum bet."""
        self.max_bet = max_bet
        self.bet_spinner.setMaximum(max_bet)
    
    def enable(self, enabled: bool):
        """Enable or disable betting controls."""
        self.bet_spinner.setEnabled(enabled)
        self.bet_button.setEnabled(enabled)


class ChipDisplay(QFrame):
    """Widget to display chip count."""
    
    def __init__(self, player_name: str = "Player", chips: int = 1000, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        
        layout = QVBoxLayout()
        
        self.name_label = QLabel(player_name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.name_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)
        
        self.chips_label = QLabel(f"💰 {chips:,}")
        self.chips_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.chips_label.font()
        font.setPointSize(14)
        self.chips_label.setFont(font)
        layout.addWidget(self.chips_label)
        
        self.setLayout(layout)
        self.chips = chips
    
    def update_chips(self, chips: int):
        """Update chip display."""
        self.chips = chips
        self.chips_label.setText(f"💰 {chips:,}")
    
    def set_name(self, name: str):
        """Update player name."""
        self.name_label.setText(name)
