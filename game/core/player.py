"""
Player class for casino games.
"""
from typing import List
from .card import Card


class Player:
    """Represents a player in casino games."""
    
    def __init__(self, name: str, chips: int = 1000, is_dealer: bool = False, is_ai: bool = False):
        """
        Initialize a player.
        
        Args:
            name: Player name
            chips: Starting chip count
            is_dealer: Whether this is the dealer (Blackjack)
            is_ai: Whether this is an AI player (Poker)
        """
        self.name = name
        self.chips = chips
        self.hand: List[Card] = []
        self.is_dealer = is_dealer
        self.is_ai = is_ai
        self.current_bet = 0
        self.folded = False
        self.all_in = False
    
    def add_card(self, card: Card):
        """Add a card to player's hand."""
        self.hand.append(card)
    
    def clear_hand(self):
        """Clear player's hand."""
        self.hand = []
        self.folded = False
        self.all_in = False
    
    def get_hand_value(self) -> int:
        """
        Calculate hand value for Blackjack.
        Handles Ace as 1 or 11.
        
        Returns:
            Hand value
        """
        value = 0
        aces = 0
        
        for card in self.hand:
            if card.rank == 'A':
                aces += 1
                value += 11
            else:
                value += card.value
        
        # Adjust for Aces
        while value > 21 and aces > 0:
            value -= 10
            aces -= 1
        
        return value
    
    def place_bet(self, amount: int) -> bool:
        """
        Place a bet.
        
        Args:
            amount: Bet amount
            
        Returns:
            True if bet successful, False if insufficient chips
        """
        if amount > self.chips:
            return False
        self.chips -= amount
        self.current_bet += amount
        if self.chips == 0:
            self.all_in = True
        return True
    
    def win_chips(self, amount: int):
        """Add chips to player's stack."""
        self.chips += amount
    
    def reset_bet(self):
        """Reset current bet to 0."""
        self.current_bet = 0
    
    def fold(self):
        """Fold hand (Poker)."""
        self.folded = True
    
    def __str__(self) -> str:
        return f"{self.name} (Chips: {self.chips})"
