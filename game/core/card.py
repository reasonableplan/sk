"""
Card and Deck classes for casino games.
"""
import random
from typing import List, Optional


class Card:
    """Represents a single playing card."""
    
    SUITS = ['♠', '♥', '♦', '♣']
    SUIT_NAMES = ['Spades', 'Hearts', 'Diamonds', 'Clubs']
    RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
    
    def __init__(self, suit: str, rank: str):
        """
        Initialize a card.
        
        Args:
            suit: Card suit (♠, ♥, ♦, ♣)
            rank: Card rank (A, 2-10, J, Q, K)
        """
        self.suit = suit
        self.rank = rank
        self._calculate_value()
    
    def _calculate_value(self):
        """Calculate card value for Blackjack."""
        if self.rank in ['J', 'Q', 'K']:
            self.value = 10
        elif self.rank == 'A':
            self.value = 11  # Ace can be 1 or 11, default to 11
        else:
            self.value = int(self.rank)
    
    def get_poker_rank_value(self) -> int:
        """Get numeric rank value for poker (2=2, ..., A=14)."""
        if self.rank == 'A':
            return 14
        elif self.rank == 'K':
            return 13
        elif self.rank == 'Q':
            return 12
        elif self.rank == 'J':
            return 11
        else:
            return int(self.rank)
    
    def get_suit_index(self) -> int:
        """Get suit index (0-3)."""
        return self.SUITS.index(self.suit)
    
    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"
    
    def __repr__(self) -> str:
        return f"Card({self.suit}, {self.rank})"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank
    
    def __hash__(self) -> int:
        return hash((self.suit, self.rank))


class Deck:
    """Represents a deck of 52 playing cards."""
    
    def __init__(self, num_decks: int = 1):
        """
        Initialize deck(s).
        
        Args:
            num_decks: Number of 52-card decks to use
        """
        self.num_decks = num_decks
        self.cards: List[Card] = []
        self.reset()
    
    def reset(self):
        """Reset and shuffle the deck."""
        self.cards = []
        for _ in range(self.num_decks):
            for suit in Card.SUITS:
                for rank in Card.RANKS:
                    self.cards.append(Card(suit, rank))
        self.shuffle()
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
    
    def deal_card(self) -> Optional[Card]:
        """
        Deal one card from the deck.
        
        Returns:
            Card object or None if deck is empty
        """
        if len(self.cards) > 0:
            return self.cards.pop()
        return None
    
    def cards_remaining(self) -> int:
        """Get number of cards remaining in deck."""
        return len(self.cards)
    
    def __len__(self) -> int:
        return len(self.cards)
