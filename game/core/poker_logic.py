"""
Poker game logic including hand evaluation and AI.
"""
from typing import List, Tuple, Dict, Set
from collections import Counter
from itertools import combinations
import random
from .card import Card


class HandEvaluator:
    """Evaluates poker hands and determines winners."""
    
    # Hand rankings (higher is better)
    HAND_RANKS = {
        'High Card': 1,
        'One Pair': 2,
        'Two Pair': 3,
        'Three of a Kind': 4,
        'Straight': 5,
        'Flush': 6,
        'Full House': 7,
        'Four of a Kind': 8,
        'Straight Flush': 9,
        'Royal Flush': 10
    }
    
    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[int, List[int], str]:
        """
        Evaluate a poker hand (best 5 cards from 7).
        
        Args:
            cards: List of cards (typically 7: 2 hole + 5 community)
            
        Returns:
            Tuple of (rank, tiebreakers, hand_name)
        """
        if len(cards) < 5:
            return (0, [], 'Incomplete Hand')
        
        best_rank = 0
        best_tiebreakers = []
        best_name = ''
        
        # Try all 5-card combinations
        for combo in combinations(cards, 5):
            rank, tiebreakers, name = HandEvaluator._evaluate_5_cards(list(combo))
            if rank > best_rank or (rank == best_rank and tiebreakers > best_tiebreakers):
                best_rank = rank
                best_tiebreakers = tiebreakers
                best_name = name
        
        return (best_rank, best_tiebreakers, best_name)
    
    @staticmethod
    def _evaluate_5_cards(cards: List[Card]) -> Tuple[int, List[int], str]:
        """Evaluate exactly 5 cards."""
        ranks = sorted([c.get_poker_rank_value() for c in cards], reverse=True)
        suits = [c.suit for c in cards]
        rank_counts = Counter(ranks)
        
        is_flush = len(set(suits)) == 1
        is_straight = HandEvaluator._is_straight(ranks)
        
        # Check for Royal Flush
        if is_flush and is_straight and ranks[0] == 14:
            return (HandEvaluator.HAND_RANKS['Royal Flush'], ranks, 'Royal Flush')
        
        # Check for Straight Flush
        if is_flush and is_straight:
            return (HandEvaluator.HAND_RANKS['Straight Flush'], ranks, 'Straight Flush')
        
        # Check for Four of a Kind
        if 4 in rank_counts.values():
            quad = [r for r, c in rank_counts.items() if c == 4][0]
            kicker = [r for r in ranks if r != quad][0]
            return (HandEvaluator.HAND_RANKS['Four of a Kind'], [quad, kicker], 'Four of a Kind')
        
        # Check for Full House
        if 3 in rank_counts.values() and 2 in rank_counts.values():
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            return (HandEvaluator.HAND_RANKS['Full House'], [trips, pair], 'Full House')
        
        # Check for Flush
        if is_flush:
            return (HandEvaluator.HAND_RANKS['Flush'], ranks, 'Flush')
        
        # Check for Straight
        if is_straight:
            return (HandEvaluator.HAND_RANKS['Straight'], ranks, 'Straight')
        
        # Check for Three of a Kind
        if 3 in rank_counts.values():
            trips = [r for r, c in rank_counts.items() if c == 3][0]
            kickers = sorted([r for r in ranks if r != trips], reverse=True)
            return (HandEvaluator.HAND_RANKS['Three of a Kind'], [trips] + kickers, 'Three of a Kind')
        
        # Check for Two Pair
        pairs = [r for r, c in rank_counts.items() if c == 2]
        if len(pairs) == 2:
            pairs = sorted(pairs, reverse=True)
            kicker = [r for r in ranks if r not in pairs][0]
            return (HandEvaluator.HAND_RANKS['Two Pair'], pairs + [kicker], 'Two Pair')
        
        # Check for One Pair
        if len(pairs) == 1:
            pair = pairs[0]
            kickers = sorted([r for r in ranks if r != pair], reverse=True)
            return (HandEvaluator.HAND_RANKS['One Pair'], [pair] + kickers, 'One Pair')
        
        # High Card
        return (HandEvaluator.HAND_RANKS['High Card'], ranks, 'High Card')
    
    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        """Check if ranks form a straight."""
        sorted_ranks = sorted(set(ranks), reverse=True)
        if len(sorted_ranks) < 5:
            return False
        
        # Check normal straight
        for i in range(len(sorted_ranks) - 4):
            if sorted_ranks[i] - sorted_ranks[i+4] == 4:
                return True
        
        # Check A-2-3-4-5 (wheel)
        if sorted_ranks == [14, 5, 4, 3, 2]:
            return True
        
        return False


class OutsCalculator:
    """Calculate outs and probabilities for poker hands."""
    
    @staticmethod
    def calculate_outs(hole_cards: List[Card], community_cards: List[Card], 
                       known_cards: Set[Card]) -> Dict[str, int]:
        """
        Calculate outs for various draws.
        
        Args:
            hole_cards: Player's hole cards
            community_cards: Community cards on board
            known_cards: All known cards (to exclude from deck)
            
        Returns:
            Dictionary of draw types and their outs count
        """
        all_cards = hole_cards + community_cards
        outs = {}
        
        # Calculate remaining cards
        remaining = 52 - len(known_cards)
        
        # Simplified outs calculation
        # This is a basic implementation - can be enhanced
        
        return {
            'flush_draw': OutsCalculator._count_flush_outs(all_cards, remaining),
            'straight_draw': OutsCalculator._count_straight_outs(all_cards, remaining),
            'pair_outs': OutsCalculator._count_pair_outs(all_cards, remaining)
        }
    
    @staticmethod
    def _count_flush_outs(cards: List[Card], remaining: int) -> int:
        """Count outs for flush draw."""
        suit_counts = Counter([c.suit for c in cards])
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        
        if max_suit_count == 4:
            return min(9, remaining)  # 9 outs for flush draw
        return 0
    
    @staticmethod
    def _count_straight_outs(cards: List[Card], remaining: int) -> int:
        """Count outs for straight draw (simplified)."""
        ranks = sorted(set([c.get_poker_rank_value() for c in cards]))
        
        # Check for open-ended straight draw
        for i in range(len(ranks) - 3):
            if ranks[i+3] - ranks[i] == 3:
                return min(8, remaining)
        
        return 0
    
    @staticmethod
    def _count_pair_outs(cards: List[Card], remaining: int) -> int:
        """Count outs to make a pair."""
        if len(cards) >= 2:
            return min(6, remaining)  # 6 outs to pair one of two hole cards
        return 0


class PokerAI:
    """
    Advanced AI player for Texas Hold'em poker using rule-based logic.
    Feature: Hand Strength, Pot Odds, Outs Calculation, Opponent Modeling (Heuristic).
    """
    
    def __init__(self, aggression: float = 0.6, bluff_frequency: float = 0.4):
        self.aggression = aggression
        self.bluff_frequency = bluff_frequency
        self.opponent_actions = []

    def decide_action(self, game_state: Dict, hole_cards: List[Card], 
                     community_cards: List[Card]) -> Tuple[str, int]:
        """
        Decide action using a 4-step process:
        1. Hand Strength Evaluation
        2. Potential Evaluation (Outs)
        3. Game Situation Analysis (Opponent Model, Pot Odds)
        4. Decision Execution
        """
        pot = game_state.get('pot', 0)
        to_call = game_state.get('to_call', 0)
        ai_chips = game_state.get('ai_chips', 0)
        round_name = game_state.get('round', 'preflop')
        
        # 1. Hand Strength
        if round_name == 'preflop':
            hand_strength = self._evaluate_preflop_strength(hole_cards)
            is_strong = hand_strength > 0.7
            is_weak = hand_strength < 0.4
        else:
            all_cards = hole_cards + community_cards
            rank, _, _ = HandEvaluator.evaluate_hand(all_cards)
            # Normalize rank (1-10) to 0.0-1.0
            hand_strength = rank / 10.0
            
            # Adjust strength based on board texture (simplified)
            # e.g., if we have a pair but board has 4 flush cards, our pair is weaker
            pass 

        # 2. Potential (Outs) - Postflop only
        outs_prob = 0.0
        if round_name != 'preflop':
            known_cards = set(hole_cards + community_cards)
            outs = OutsCalculator.calculate_outs(hole_cards, community_cards, known_cards)
            total_outs = sum(outs.values())
            # Rule of 2 and 4 (approximate percentage)
            cards_to_come = 2 if round_name == 'flop' else 1
            outs_prob = min((total_outs * cards_to_come * 2) / 100.0, 1.0)
            
        # 3. Game State & Opponent Model
        pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0
        opponent_strength = self._estimate_opponent_strength(game_state, community_cards)
        
        # Effective strength combines current strength and potential
        effective_strength = max(hand_strength, outs_prob)
        
        # 4. Decision Tree
        if round_name == 'preflop':
            return self._decide_preflop(hand_strength, to_call, ai_chips, pot, game_state)
        else:
            return self._decide_postflop(effective_strength, opponent_strength, pot_odds, 
                                       to_call, ai_chips, pot, game_state)

    def _decide_preflop(self, strength: float, to_call: int, chips: int, pot: int, game_state: Dict) -> Tuple[str, int]:
        # Tiered preflop strategy
        min_raise = max(to_call * 2, game_state.get('big_blind', 20))
        
        if strength > 0.8: # Premium hands (AA, KK, AKs)
            raise_amt = int(pot * 1.5) if to_call == 0 else min_raise * 2
            return ('RAISE', min(raise_amt, chips))
            
        elif strength > 0.6: # Strong hands (TT-QQ, AQs)
            if to_call < chips * 0.1: # Call if cheap
                return ('RAISE' if random.random() < self.aggression else 'CALL', to_call)
            return ('CALL', to_call)
            
        elif strength > 0.4: # Playable hands (Pairs, connectors)
            if to_call <= game_state.get('big_blind', 20):
                return ('CALL', to_call)
            # Fold to aggression
            return ('FOLD', 0)
            
        else: # Trash
            # Random bluff check
            if to_call == 0 and random.random() < self.bluff_frequency:
                return ('BET', game_state.get('big_blind', 20))
            return ('CHECK' if to_call == 0 else 'FOLD', 0)

    def _decide_postflop(self, my_strength: float, opp_strength: float, pot_odds: float, 
                        to_call: int, chips: int, pot: int, game_state: Dict) -> Tuple[str, int]:
        
        # 1. Bluff Catching Logic
        # If opponent bets, we reduce the credit we give them, assuming they might be bluffing.
        adjusted_opp_strength = min(opp_strength, 0.8) 
        if to_call > pot * 0.5: # Large bet
             adjusted_opp_strength -= 0.1 # Assume they are polarizing (nuts or air)
             
        win_prob = my_strength - adjusted_opp_strength + 0.5 
        
        # 2. Hero Calling (Call with weak hand to catch bluff)
        # If we have a mid-strength hand (0.4-0.6) and pot odds aren't terrible, call sometimes.
        can_bluff_catch = (0.4 <= my_strength <= 0.7) and (to_call < chips * 0.4)
        if to_call > 0 and can_bluff_catch:
            if random.random() < 0.4: # 40% chance to hero call
                return ('CALL', to_call)

        if to_call == 0:
            # Check or Bet?
            if win_prob > 0.7: # Value bet
                bet = int(pot * 0.75)
                return ('BET', min(bet, chips))
            
            # Active Bluffing (Betting with weak hand)
            # If our hand is weak (<0.4) but we want to steal the pot
            if my_strength < 0.4 and random.random() < self.bluff_frequency: 
                # Big bluff to scare opponent
                bet = int(pot * 1.0) 
                return ('BET', min(bet, chips))
            
            return ('CHECK', 0)
        else:
            # Fold, Call, or Raise?
            
            # Hardened Value Raise
            if my_strength > 0.8:
                raise_amt = int(pot * 1.5)
                return ('RAISE', min(raise_amt, chips))
            
            # Decent hand call (Standard)
            if my_strength > 0.6:
                if to_call < chips:
                    return ('CALL', to_call)
            
            # Active Bluff Raise (Re-raise bluff)
            # If we are facing a bet, sometimes raise big with trash to force a fold
            if to_call > 0 and my_strength < 0.4 and random.random() < (self.bluff_frequency * 0.5):
                raise_amt = int(pot * 2.0) # Huge overbet bluff
                return ('RAISE', min(raise_amt, chips))
            
            # Standard Odds Calculation
            if win_prob > pot_odds: 
                return ('CALL', to_call)
                
            # Last ditch bluff catch or fold
            if win_prob > 0.2 and win_prob > pot_odds - 0.15:
                 return ('CALL', to_call)
            
            return ('FOLD', 0)

    def _evaluate_preflop_strength(self, hole_cards: List[Card]) -> float:
        """Evaluate preflop hand strength."""
        if len(hole_cards) != 2:
            return 0.0
        c1, c2 = hole_cards
        r1, r2 = c1.get_poker_rank_value(), c2.get_poker_rank_value()
        
        if r1 == r2: # Pocket pair
            return 0.6 + (r1 / 40.0)
        
        high = max(r1, r2)
        low = min(r1, r2)
        gap = high - low
        
        score = high / 20.0
        if c1.suit == c2.suit: score += 0.1
        if gap < 3: score += 0.1
        if gap == 1: score += 0.05
        
        return min(score, 0.95)

    def _estimate_opponent_strength(self, game_state: Dict, community_cards: List[Card]) -> float:
        """
        Estimate opponent strength based on board texture and betting.
        If board is wet (lots of draws) and opponent bets big, strength is high.
        """
        opp_bet = game_state.get('opponent_last_bet', 0)
        pot = game_state.get('pot', 1)
        
        base_strength = 0.4 # Assume average hand
        
        # Betting cues
        if opp_bet > pot * 0.8: base_strength = 0.8
        elif opp_bet > pot * 0.5: base_strength = 0.6
        elif opp_bet > 0: base_strength = 0.5
        else: base_strength = 0.3
        
        # Board texture cues (simplified)
        if len(community_cards) >= 3:
            # Check for flush/straight possibilities on board
            suits = [c.suit for c in community_cards]
            ranks = sorted([c.get_poker_rank_value() for c in community_cards])
            
            is_wet_board = False
            if max(Counter(suits).values()) >= 3: is_wet_board = True
            
            # If board is scary and opponent bets, credit them with strength
            if is_wet_board and opp_bet > 0:
                base_strength += 0.1
                
        return min(base_strength, 1.0)

    def record_opponent_action(self, action: str, amount: int, pot: int):
        self.opponent_actions.append({'action': action, 'amount': amount, 'pot': pot})
