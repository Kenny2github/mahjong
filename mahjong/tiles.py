"""Enums and the Tile class."""
from __future__ import annotations
from enum import Enum, IntEnum
from typing import Union

__all__ = [
    'Suit',
    'Simples',
    'Honors',
    'Bonuses',
    'Misc',
    'Wind',
    'Dragon',
    'Flower',
    'Season',
    'ORDER',
    'Number',

    'Tile',
    'BonusTile',
]

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
    FENG = 'feng'  # value is instance of Wind
    LONG = 'long'  # value is instance of Dragon

class Bonuses(Suit):
    """Enum for bonus suits (tiles that only count when you win)"""
    HUA = 'hua'
    GUI = 'gui'

class Misc(Suit):
    """Enum for special case suits"""
    UNKNOWN = '?'
    HIDDEN = 'k'
    MISSING = ' '

class Wind(IntEnum):
    """Represents a wind direction"""
    EAST = 0
    SOUTH = 1
    WEST = 2
    NORTH = 3

class Dragon(IntEnum):
    """Represents a dragon"""
    RED = 0 # hong zhong
    GREEN = 1 # fa cai
    WHITE = 2 # bai ban

class Flower(IntEnum):
    """Represents a Flowers tile"""
    MEI = Wind.EAST
    LAN = Wind.SOUTH
    JU = Wind.WEST
    ZHU = Wind.NORTH

class Season(IntEnum):
    """Represents a Seasons tile"""
    SPRING = Wind.EAST
    SUMMER = Wind.SOUTH
    AUTUMN = Wind.WEST
    WINTER = Wind.NORTH

ORDER = {
    'wan': 0, 'tong': 1, 'zhu': 2,
    'feng': 3, 'long': 4
}

Number = Union[int, Wind, Dragon, Flower, Season]

class Tile:
    """Data class for tiles."""
    suit: Suit
    number: Number

    def __init__(self, suit: Suit, number: Number):
        """Initialize Tile."""
        self.suit = suit
        self.number = number

    @classmethod
    def from_str(cls, s: str) -> Tile:
        """Tile.from_str('suit/number') -> Tile"""
        suit_s, number_s = s.split('/')
        for num in (Simples, Honors, Bonuses, Misc):
            try:
                suit: Suit = num(suit_s)
            except ValueError:
                continue
            else:
                break
        else:
            raise ValueError('Invalid suit')
        number: int = int(number_s) - 1
        if not (0 <= number < 9):
            raise ValueError(f'Number {number_s} not in range [1, 9]')
        if suit == Honors.FENG:
            number = Wind(number)
        if suit == Honors.LONG:
            number = Dragon(number)
        return cls(suit, number)

    def __str__(self) -> str:
        """str(tile) -> 'suit/number'"""
        return f'{self.suit.value}/{self.number}'

    __repr__ = __str__

    def __hash__(self):
        return hash((self.suit, self.number))

    def __eq__(self, other: Tile) -> bool:
        """Tiles are equal when their suits and numbers are equal."""
        if not (isinstance(other, type(self)) or isinstance(self, type(other))):
            return NotImplemented
        return hash(self) == hash(other)

    def __lt__(self, other: Tile) -> bool:
        if not (isinstance(other, type(self)) or isinstance(self, type(other))):
            return NotImplemented
        if self.suit == other.suit:
            return self.number < other.number
        if self.suit.value not in ORDER or other.suit.value not in ORDER:
            return False
        return ORDER[self.suit.value] < ORDER[other.suit.value]

class BonusTile(Tile):
    suit: Bonuses
    number: Union[int, Flower, Season]

    def __init__(self, suit: Bonuses, number: Union[int, Flower, Season]):
        """Initialize Tile."""
        self.suit = suit
        self.number = number
