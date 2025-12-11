"""
Blackjack game logic.
"""


class BlackjackDealer:
    """Dealer logic for Blackjack."""
    
    @staticmethod
    def should_hit(hand_value: int) -> bool:
        """
        Determine if dealer should hit.
        Standard rule: Hit on 16 or less, stand on 17 or more.
        
        Args:
            hand_value: Current hand value
            
        Returns:
            True if should hit, False if should stand
        """
        return hand_value <= 16
    
    @staticmethod
    def check_blackjack(hand_value: int, num_cards: int) -> bool:
        """
        Check if hand is a natural blackjack.
        
        Args:
            hand_value: Hand value
            num_cards: Number of cards in hand
            
        Returns:
            True if natural blackjack (21 with 2 cards)
        """
        return hand_value == 21 and num_cards == 2
    
    @staticmethod
    def check_bust(hand_value: int) -> bool:
        """Check if hand is bust (over 21)."""
        return hand_value > 21
    
    @staticmethod
    def calculate_payout(player_value: int, dealer_value: int, 
                        bet: int, player_blackjack: bool, dealer_blackjack: bool) -> int:
        """
        Calculate payout for player.
        
        Args:
            player_value: Player's hand value
            dealer_value: Dealer's hand value
            bet: Bet amount
            player_blackjack: Whether player has blackjack
            dealer_blackjack: Whether dealer has blackjack
            
        Returns:
            Payout amount (0 for loss, bet for push, bet*2 for win, bet*2.5 for blackjack)
        """
        # Both blackjack - push
        if player_blackjack and dealer_blackjack:
            return bet
        
        # Player blackjack - 3:2 payout
        if player_blackjack:
            return int(bet * 2.5)
        
        # Dealer blackjack - player loses
        if dealer_blackjack:
            return 0
        
        # Player bust - loses
        if player_value > 21:
            return 0
        
        # Dealer bust - player wins
        if dealer_value > 21:
            return bet * 2
        
        # Compare values
        if player_value > dealer_value:
            return bet * 2
        elif player_value == dealer_value:
            return bet  # Push
        else:
            return 0  # Dealer wins
