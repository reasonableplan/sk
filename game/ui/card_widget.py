"""
Card widget for displaying playing cards.
"""
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QLinearGradient
from typing import Optional


class CardWidget(QLabel):
    """Widget to display a playing card."""
    
    def __init__(self, card=None, face_up: bool = True, parent=None):
        """
        Initialize card widget.
        
        Args:
            card: Card object to display
            face_up: Whether to show card face or back
            parent: Parent widget
        """
        super().__init__(parent)
        self.card = card
        self.face_up = face_up
        self.setMinimumSize(80, 120)
        self.setMaximumSize(80, 120)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                background-color: white;
                border: 2px solid #333;
                border-radius: 8px;
            }
        """)
    
    def set_card(self, card, face_up: bool = True):
        """Update the card being displayed."""
        self.card = card
        self.face_up = face_up
        self.update()
    
    def flip(self):
        """Flip the card over."""
        self.face_up = not self.face_up
        self.update()
    
    def paintEvent(self, event):
        """Custom paint event to draw the card."""
        super().paintEvent(event)
        
        if not self.card:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.face_up:
            self._draw_card_face(painter)
        else:
            self._draw_card_back(painter)
    
    def _draw_card_face(self, painter: QPainter):
        """Draw the front of the card."""
        # Determine color
        if self.card.suit in ['♥', '♦']:
            color = QColor(220, 20, 60)  # Crimson
        else:
            color = QColor(0, 0, 0)  # Black
        
        # Draw rank in corners
        font = QFont('Arial', 16, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(color)
        
        # Top-left
        painter.drawText(10, 25, self.card.rank)
        painter.drawText(10, 45, self.card.suit)
        
        # Bottom-right (rotated)
        painter.save()
        painter.translate(70, 95)
        painter.rotate(180)
        painter.drawText(0, 0, self.card.rank)
        painter.drawText(0, 20, self.card.suit)
        painter.restore()
        
        # Draw large suit in center
        font = QFont('Arial', 36, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(20, 75, self.card.suit)
    
    def _draw_card_back(self, painter: QPainter):
        """Draw the back of the card."""
        # Create gradient background
        gradient = QLinearGradient(0, 0, 80, 120)
        gradient.setColorAt(0, QColor(25, 25, 112))  # Midnight blue
        gradient.setColorAt(1, QColor(65, 105, 225))  # Royal blue
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(5, 5, 70, 110, 5, 5)
        
        # Draw pattern
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
        for i in range(0, 80, 15):
            painter.drawLine(i, 0, i, 120)
        for i in range(0, 120, 15):
            painter.drawLine(0, i, 80, i)
