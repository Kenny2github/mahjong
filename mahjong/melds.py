"""Contains the Meld class and its subclasses."""

from .tiles import Simples

class Meld:
    """Represents a single meld of tiles."""

    size = 0 # size of the meld

    def __init__(self, tiles):
        """Initialize the meld with its tiles and check validity."""
        self.tiles = tiles
        self.tiles.sort()
        self.check_meld()

    def __str__(self):
        """str(meld) -> 'suit1/num1|suit2/num2|...'"""
        return '|'.join(map(str, self.tiles))
    __repr__ = __str__

    def check_meld(self):
        """Check validity of the meld. Raises ValueError upon failure."""
        raise NotImplementedError

    def check_suit(self):
        """Ensures all tiles are the same suit."""
        suit = None
        for tile in self.tiles:
            if suit is not None and tile.suit != suit:
                raise ValueError(
                    f'{type(self).__name__}s must be one suit: '
                    f'{suit} != {tile.suit}'
                )
            suit = tile.suit

class _SameNum(Meld):
    """Base class that provides check_num method."""
    def check_meld(self):
        """Check validity of the same-numbered meld."""
        self.check_num()

    def check_num(self):
        """Ensures all tiles are the same number/value."""
        self.check_suit()
        num = None
        for tile in self.tiles:
            if num is not None and tile.number != num:
                raise ValueError(
                    f'{type(self).__name__}s must be all the same tile: '
                    f'{num} != {tile.number}'
                )
            num = tile.number

class Pong(_SameNum):
    """Represents a Pong meld (three identical tiles)"""

    size = 3

    def check_meld(self):
        """Check validity as a Pong."""
        if len(self.tiles) != self.size:
            raise ValueError(f'Pongs must be {self.size} tiles')
        self.check_num()

class Kong(_SameNum):
    """Represents a Kong meld (four identical tiles, counted as three)"""

    size = 4

    def check_meld(self):
        """Check validity as a Kong."""
        if len(self.tiles) != self.size:
            raise ValueError(f'Kongs must be {self.size} tiles')
        self.check_num()

    def __str__(self):
        """Kongs are represented by one faceup, two stacked down, one up"""
        return '|'.join(map(str, [self.tiles[0], 'k', self.tiles[-1]]))

class Chow(Meld):
    """Represents a Chow meld (three tiles of the same suit with consecutive numbers)"""

    size = 3

    def check_meld(self):
        """Check validity as a Chow."""
        if len(self.tiles) != self.size:
            raise ValueError(f'Chows must be {self.size} tiles')
        for tile in self.tiles:
            if not isinstance(tile.suit, Simples):
                raise ValueError(
                    'Chows must be Simples only, '
                    f'not {type(tile.suit).__name__}'
                )
        self.check_suit()
        num = None
        for tile in self.tiles:
            if num is not None and tile.number != num + 1:
                raise ValueError(
                    'Chows must be tiles with consecutive numbers: '
                    f'{tile.number} != {num} + 1'
                )
            num = tile.number

class Eyes(_SameNum):
    """Represents an Eyes meld (two identical tiles), used only in winning hand)"""

    size = 2

    def check_meld(self):
        """Check validity as an Eyes."""
        if len(self.tiles) != self.size:
            raise ValueError(f'Eyes must be {self.size} tiles')
        self.check_num()
