from typing import List, Tuple
from .tiles import Bonuses, Tile, BonusTile, Wind
from .melds import Meld, WuFlag, faan

class Player:
    """Represents one Mahjong player."""

    seat: Wind
    hand: List[Tile]
    shown: List[Meld]
    bonus: List[BonusTile]

    @property
    def full_hand(self):
        """All tiles in this player's possession, except Bonuses."""
        return sorted(self.hand + [tile for meld in self.shown
                                   for tile in meld.tiles])

    def __init__(self, seat: int):
        self.seat = Wind(seat)
        self.hand = []
        self.shown = []
        self.bonus = []

    def __repr__(self) -> str:
        return f'<Player #{self.seat}: {",".join(map(repr, self.hand))}, '\
            f'shown {self.shown}>'

    __str__ = __repr__

    def draw(self, wall: List[Tile]) -> Tile:
        """Draw a tile from the wall, and keep doing so if it's a Bonus."""
        tile = wall.pop()
        while isinstance(tile, BonusTile):
            self.bonus.append(tile) # Step 21
            self.bonus.sort()
            tile = wall.pop()
        self.hand.append(tile) # Step 20
        return tile

    def show_meld(self, discard: Tile, meld: Meld):
        """Save a meld and remove its tiles from the hand."""
        self.hand.append(discard)
        for tile in meld.tiles:
            self.hand.remove(tile)
        self.shown.append(meld) # Step 19

    def bonus_faan(self) -> Tuple[int, WuFlag]:
        """Get faan won from bonus tiles or lack thereof."""
        flags = WuFlag.CHICKEN_HAND
        if not self.bonus:
            flags |= WuFlag.NO_BONUSES
        found = {
            Bonuses.GUI: [False]*4,
            Bonuses.HUA: [False]*4
        }
        for tile in self.bonus:
            if tile.number == self.seat:
                if tile.suit == Bonuses.HUA:
                    flags |= WuFlag.ALIGNED_FLOWERS
                elif tile.suit == Bonuses.GUI:
                    flags |= WuFlag.ALIGNED_SEASONS
            found[tile.suit][tile.number] = True
        for k, v in found.items():
            if all(v):
                if k == Bonuses.HUA:
                    flags |= WuFlag.TABLE_OF_FLOWERS
                elif k == Bonuses.GUI:
                    flags |= WuFlag.TABLE_OF_SEASONS
        if all(map(all, found.values())):
            flags = WuFlag.HAND_OF_BONUSES
        if WuFlag.TABLE_OF_FLOWERS in flags:
            flags &= ~(WuFlag.ALIGNED_FLOWERS)
        if WuFlag.TABLE_OF_SEASONS in flags:
            flags &= ~(WuFlag.ALIGNED_SEASONS)
        return (faan(flags), flags)