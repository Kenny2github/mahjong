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
    FENG = 'feng' # 0 = east, 1 = south, 2 = west, 3 = north
    LONG = 'long' # 0 = hong zhong, 1 = fa cai, 2 = bai ban

class Bonuses(Suit):
    """Enum for bonus suits (tiles that only count when you win)"""
    HUA = 'hua'
    GUI = 'gui'

class Misc(Suit):
    """Enum for special case suits"""
    UNKNOWN = '?'
    HIDDEN = 'k'
    MISSING = ' '

ORDER = {
    'wan': 0, 'tong': 1, 'zhu': 2,
    'feng': 3, 'long': 4
}

class Tile:
    """Data class for tiles."""
    suit: Suit
    number: int

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
        return ORDER[self.suit.value] < ORDER[other.suit.value]
