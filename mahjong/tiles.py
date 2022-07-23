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
    """Enum for simples suits (numbered from 1-9).

    Attributes:
        ZHU: 竹 - Bamboo
        TONG: 銅 - Bronze/Dots
        WAN: 萬 - Myriad/Characters
    """
    ZHU = 'zhu'
    TONG = 'tong'
    WAN = 'wan'

class Honors(Suit):
    """Enum for honors suits (tiles that cannot :class:`Chow`).

    Attributes:
        FENG: 風 - :class:`Wind`
        LONG: 龍 - :class:`Dragon`
    """
    FENG = 'feng'  # value is instance of Wind
    LONG = 'long'  # value is instance of Dragon

class Bonuses(Suit):
    """Enum for bonus suits (tiles that only count when you win).

    Attributes:
        HUA: 花 - :class:`Flower`
        GUI: 季 - :class:`Season` (wrong pinyin but too late to change it)
    """
    HUA = 'hua'
    GUI = 'gui'

class Misc(Suit):
    """Enum for special case suits.

    Attributes:
        UNKNOWN: Mystery suit.
        HIDDEN: Hidden in a :class:`Kong` display.
        MISSING: No tile here.
    """
    UNKNOWN = '?'
    HIDDEN = 'k'
    MISSING = ' '

class Wind(IntEnum):
    """Represents a wind direction.

    Attributes:
        EAST: 東 - First wind.
        SOUTH: 南 - Second wind.
        WEST: 西 - Third wind.
        NORTH: 北 - Fourth wind.
    """
    EAST = 0
    SOUTH = 1
    WEST = 2
    NORTH = 3

class Dragon(IntEnum):
    """Represents a dragon.

    Attributes:
        RED: 紅中
        GREEN: 發財
        WHITE: 白板
    """
    RED = 0 # hong zhong
    GREEN = 1 # fa cai
    WHITE = 2 # bai ban

class Flower(IntEnum):
    """Represents a Flowers tile.

    Attributes:
        MEI: 梅 - Plum blossom - first flower
        LAN: 蘭 - Orchid - second flower
        JU: 菊 - Chrysanthemum - third flower
        ZHU: 竹 - Bamboo - fourth flower
    """
    MEI = Wind.EAST.value
    LAN = Wind.SOUTH.value
    JU = Wind.WEST.value
    ZHU = Wind.NORTH.value

class Season(IntEnum):
    """Represents a Seasons tile.

    Attributes:
        SPRING: 春 - First season
        SUMMER: 夏 - Second season
        AUTUMN: 秋 - Third season
        WINTER: 冬 - Fourth season
    """
    SPRING = Wind.EAST.value
    SUMMER = Wind.SOUTH.value
    AUTUMN = Wind.WEST.value
    WINTER = Wind.NORTH.value

ORDER = {
    'wan': 0, 'tong': 1, 'zhu': 2,
    'feng': 3, 'long': 4
}

Number = Union[int, Wind, Dragon]

class Tile:
    """Data class for tiles."""
    suit: Suit
    number: Number

    def __init__(self, suit: Suit, number: Number):
        """Initialize Tile."""
        self.suit = suit
        self.number = number
        if isinstance(suit, Simples):
            max_num = 9
        else:
            max_num = 4
        if not (0 <= number < max_num):
            raise ValueError(f'Number {number+1} not in range [1, {max_num}]')
        if isinstance(self.suit, Simples):
            self.number = int(number)
        elif self.suit == Honors.FENG:
            self.number = Wind(number)
        elif self.suit == Honors.LONG:
            self.number = Dragon(number)
        elif self.suit in Bonuses:
            raise ValueError('Please use the BonusTile class for bonus tiles.')
        else:
            raise ValueError(f'Invalid suit: {self.suit!r}')

    @classmethod
    def from_str(cls, s: str) -> Union[Tile, BonusTile]:
        """Tile.from_str('suit/number') -> Tile | BonusTile"""
        suit_s, number_s = s.split('/')
        suit: Suit = Misc.UNKNOWN
        for num in (Simples, Honors, Bonuses, Misc):
            try:
                suit = num(suit_s)
            except ValueError:
                continue
            else:
                break
        else:
            raise ValueError('Invalid suit')
        number: int = int(number_s) - 1
        # number checking and casting is done by constructors
        if isinstance(suit, Bonuses):
            return BonusTile(suit, number)
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
        if self.suit == Bonuses.HUA:
            self.number = Flower(number)
        elif self.suit == Bonuses.GUI:
            self.number = Season(number)
        else:
            raise ValueError(f'Invalid BonusTile suit: {self.suit!r}')
