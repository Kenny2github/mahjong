"""Contains suit enums and the Tile class."""

from enum import Enum

class Suit(Enum):
    """Base enum class for suits."""
    pass

class Simples(Suit):
    """Enum for simples suits (numbered from 1-9)"""
    ZHU = 'zhu'
    TONG = 'tong'
    WAN = 'wan'

class Honors(Suit):
    """Enum for honors suits (tiles that cannot Chow)"""
    FENG = 'feng'
    LONG = 'long'

class Bonuses(Suit):
    """Enum for bonus suits (tiles that only count when you win)"""
    HUA = 'hua'
    GUI = 'gui'

class Tile:
    """Data class for tiles."""

    def __init__(self, suit, number):
        """Initialize data"""
        self.suit = suit
        self.number = number

    def __str__(self):
        """str(tile) -> 'suit/number'"""
        return f'{self.suit.value}/{self.number}'
    __repr__ = __str__

    def __eq__(self, other):
        """Tiles are equal when their suits and numbers are equal."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.suit == other.suit and self.number == other.number

    def __lt__(self, other):
        """Tiles are sorted by suit before number."""
        if not isinstance(other, type(self)):
            return NotImplemented
        if self.suit == other.suit:
            return self.number < other.number
        # note: this does indeed mean that suit sorting is arbitrary
        # however the important part is the grouping
        return self.suit.value < other.suit.value
