"""
Texas Hold'em Poker game screen.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QMessageBox, QFrame, QGridLayout, QProgressBar)
from PyQt6.QtCore import Qt, QTimer
from ..core.card import Deck, Card
from ..core.player import Player
from ..core.poker_logic import PokerAI, HandEvaluator, OutsCalculator
from .game_widgets import HandWidget, BettingControls, ChipDisplay


class PokerGameWidget(QWidget):
    """Main widget for Texas Hold'em Poker game."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.deck = Deck()
        self.player = Player("You", chips=1000)
        self.ai_player = Player("Computer", chips=1000, is_ai=True)
        self.initial_chips = self.player.chips
        self.ai_logic = PokerAI()
        
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.round_phase = 'preflop'
        
        # Session limit (simulating "deck running out" or fixed hands)
        self.hands_played = 0
        self.max_hands = 20 
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize UI components with improved layout."""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(main_layout)
        
        # --- Left Side: Poker Table ---
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: #006400; /* Poker Green */
                border: 10px solid #8B4513; /* Saddle Brown */
                border-radius: 100px;
            }
        """)
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(50, 40, 50, 40)
        table_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # AI Opponent (Top)
        self.ai_status_label = QLabel("Waiting...")
        self.ai_status_label.setStyleSheet("color: #ecf0f1; font-size: 14px; background: transparent; border: none;")
        self.ai_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(self.ai_status_label)
        
        self.ai_hand_widget = HandWidget()
        ai_layout = QHBoxLayout()
        ai_layout.addStretch()
        ai_layout.addWidget(self.ai_hand_widget)
        ai_layout.addStretch()
        table_layout.addLayout(ai_layout)
        
        table_layout.addStretch()
        
        # Community Cards (Center)
        self.pot_label = QLabel("POT: 0")
        self.pot_label.setStyleSheet("font-size: 28px; color: gold; font-weight: bold; background: transparent; border: none;")
        self.pot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(self.pot_label)
        
        self.community_cards_widget = HandWidget()
        cc_layout = QHBoxLayout()
        cc_layout.addStretch()
        cc_layout.addWidget(self.community_cards_widget)
        cc_layout.addStretch()
        table_layout.addLayout(cc_layout)
        
        table_layout.addStretch()
        
        # Player (Bottom)
        self.player_hand_widget = HandWidget()
        p_layout = QHBoxLayout()
        p_layout.addStretch()
        p_layout.addWidget(self.player_hand_widget)
        p_layout.addStretch()
        table_layout.addLayout(p_layout)
        
        self.player_status_label = QLabel("")
        self.player_status_label.setStyleSheet("color: #ecf0f1; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        self.player_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(self.player_status_label)
        
        main_layout.addWidget(table_frame, stretch=7)
        
        # --- Right Side: Info & Controls ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)
        
        # Info Panel
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame { background-color: #34495e; border-radius: 10px; padding: 10px; }
            QLabel { color: white; border: none; }
        """)
        info_layout = QVBoxLayout(info_frame)
        
        # Chip Counts
        self.ai_chip_display = ChipDisplay("Computer", self.ai_player.chips)
        self.player_chip_display = ChipDisplay("You", self.player.chips)
        self.player_chip_display.setStyleSheet("border:none; background:transparent;")
        self.ai_chip_display.setStyleSheet("border:none; background:transparent;")
        
        info_layout.addWidget(self.ai_chip_display)
        info_layout.addWidget(self.player_chip_display)
        
        # Hands Progress
        self.hand_progress = QProgressBar()
        self.hand_progress.setFormat("Hand %v/%m")
        self.hand_progress.setMaximum(self.max_hands)
        self.hand_progress.setValue(0)
        self.hand_progress.setStyleSheet("""
             QProgressBar { border: 1px solid grey; border-radius: 4px; text-align: center; }
             QProgressBar::chunk { background-color: #9b59b6; }
        """)
        info_layout.addWidget(QLabel("Session Progress:"))
        info_layout.addWidget(self.hand_progress)
        
        right_panel.addWidget(info_frame)
        
        # Controls
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("background: transparent;")
        ctrl_layout = QVBoxLayout(ctrl_frame)
        
        btn_style = """
            QPushButton {
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                color: white;
            }
        """
        
        self.fold_btn = QPushButton("FOLD")
        self.check_btn = QPushButton("CHECK")
        self.call_btn = QPushButton("CALL")
        self.bet_btn = QPushButton("BET / RAISE")
        
        self.fold_btn.setStyleSheet(btn_style + "background-color: #c0392b;")
        self.check_btn.setStyleSheet(btn_style + "background-color: #f39c12;")
        self.call_btn.setStyleSheet(btn_style + "background-color: #2980b9;")
        self.bet_btn.setStyleSheet(btn_style + "background-color: #27ae60;")
        
        self.fold_btn.clicked.connect(self.action_fold)
        self.check_btn.clicked.connect(self.action_check)
        self.call_btn.clicked.connect(self.action_call)
        
        # Betting Logic
        self.bet_controls = BettingControls(min_bet=10, max_bet=self.player.chips)
        self.bet_controls.bet_placed.connect(self.action_bet)
        self.bet_btn.clicked.connect(lambda: self.bet_controls.show() or self.bet_controls.enable(True))
        self.bet_controls.hide()
        
        ctrl_layout.addWidget(self.fold_btn)
        ctrl_layout.addWidget(self.check_btn)
        ctrl_layout.addWidget(self.call_btn)
        ctrl_layout.addWidget(self.bet_btn)
        ctrl_layout.addWidget(self.bet_controls)
        
        right_panel.addWidget(ctrl_frame)
        right_panel.addStretch()
        
        # New Hand Button
        self.new_hand_btn = QPushButton("START NEW HAND")
        self.new_hand_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                font-size: 16px;
                padding: 20px;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #9b59b6; }
        """)
        self.new_hand_btn.clicked.connect(self.start_new_hand)
        right_panel.addWidget(self.new_hand_btn)
        
        # Exit
        finish_btn = QPushButton("FINISH SESSION")
        finish_btn.setStyleSheet("background-color: #7f8c8d; color: white; padding: 10px; border-radius: 5px;")
        finish_btn.clicked.connect(self.finish_game)
        right_panel.addWidget(finish_btn)
        
        main_layout.addLayout(right_panel, stretch=3)
        
        self.toggle_game_controls(False)

    def toggle_game_controls(self, enable: bool):
        self.fold_btn.setEnabled(enable)
        self.check_btn.setEnabled(enable)
        self.call_btn.setEnabled(enable)
        self.bet_btn.setEnabled(enable)
        if not enable:
            self.bet_controls.hide()

    def start_new_hand(self):
        # Game Over Check
        if self.player.chips <= 0:
            QMessageBox.critical(self, "Game Over", "You are out of chips!")
            self.finish_game()
            return
        if self.ai_player.chips <= 0:
            QMessageBox.information(self, "Victory", "Computer is bankrupt!")
            self.finish_game()
            return
            
        if self.hands_played >= self.max_hands:
            QMessageBox.information(self, "Session Complete", "You reached the maximum number of hands.")
            self.finish_game()
            return
            
        self.hands_played += 1
        self.hand_progress.setValue(self.hands_played)
        
        self.new_hand_btn.hide()
        self.toggle_game_controls(True)
        
        # Reset state
        self.deck.reset() # Using simple deck reset instead of complex persistent shoe for Poker
        self.player.clear_hand()
        self.ai_player.clear_hand()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.player.reset_bet()
        self.ai_player.reset_bet()
        
        self.player_hand_widget.clear_hand()
        self.ai_hand_widget.clear_hand()
        self.community_cards_widget.clear_hand()
        
        # Blinds
        sb = 10
        bb = 20
        self.player.place_bet(sb) # Simplified blind logic
        self.ai_player.place_bet(bb)
        self.pot += sb + bb
        self.update_info_display()
        
        # Deal
        for _ in range(2):
            self.player.add_card(self.deck.deal_card())
            self.ai_player.add_card(self.deck.deal_card())
            
        self.player_hand_widget.add_card(self.player.hand[0])
        self.player_hand_widget.add_card(self.player.hand[1])
        
        self.ai_hand_widget.add_card(self.ai_player.hand[0], face_up=False)
        self.ai_hand_widget.add_card(self.ai_player.hand[1], face_up=False)
        
        self.round_phase = 'preflop'
        self.status_update("Preflop: Your Action")
        self.update_buttons()

    def update_buttons(self):
        to_call = self.ai_player.current_bet - self.player.current_bet
        
        if to_call == 0:
            self.check_btn.setEnabled(True)
            self.call_btn.setEnabled(False) 
            self.call_btn.setText("CALL")
        else:
            self.check_btn.setEnabled(False)
            self.call_btn.setEnabled(True)
            self.call_btn.setText(f"CALL {to_call}")
            
    def next_phase(self):
        self.player.reset_bet()
        self.ai_player.reset_bet()
        self.current_bet = 0
        
        if self.round_phase == 'preflop':
            self.round_phase = 'flop'
            for _ in range(3): self.community_cards.append(self.deck.deal_card())
        elif self.round_phase == 'flop':
            self.round_phase = 'turn'
            self.community_cards.append(self.deck.deal_card())
        elif self.round_phase == 'turn':
            self.round_phase = 'river'
            self.community_cards.append(self.deck.deal_card())
        elif self.round_phase == 'river':
            self.showdown()
            return
            
        self.community_cards_widget.clear_hand()
        for card in self.community_cards:
            self.community_cards_widget.add_card(card)
            
        self.status_update(f"{self.round_phase.capitalize()}: Your Action")
        self.update_buttons()

    def ai_turn(self):
        self.status_update("Computer is thinking...")
        # Disable controls while AI thinks
        self.toggle_game_controls(False)
        QTimer.singleShot(1000, self._process_ai_move)
        
    def _process_ai_move(self):
        game_state = {
            'pot': self.pot,
            'current_bet': self.ai_player.current_bet,
            'to_call': self.player.current_bet - self.ai_player.current_bet,
            'round': self.round_phase,
            'ai_chips': self.ai_player.chips,
            'opponent_last_bet': self.player.current_bet,
            'big_blind': 20
        }
        
        action, amount = self.ai_logic.decide_action(
            game_state, self.ai_player.hand, self.community_cards
        )
        
        if action == 'FOLD':
            self.status_update("Computer Folds. You Win!")
            self.distribute_pot(self.player)
            self.end_hand()
        elif action == 'CHECK':
            self.ai_status_label.setText("Check")
            if self.player.current_bet == self.ai_player.current_bet:
                self.toggle_game_controls(True)
                self.next_phase()
            else:
                self.toggle_game_controls(True)
                self.status_update("Your Action")
        elif action == 'CALL':
            call_amt = self.player.current_bet - self.ai_player.current_bet
            self.ai_player.place_bet(call_amt)
            self.pot += call_amt
            self.update_info_display()
            self.ai_status_label.setText("Call")
            self.toggle_game_controls(True)
            self.next_phase()
        elif action in ['BET', 'RAISE']:
            self.ai_player.place_bet(amount)
            self.pot += amount
            self.update_info_display()
            self.ai_status_label.setText(f"{action} {amount}")
            self.toggle_game_controls(True)
            self.update_buttons()
            self.status_update("Your turn to call/raise")

    def action_fold(self):
        self.status_update("You Folded.")
        self.distribute_pot(self.ai_player)
        self.end_hand()

    def action_check(self):
        self.status_update("You Checked.")
        self.ai_turn()

    def action_call(self):
        amt = self.ai_player.current_bet - self.player.current_bet
        self.player.place_bet(amt)
        self.pot += amt
        self.update_info_display()
        self.status_update("You Called.")
        self.next_phase() 

    def action_bet(self, amount):
        self.bet_controls.hide()
        self.player.place_bet(amount)
        self.pot += amount
        self.update_info_display()
        self.status_update(f"You Bet {amount}")
        self.ai_turn()

    def showdown(self):
        self.status_update("Showdown!")
        
        self.ai_hand_widget.clear_hand()
        for card in self.ai_player.hand:
            self.ai_hand_widget.add_card(card, face_up=True)
            
        player_score, _, p_name = HandEvaluator.evaluate_hand(self.player.hand + self.community_cards)
        ai_score, _, ai_name = HandEvaluator.evaluate_hand(self.ai_player.hand + self.community_cards)
        
        msg = f"You: {p_name}\nAI: {ai_name}\n\n"
        
        if player_score > ai_score:
            msg += "You Win!"
            self.distribute_pot(self.player)
        elif ai_score > player_score:
            msg += "Computer Wins!"
            self.distribute_pot(self.ai_player)
        else:
            msg += "Split Pot!"
            half = self.pot // 2
            self.player.win_chips(half)
            self.ai_player.win_chips(half)
            self.pot = 0
            
        QMessageBox.information(self, "Round Result", msg)
        self.end_hand()

    def distribute_pot(self, winner: Player):
        winner.win_chips(self.pot)
        self.pot = 0
        self.update_info_display()

    def end_hand(self):
        self.toggle_game_controls(False)
        self.new_hand_btn.show()

    def update_info_display(self):
        self.pot_label.setText(f"POT: {self.pot}")
        self.player_chip_display.update_chips(self.player.chips)
        self.ai_chip_display.update_chips(self.ai_player.chips)

    def status_update(self, msg):
        self.player_status_label.setText(msg)

    def finish_game(self):
        net = self.player.chips - self.initial_chips
        result = "PROFIT" if net > 0 else "LOSS"
        msg = f"Session Ended.\n\nHands Played: {self.hands_played}\nFinal Chips: {self.player.chips}\nNet: {net}\nResult: {result}"
        QMessageBox.information(self, "Session Result", msg)
        parent = self.window()
        if parent:
            parent.close()
