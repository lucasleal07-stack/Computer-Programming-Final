"""Card representations and deck management for Blackjack."""

import random
from typing import List
from enum import Enum


class Suit(Enum):
    """Card suits (Unicode symbols)."""
    HEARTS = ("♥", "H")
    DIAMONDS = ("♦", "D")
    CLUBS = ("♣", "C")
    SPADES = ("♠", "S")


class Rank(Enum):
    """Card ranks with display name and blackjack value.
    
    Format: (display_string, base_value)
    - Numbers 2-10: face value
    - Face cards (J, Q, K): 10
    - Ace: 11 (can convert to 1 in hand_logic)
    """
    TWO = ("2", 2)
    THREE = ("3", 3)
    FOUR = ("4", 4)
    FIVE = ("5", 5)
    SIX = ("6", 6)
    SEVEN = ("7", 7)
    EIGHT = ("8", 8)
    NINE = ("9", 9)
    TEN = ("10", 10)
    JACK = ("J", 10)
    QUEEN = ("Q", 10)
    KING = ("K", 10)
    ACE = ("A", 11)

    def __init__(self, display, base_value):
        self.display = display
        self.base_value = base_value


class Card:
    """Single playing card with suit and rank."""

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def __str__(self) -> str:
        """Returns card string (e.g., 'A♥', '10♦')."""
        return f"{self.rank.display}{self.suit.value}"

    def get_value(self, allow_ace_as_one: bool = False) -> int:
        """Return card value. Aces default to 11, or 1 if allow_ace_as_one=True."""
        if self.rank == Rank.ACE and allow_ace_as_one:
            return 1
        return self.rank.base_value
    def image_key(self) -> str:
        '''returns the image key so that it can pull the assigned png 
        examples AH, AS ect.'''
        # File names use rank + suit short (e.g., 'AH', '10D', 'QS')
        rank = self.rank.display
        # Suit value is stored as a tuple (symbol, short) => ('♥','H')
        suit_short = self.suit.value[1]
        return f"{rank}{suit_short}"



class Deck:
    """Standard 52-card deck with shuffle and deal operations."""

    def __init__(self):
        self.cards: List[Card] = []
        self._build()

    def _build(self):
        """Build complete 52-card deck (4 suits × 13 ranks)."""
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        """Randomize card order."""
        random.shuffle(self.cards)

    def deal(self) -> Card:
        """Deal a card from the top of the deck.
        
        Raises ValueError if deck is empty (reshuffle handled in game.py).
        """
        if not self.cards:
            raise ValueError("Deck is empty")
        return self.cards.pop()

    def remaining(self) -> int:
        """Return number of cards left in deck."""
        return len(self.cards)
