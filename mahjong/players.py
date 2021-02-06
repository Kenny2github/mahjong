from typing import List
from .tiles import Bonuses, Tile, BonusTile, Wind
from .melds import Meld

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

    def bonus_faan(self) -> int:
        """Get faan won from bonus tiles or lack thereof."""
        points = 0
        if not self.bonus:
            points += 1 # :(
        found = {
            Bonuses.GUI: [False]*4,
            Bonuses.HUA: [False]*4
        }
        for tile in self.bonus:
            if tile.number == self.seat:
                points += 1
            found[tile.suit][tile.number] = True
        for v in found.values():
            if all(v):
                points += 1
        if all(map(all, found.values())):
            points += 8
        return points