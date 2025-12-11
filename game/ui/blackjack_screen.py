"""
Blackjack game screen.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QMessageBox, QFrame, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from ..core.card import Deck
from ..core.player import Player
from ..core.blackjack_logic import BlackjackDealer
from .game_widgets import HandWidget, BettingControls, ChipDisplay


class BlackjackGameWidget(QWidget):
    """Main widget for Blackjack game."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck = Deck(num_decks=6)
        self.player = Player("You")
        self.dealer = Player("Dealer", is_dealer=True)
        self.initial_chips = self.player.chips
        self.game_active = False
        self.shoe_penetration_limit = 0.25  # End game when 25% cards left
        
        self.setup_ui()
        self.reset_game_state()
        
    def setup_ui(self):
        """Initialize UI components with improved layout."""
        # Main layout - Horizontal mainly (Table left, Controls/Info right)
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)
        
        # --- Left Side: Game Table ---
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: #004d00;
                border: 10px solid #654321;
                border-radius: 40px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(40, 40, 40, 40)
        
        # Dealer Section
        dealer_label = QLabel("DEALER")
        dealer_label.setStyleSheet("color: rgba(255,255,255,0.7); font-weight: bold; font-size: 16px; border: none;")
        dealer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(dealer_label)
        
        self.dealer_score_label = QLabel("0")
        self.dealer_score_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold; border: none;")
        self.dealer_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(self.dealer_score_label)
        
        self.dealer_hand_widget = HandWidget()
        dealer_hand_frame = QFrame()
        dealer_hand_frame.setStyleSheet("background-color: transparent; border: none;")
        dh_layout = QHBoxLayout(dealer_hand_frame)
        dh_layout.addWidget(self.dealer_hand_widget)
        dh_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(dealer_hand_frame)
        
        table_layout.addStretch()
        
        # Center Message
        self.message_label = QLabel("PLACE YOUR BET")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("color: gold; font-size: 32px; font-weight: bold; border: none; text-shadow: 2px 2px black;")
        table_layout.addWidget(self.message_label)
        
        table_layout.addStretch()
        
        # Player Section
        self.player_hand_widget = HandWidget()
        player_hand_frame = QFrame()
        player_hand_frame.setStyleSheet("background-color: transparent; border: none;")
        ph_layout = QHBoxLayout(player_hand_frame)
        ph_layout.addWidget(self.player_hand_widget)
        ph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(player_hand_frame)
        
        self.player_score_label = QLabel("0")
        self.player_score_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold; border: none;")
        self.player_score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(self.player_score_label)
        
        player_label = QLabel("YOU")
        player_label.setStyleSheet("color: rgba(255,255,255,0.7); font-weight: bold; font-size: 16px; border: none;")
        player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(player_label)
        
        main_layout.addWidget(table_frame, stretch=7)
        
        # --- Right Side: Controls & Info ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
        
        # Info Card
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-radius: 15px;
                padding: 15px;
            }
            QLabel { color: white; border: none; }
        """)
        info_layout = QVBoxLayout(info_frame)
        
        self.chip_display = ChipDisplay(self.player.name, self.player.chips)
        self.chip_display.setStyleSheet("border: none; background: transparent;")
        info_layout.addWidget(self.chip_display)
        
        # Shoe Progress
        shoe_label = QLabel("Shoe Remaining:")
        self.shoe_progress = QProgressBar()
        self.shoe_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
                height: 15px;
            }
            QProgressBar::chunk {
                background-color: #3498db; 
            }
        """)
        self.shoe_progress.setValue(100)
        info_layout.addWidget(shoe_label)
        info_layout.addWidget(self.shoe_progress)
        
        right_panel.addWidget(info_frame)
        
        # Betting Controls
        self.betting_controls = BettingControls(max_bet=self.player.chips)
        self.betting_controls.bet_placed.connect(self.start_round)
        right_panel.addWidget(self.betting_controls)
        
        # Game Actions
        action_layout = QVBoxLayout()
        
        btn_style = """
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border-radius: 10px;
                padding: 15px;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #bdc3c7;
            }
            QPushButton:hover { background-color: #ffffff; border-color: #3498db; }
            QPushButton:disabled { background-color: #7f8c8d; color: #bdc3c7; border-color: #7f8c8d; }
        """
        
        self.hit_button = QPushButton("HIT")
        self.stand_button = QPushButton("STAND")
        self.hit_button.setStyleSheet(btn_style)
        self.stand_button.setStyleSheet(btn_style)
        
        self.hit_button.clicked.connect(self.hit)
        self.stand_button.clicked.connect(self.stand)
        
        action_layout.addWidget(self.hit_button)
        action_layout.addWidget(self.stand_button)
        right_panel.addLayout(action_layout)
        
        # New Round Button
        self.new_round_button = QPushButton("NEXT ROUND")
        self.new_round_button.setStyleSheet("""
            QPushButton {
                background-color: #f1c40f; 
                color: #2c3e50;
                border-radius: 10px;
                padding: 15px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton:hover { background-color: #f39c12; }
        """)
        self.new_round_button.clicked.connect(self.prepare_new_round)
        right_panel.addWidget(self.new_round_button)
        
        # Exit Button
        finish_btn = QPushButton("FINISH SESSION")
        finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        finish_btn.clicked.connect(self.finish_game)
        right_panel.addWidget(finish_btn)
        
        right_panel.addStretch()
        main_layout.addLayout(right_panel, stretch=3)
        
    def reset_game_state(self):
        """Full reset."""
        self.hit_button.setEnabled(False)
        self.stand_button.setEnabled(False)
        self.new_round_button.hide()
        self.player_hand_widget.clear_hand()
        self.dealer_hand_widget.clear_hand()
        self.betting_controls.show()
        self.betting_controls.enable(True)
        self.deck.reset()
        self.shoe_progress.setValue(100)
        
    def get_cards_percentage(self) -> float:
        return (self.deck.cards_remaining() / (52 * self.deck.num_decks)) * 100

    def start_round(self, bet_amount):
        if not self.player.place_bet(bet_amount):
            QMessageBox.warning(self, "No Chips", "You are bankrupt!")
            self.finish_game()
            return
            
        self.chip_display.update_chips(self.player.chips)
        self.betting_controls.hide()
        self.betting_controls.enable(False)
        self.hit_button.setEnabled(True)
        self.stand_button.setEnabled(True)
        self.message_label.setText("YOUR TURN")
        
        self.player.clear_hand()
        self.dealer.clear_hand()
        
        # Deal
        self.player.add_card(self.deck.deal_card())
        self.dealer.add_card(self.deck.deal_card())
        self.player.add_card(self.deck.deal_card())
        self.dealer.add_card(self.deck.deal_card())
        
        self.update_ui(show_dealer_hole=False)
        
        # Check BJ
        if self.player.get_hand_value() == 21:
            self.handle_blackjack()
            
        self.shoe_progress.setValue(int(self.get_cards_percentage()))

    def update_ui(self, show_dealer_hole: bool = False):
        self.player_hand_widget.clear_hand()
        for card in self.player.hand:
            self.player_hand_widget.add_card(card)
            
        self.dealer_hand_widget.clear_hand()
        for i, card in enumerate(self.dealer.hand):
            if i == 0 and not show_dealer_hole:
                self.dealer_hand_widget.add_card(card, face_up=False)
            else:
                self.dealer_hand_widget.add_card(card, face_up=True)
                
        self.player_score_label.setText(str(self.player.get_hand_value()))
        
        if show_dealer_hole:
            self.dealer_score_label.setText(str(self.dealer.get_hand_value()))
        else:
            val = self.dealer.hand[1].value if self.dealer.hand[1].rank != 'A' else 11
            self.dealer_score_label.setText(f"{val} + ?")

    def hit(self):
        self.player.add_card(self.deck.deal_card())
        self.update_ui()
        self.shoe_progress.setValue(int(self.get_cards_percentage()))
        
        if self.player.get_hand_value() > 21:
            self.end_round("bust")

    def stand(self):
        self.hit_button.setEnabled(False)
        self.stand_button.setEnabled(False)
        self.play_dealer_turn()

    def play_dealer_turn(self):
        self.update_ui(show_dealer_hole=True)
        self.message_label.setText("DEALER TURN")
        
        # Basic automation with simple delay loop (blocking for simplicity, can be improved)
        while self.dealer.get_hand_value() <= 16:
            self.dealer.add_card(self.deck.deal_card())
            self.update_ui(show_dealer_hole=True)
            QTimer.singleShot(500, lambda: None) # Non-blocking wait dummy
        
        d_val = self.dealer.get_hand_value()
        p_val = self.player.get_hand_value()
        
        if d_val > 21:
            self.end_round("dealer_bust")
        elif d_val > p_val:
            self.end_round("lose")
        elif d_val < p_val:
            self.end_round("win")
        else:
            self.end_round("push")

    def handle_blackjack(self):
        d_val = self.dealer.get_hand_value()
        if d_val == 21:
            self.end_round("push")
        else:
            self.end_round("blackjack")

    def end_round(self, result: str):
        self.hit_button.setEnabled(False)
        self.stand_button.setEnabled(False)
        self.update_ui(show_dealer_hole=True)
        
        bet = self.player.current_bet
        winnings = 0
        
        if result == "blackjack":
            winnings = int(bet * 2.5)
            self.message_label.setText("BLACKJACK! WIN 3:2")
        elif result == "win" or result == "dealer_bust":
            winnings = bet * 2
            self.message_label.setText("YOU WIN!")
        elif result == "push":
            winnings = bet
            self.message_label.setText("PUSH")
        else:
            self.message_label.setText("DEALER WINS")
            
        if winnings > 0:
            self.player.win_chips(winnings)
            
        self.player.reset_bet()
        self.chip_display.update_chips(self.player.chips)
        self.shoe_progress.setValue(int(self.get_cards_percentage()))
        
        self.new_round_button.show()

    def prepare_new_round(self):
        # Check Game Over Conditions
        if self.player.chips <= 0:
            QMessageBox.critical(self, "GAME OVER", "You ran out of chips!")
            self.finish_game()
            return

        if self.get_cards_percentage() < 25:
            QMessageBox.information(self, "Shoe Empty", "The shoe is exhausted. Game Over.")
            self.finish_game()
            return
            
        self.reset_round_ui()

    def reset_round_ui(self):
        self.new_round_button.hide()
        self.hit_button.setEnabled(False)
        self.stand_button.setEnabled(False)
        self.betting_controls.show()
        self.betting_controls.enable(True)
        self.betting_controls.set_max_bet(self.player.chips)
        self.player_hand_widget.clear_hand()
        self.dealer_hand_widget.clear_hand()
        self.message_label.setText("PLACE YOUR BET")
        self.player_score_label.setText("0")
        self.dealer_score_label.setText("0")

    def finish_game(self):
        """Calculate final result and close."""
        net = self.player.chips - self.initial_chips
        result = "PROFIT" if net > 0 else "LOSS"
        msg = f"Game Over!\n\nFinal Chips: {self.player.chips}\nNet: {net}\nResult: {result}"
        QMessageBox.information(self, "Session Result", msg)
        
        # Close widget or signal parent
        parent = self.window()
        if parent:
            parent.close() # Or just return to menu
