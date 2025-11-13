"""Hand value calculation and outcome comparison for Blackjack."""

from typing import Tuple, List
from cards import Card, Rank


def calculate_hand_value(cards: List[Card]) -> Tuple[int, bool]:
    """Calculate hand value with intelligent Ace handling.
    
    Strategy: Count all Aces as 11, convert to 1 until total ≤ 21.
    
    Args:
        cards: List of Card objects
    
    Returns:
        Tuple of (total_value, hand_has_usable_ace)
    """
    total = sum(card.get_value(allow_ace_as_one=False) for card in cards)
    num_aces = sum(1 for card in cards if card.rank == Rank.ACE)

    # Convert Aces from 11 to 1 until hand <= 21
    while total > 21 and num_aces > 0:
        total -= 10
        num_aces -= 1

    # Soft hand if an Ace remains as 11
    has_ace = num_aces > 0
    return total, has_ace


def compare_hands(player_total: int, dealer_total: int) -> Tuple[str, str]:
    """Compare player and dealer hands to determine outcome.
    
    Returns:
        Tuple of (result_string, message_string)
        - result_string: "bust", "win", "lose", or "push"
        - message_string: Human-readable outcome
    """
    if player_total > 21:
        return "bust", "Bust! Dealer wins."
    elif dealer_total > 21:
        return "win", "Dealer busts! You win."
    elif player_total == dealer_total:
        return "push", "Push! It's a tie."
    elif player_total > dealer_total:
        return "win", "You win!"
    else:
        return "lose", "Dealer wins."
