"""Contains classes representing melds that check their validity."""
from __future__ import annotations
from enum import Flag
from itertools import combinations
from typing import Optional, Sequence, Union, Iterable, List, Iterator, TypeVar, Type, Tuple
from .tiles import Honors, Tile, Simples, Bonuses, Misc, Wind

__all__ = [
    'WuFlag',
    'THIRTEEN_ORPHANS',
    'FLAG_FAAN',
    'Meld',
    'Pong',
    'Kong',
    'Chow',
    'Eyes',
    'Wu',
    'faan',
]

class WuFlag(Flag):
    """Possible criteria that a :class:`Wu` may fulfil.

    .. note:: When a flag is implied, its faan may or may not be included.

    Attributes:
        CHICKEN_HAND: The worst type of winning hand. Worth no faan.
        COMMON_HAND: Every :class:`Meld` is a :class:`Chow`.
        ALL_IN_TRIPLETS: Every :class:`Meld` is either a
            :class:`Pong` or :class:`Kong`.
        MIXED_ONE_SUIT: Every :class:`Tile` is an :class:`Honors`
            or from the same suit.
        ALL_ONE_SUIT: Every :class:`Tile` is from the same suit.
        ALL_HONOR_TILES: Every :class:`Tile` is an :class:`Honors`.
        SMALL_DRAGONS: A :class:`Meld` for two :class:`Dragon` types,
            and a pair of :class:`Eyes` for the third.
        GREAT_DRAGONS: A :class:`Meld` for every :class:`Dragon` type.
        SMALL_WINDS: A :class:`Meld` for three :class:`Wind` directions,
            and a pair of :class:`Eyes` for the fourth.
        GREAT_WINDS: A :class:`Meld` for every :class:`Wind` direction.
        NINE_GATES: 1112345678999 plus one more tile, all from one suit.
            :attr:`ALL_ONE_SUIT` is implied.
        ALL_KONGS: Every :class:`Meld` is a :class:`Kong`.
        SELF_TRIPLETS: Every :class:`Meld` is an unrevealed :class:`Pong`.
            :attr:`ALL_IN_TRIPLETS` is implied.
        ORPHANS: Every :class:`Meld` is a :class:`Pong` of ones or nines.
            :attr:`ALL_IN_TRIPLETS` is implied.
        THIRTEEN_ORPHANS: A special case - a one and nine from every suit,
            plus one of every :class:`Honors` tile, plus any other tile.
        SEAT_WIND: A :class:`Meld` is of the winner's seat :class:`Wind`.
        PREVAILING_WIND: A :class:`Meld` is of the prevailing :class:`Wind`.
        RED_DRAGON: A :class:`Meld` is of :attr:`Dragon.RED`.
        GREEN_DRAGON: A :class:`Meld` is of :attr:`Dragon.GREEN`.
        WHITE_DRAGON: A :class:`Meld` is of :attr:`Dragon.WHITE`.
        MIXED_ORPHANS: All tiles are either ones, nines, or :class:`Honors`.
        SELF_DRAW: The winning :class:`Tile` was drawn, not stolen.
        ALL_FROM_WALL: No :class:`Meld` was shown until the end.
        ROBBING_KONG: The winning :class:`Tile` was stolen from
            a :class:`Kong` someone else had declared.
        LAST_CATCH: The winning :class:`Tile` was the last draw or discard.
        BY_KONG: The winning :class:`Tile` was drawn to compensate
            a :class:`Kong`.
        DOUBLE_KONG: The winning :class:`Tile` was drawn to compensate
            a :class:`Kong` formed from a :class:`Tile` that was drawn
            to compensate a :class:`Kong`.
        HEAVENLY: :attr:`~Wind.EAST` :class:`Player` wins without playing.
        EARTHLY: A :class:`Player` other than :attr:`~Wind.EAST`
            wins by stealing their first discard.
        TWELVE_PIECE: When :class:`Player` 2 (for example) steals a tile
            from player 1 to form their 4th :class:`Meld`, and then
            gets to :attr:`SELF_DRAW`, player 1 suffers this penalty.
        GAVE_DRAGON: When :class:`Player` 2 (for example) steals a
            :class:`Dragon` :class:`Tile` from player 1 to form their
            3rd Dragon meld, and then later wins, player 1 suffers this
            penalty. Even if player 3 or 4 discarded the tile that let
            player 2 win, player 1 still suffers the penalty in their place.
        GAVE_KONG: When :class:`Player` 2 (for example) steals a tile from
            player 1 that was previously unseen to form a :class:`Kong`,
            and then wins :attr:`BY_KONG`, player 1 suffers this penalty.
        NO_BONUSES: The :class:`Player` collected zero :class:`Bonuses`.
        ALIGNED_FLOWERS: The :class:`Player` collected a :class:`Flower`
            that aligns with their seat.
        ALIGNED_SEASONS: The :class:`Player` collected a :class:`Season`
            that aligns with their seat.
        TABLE_OF_FLOWERS: The :class:`Player` collected every :class:`Flower`.
        TABLE_OF_SEASONS: The :class:`Player` collected every :class:`Season`.
        HAND_OF_BONUSES: The :class:`Player` collected all :class:`Bonuses`.
            This is an immediate winning hand, regardless of their real tiles.
    """
    CHICKEN_HAND = 0

    # types
    COMMON_HAND = 1 << 0
    ALL_IN_TRIPLETS = 1 << 1
    MIXED_ONE_SUIT = 1 << 2
    ALL_ONE_SUIT = 1 << 3
    ALL_HONOR_TILES = 1 << 4
    SMALL_DRAGONS = 1 << 5
    GREAT_DRAGONS = 1 << 6
    SMALL_WINDS = 1 << 7
    GREAT_WINDS = 1 << 8
    NINE_GATES = 1 << 9
    ALL_KONGS = 1 << 10
    SELF_TRIPLETS = 1 << 11
    ORPHANS = 1 << 12
    THIRTEEN_ORPHANS = 1 << 13

    # presence of certain tiles
    SEAT_WIND = 1 << 14
    PREVAILING_WIND = 1 << 15
    RED_DRAGON = 1 << 16
    GREEN_DRAGON = 1 << 17
    WHITE_DRAGON = 1 << 18
    MIXED_ORPHANS = 1 << 19

    # winning condition
    SELF_DRAW = 1 << 20
    ALL_FROM_WALL = 1 << 21
    ROBBING_KONG = 1 << 22
    LAST_CATCH = 1 << 23
    BY_KONG = 1 << 24
    DOUBLE_KONG = 1 << 25
    HEAVENLY = 1 << 26
    EARTHLY = 1 << 27

    # penalties
    TWELVE_PIECE = 1 << 28
    GAVE_DRAGON = 1 << 29
    GAVE_KONG = 1 << 30

    # bonuses
    NO_BONUSES = 1 << 31
    ALIGNED_FLOWERS = 1 << 32
    ALIGNED_SEASONS = 1 << 33
    TABLE_OF_FLOWERS = 1 << 34
    TABLE_OF_SEASONS = 1 << 35
    HAND_OF_BONUSES = 1 << 36

# special case: 1 & 9 of each suit + every value of honors suits
THIRTEEN_ORPHANS = set(map(Tile.from_str, (
    'tong/1|tong/9|zhu/1|zhu/9|wan/1|wan/9|'  # simples
    'feng/1|feng/2|feng/3|feng/4|long/1|long/2|long/3'  # honors
).split('|')))

FLAG_FAAN = {
    WuFlag.CHICKEN_HAND: 0,
    WuFlag.COMMON_HAND: 1, WuFlag.ALL_IN_TRIPLETS: 3,
    WuFlag.ALL_HONOR_TILES: 10, WuFlag.ALL_ONE_SUIT: 7,
    WuFlag.MIXED_ONE_SUIT: 3, WuFlag.GREAT_DRAGONS: 8,
    WuFlag.SMALL_DRAGONS: 5, WuFlag.GREAT_WINDS: 13,
    WuFlag.SMALL_WINDS: 10, WuFlag.THIRTEEN_ORPHANS: 13,
    WuFlag.ALL_KONGS: 13, WuFlag.SELF_TRIPLETS: 8,
    WuFlag.ORPHANS: 10, WuFlag.NINE_GATES: 10,
    WuFlag.RED_DRAGON: 1, WuFlag.GREAT_WINDS: 1,
    WuFlag.WHITE_DRAGON: 1, WuFlag.SEAT_WIND: 1,
    WuFlag.PREVAILING_WIND: 1, WuFlag.MIXED_ORPHANS: 1,
    WuFlag.SELF_DRAW: 1, WuFlag.ALL_FROM_WALL: 1,
    WuFlag.ROBBING_KONG: 1, WuFlag.LAST_CATCH: 1,
    WuFlag.BY_KONG: 1, WuFlag.DOUBLE_KONG: 8,
    WuFlag.HEAVENLY: 13, WuFlag.EARTHLY: 13,
    WuFlag.TWELVE_PIECE: 0, WuFlag.GAVE_DRAGON: 0, WuFlag.GAVE_KONG: 0,
    WuFlag.NO_BONUSES: 1, WuFlag.ALIGNED_FLOWERS: 1,
    WuFlag.ALIGNED_SEASONS: 1, WuFlag.TABLE_OF_FLOWERS: 2,
    WuFlag.TABLE_OF_SEASONS: 2, WuFlag.HAND_OF_BONUSES: 8,
}

def _tname(obj) -> str:
    return type(obj).__name__

T = TypeVar('T', bound='Meld')

class Meld:
    """Represents a meld of tiles."""

    @property
    def size(self) -> Union[int, range]:
        """Valid size of this meld."""
        raise NotImplementedError

    tiles: Tuple[Tile, ...]

    def __init__(self, tiles: Iterable[Tile]):
        """Check validity upon initialization."""
        self.tiles = tuple(sorted(tiles))
        self.check_meld()

    @classmethod
    def from_str(cls: Type[T], s: str) -> T:
        """Meld.from_str('suit1/num1|...') -> Meld"""
        return cls(map(Tile.from_str, s.split('|')))

    def __str__(self) -> str:
        """str(meld) -> 'suit1/num1|suit2/num2|...'"""
        tiles = list(self.tiles)
        if isinstance(self, Wu):
            for meld in self.fixed_melds:
                tiles.extend(meld.tiles)
        tiles.sort()
        return '|'.join(map(str, tiles))

    __repr__ = __str__

    def __hash__(self) -> int:
        return hash((type(self),) + self.tiles)

    def __eq__(self, other: Meld) -> bool:
        """Two Melds are equal if they are same type and same tiles."""
        if not isinstance(other, Meld):
            return NotImplemented
        return hash(self) == hash(other)

    def __lt__(self, other: Meld) -> bool:
        order = [Wu, Kong, Pong, Chow, Eyes]
        if type(self) is not type(other):
            return order.index(type(self)) > order.index(type(other))
        return self.tiles < other.tiles

    def check_meld(self) -> None:
        """Check validity of the meld. Raises ValueError upon failure."""
        self.check_size()
        for tile in self.tiles:
            if isinstance(tile.suit, Bonuses):
                raise ValueError('No Bonus tiles in a meld')

    def check_size(self) -> None:
        """Check that the meld is the right size."""
        if isinstance(self.size, range) and isinstance(self, Wu):
            size = len(self.all_tiles)
            if size not in self.size:
                start, stop = self.size.start, self.size.stop
                raise ValueError(f'{_tname(self)} must be '
                                 f'[{start},{stop}) tiles, '
                                 f'you have {len(self.tiles)}: {self.tiles}')
        else:
            if len(self.tiles) != self.size:
                raise ValueError(f'{_tname(self)} must be {self.size} tiles, '
                                 f'you have {len(self.tiles)}: {self.tiles}')

    def check_suit(self) -> None:
        """Check that all tiles are the same suit."""
        suit = self.tiles[0].suit
        for tile in self.tiles[1:]:
            if tile.suit != suit:
                raise ValueError(
                    f'{_tname(self)} must be all one suit: '
                    f'{suit} != {tile.suit}'
                )

class _SameNum(Meld):
    """Base class that provides check_num method."""

    def check_meld(self) -> None:
        """Check validity of the meld."""
        super().check_meld()
        self.check_num()

    def check_num(self) -> None:
        """Check that all tiles are the same number/value."""
        self.check_suit()
        num = self.tiles[0].number
        for tile in self.tiles[1:]:
            if tile.number != num:
                raise ValueError(
                    f'{_tname(self)}s must be the same tile: '
                    f'{num} != {tile.number}'
                )

class Pong(_SameNum):
    """Represents a Pong (three identical tiles)"""

    size: int = 3

class Kong(_SameNum):
    """Represents a Kong (four identical tiles, counted as three)"""

    size: int = 4

    def __str__(self) -> str:
        """Kongs are represented by one faceup, two stacked down, one faceup"""
        return '|'.join(map(str, [
            self.tiles[0], Misc.HIDDEN.value, self.tiles[-1]]))

class Chow(Meld):
    """Represents a Chow (three tiles of the same suit with consecutive numbers)"""

    size: int = 3

    def check_meld(self) -> None:
        """Check validity as a Chow."""
        super().check_meld()
        self.check_suit()
        if not isinstance(self.tiles[0].suit, Simples):
            raise ValueError(
                f'Chows can only be Simples, not {_tname(self.tiles[0].suit)}')
        num = self.tiles[0].number
        for i, tile in enumerate(self.tiles):
            if tile.number != num + i:
                raise ValueError('Chows must have consecutive numbers: '
                                 f'{tile.number} != {num + i}')

class Eyes(_SameNum):
    """Represents a pair of Eyes (two identical tiles, only valid in winning hand)"""

    size: int = 2

class Wu(Meld):
    """Represents a winning hand. This can only consist of sub-melds.

    .. warning::

        For some hands, instantiating this class is NOT atomic.
        So far I have discovered hands that take a full second or two.
        Consider instantiating this class a blocking procedure, and
        treat it as such, e.g. in asynchronous contexts.
    """

    size: range = range(14, 19) # [14, 18]
    melds: List[List[Meld]]
    fixed_melds: List[Meld]
    arrived: Optional[Tile]
    discarder: Optional[Wind]
    base_flags: WuFlag

    @property
    def all_tiles(self) -> List[Tile]:
        tiles = list(self.tiles)
        for meld in self.fixed_melds:
            tiles.extend(meld.tiles)
        tiles.sort()
        return tiles

    def __init__(self, tiles: Iterable[Tile],
                 melds: Optional[Iterable[Meld]] = None,
                 arrived: Optional[Tile] = None,
                 discarder: Optional[int] = None,
                 flags: WuFlag = WuFlag.CHICKEN_HAND):
        """Check validity upon initialization."""
        self.tiles = tuple(sorted(tiles))
        self.fixed_melds = list(melds or [])
        self.arrived = arrived
        self.discarder = Wind(discarder) if discarder is not None else None
        self.base_flags = flags
        self.check_meld()

    @classmethod
    def from_str(cls: Type[Wu], s: str, *a, **kw) -> Wu:
        """Wu.from_str('suit1/num1|...') -> Wu"""
        return cls(map(Tile.from_str, s.split('|')), *a, *kw)

    def check_meld(self) -> None:
        """Check that this hand is a winning hand.
        Returns all possible winning combinations.
        """
        super().check_meld()
        # sort each combo of melds, to make out-of-order duplicates
        # equal, then pass them through a set to weed them out
        self.melds = list(map(list, {
            tuple(sorted(combo)) for combo in self.valid_combos()}))
        if not self.melds:
            raise ValueError('No valid combos')

    def valid_combos(self) -> Iterator[List[Meld]]:
        """Yield all possible winning sets of melds."""
        tc = len(self.tiles)
        len_ts = tc - 2 # tile count minus eyes
        checked = set()
        for e1, e2 in combinations(range(tc), 2):
            if e1 == e2:
                continue
            try:
                test_eyes = Eyes((self.tiles[e1], self.tiles[e2]))
            except ValueError:
                continue
            if test_eyes in checked:
                continue
            checked.add(test_eyes)
            # tiles other than the eyes we're checking
            ts = [x for i, x in enumerate(self.tiles) if i != e1 and i != e2]
            possible = self.all_melds_pos(ts)
            combos = combinations(possible, 4 - len(self.fixed_melds))
            for combo in combos:
                # Try to find two melds using the same index.
                # The naive way I was previously using was to
                # slam all the indexes into a set and check its length.
                # However, when we're dealing with over a million combos,
                # that gets expensive. Instead, manually loop until we
                # find a single duplicate, at which point we skip immediately.
                covered = set()
                found_dupe = False
                for _, idxs in combo:
                    for i in idxs:
                        if i in covered:
                            found_dupe = True
                            break
                        covered.add(i)
                    if found_dupe:
                        break
                if found_dupe:
                    # can't have duplicate indexes, skip this combo
                    continue
                covered = [tile for meld, idxs in combo for tile in meld.tiles]
                if len(covered) != len_ts:
                    continue
                melds = [meld for meld, idxs in combo] + list(self.fixed_melds)
                melds.append(test_eyes)
                yield melds
        if set(self.tiles) == THIRTEEN_ORPHANS:
            melds: List[Meld] = [_UncheckedWu(self.tiles)]
            yield melds

    @staticmethod
    def get_triplet(trip: List[Tile]) -> Union[Meld, None]:
        """Try to get a meld."""
        try:
            return Pong(trip)
        except ValueError:
            pass
        try:
            return Chow(trip)
        except ValueError:
            pass
        return None

    def all_melds_pos(self, ts) -> List[Tuple[Meld, Tuple[int, int, int]]]:
        """Get every possible meld and the indexes of their component cards.
        Modified from
        https://github.com/offe/py-mcr/blob/master/mahjonggrouping.py#L108-L121
        """
        trips = {}
        tc = len(ts)
        for t1, t2, t3 in combinations(range(tc), 3):
            t1, t2, t3 = trip_idxs = tuple(sorted((t1, t2, t3)))
            # already checked
            if trip_idxs in trips:
                continue
            # not unique indexes
            if len(set(trip_idxs)) != 3:
                continue
            trip = [ts[i] for i in trip_idxs]
            meld = self.get_triplet(trip)
            if isinstance(meld, Pong) and t3 < tc - 1:
                old_idxs = trip_idxs
                old_meld = meld
                for t4 in range(t3 + 1, tc):
                    trip_idxs = tuple(sorted((t1, t2, t3, t4)))
                    if trip_idxs in trips or len(set(trip_idxs)) != 4:
                        continue
                    trip = [ts[i] for i in trip_idxs]
                    try:
                        meld = Kong(trip)
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    trip_idxs = old_idxs
                    meld = old_meld
            if meld:
                trips[trip_idxs] = meld
        return sorted((i, j) for j, i in trips.items())

    def flags(self, choice: Sequence[Meld],
             winds: Optional[Tuple[int, int]] = None) -> WuFlag:
        """WuFlags that apply to this choice of winning hand."""
        all_tiles = self.all_tiles
        types = self.base_flags
        if all(isinstance(meld, (Chow, Eyes)) for meld in choice):
            types |= WuFlag.COMMON_HAND
        if all(isinstance(meld, (Pong, Kong, Eyes)) for meld in choice):
            types |= WuFlag.ALL_IN_TRIPLETS
        suit = None
        hon = False
        all_one_suit = False
        for tile in all_tiles:
            if isinstance(tile.suit, Honors):
                hon = True
                continue
            if suit is not None and tile.suit != suit:
                break
            suit = tile.suit
        else:
            if hon and suit is None:
                # no regulars, only honors
                types |= WuFlag.ALL_HONOR_TILES
            elif not hon:
                # no honors, only regulars
                types |= WuFlag.ALL_ONE_SUIT
            else:
                # regulars (but of one suit) and honors
                types |= WuFlag.MIXED_ONE_SUIT
        long: List[Optional[type]] = [None, None, None]
        for meld in choice:
            if isinstance(meld, Chow):
                continue # can't be dragons
            if meld.tiles[0].suit != Honors.LONG:
                continue # not dragons
            long[meld.tiles[0].number] = type(meld)
        if all(long):
            if not any(typ is Eyes for typ in long):
                types |= WuFlag.GREAT_DRAGONS
            else:
                types |= WuFlag.SMALL_DRAGONS
        feng: List[Optional[type]] = [None, None, None, None]
        for meld in choice:
            if isinstance(meld, Chow):
                continue # can't be winds
            if meld.tiles[0].suit != Honors.FENG:
                continue # not winds
            feng[meld.tiles[0].number] = type(meld)
        if all(feng):
            if not any(typ is Eyes for typ in feng):
                types |= WuFlag.GREAT_WINDS
            else:
                types |= WuFlag.SMALL_WINDS
        if len(choice) == 1: # only one possible way this can happen
            types |= WuFlag.THIRTEEN_ORPHANS
        if all(isinstance(meld, (Kong, Eyes)) for meld in choice):
            types |= WuFlag.ALL_KONGS
        if not self.fixed_melds and WuFlag.ALL_IN_TRIPLETS in types:
            if WuFlag.SELF_DRAW in types or ( # self draw or
                self.arrived is not None
                # stolen discard not in regular melds,
                and all(self.arrived not in meld.tiles
                        for meld in choice
                        if not isinstance(meld, Eyes))
                # only eyes
                and all(self.arrived in meld.tiles
                        for meld in choice
                        if isinstance(meld, Eyes))
            ):
                types |= WuFlag.SELF_TRIPLETS
        for meld in choice:
            if isinstance(meld, Chow):
                break
            if not isinstance(meld.tiles[0].suit, Simples):
                break
            if meld.tiles[0].number not in {0, 8}:
                break
        else:
            types |= WuFlag.ORPHANS
        counts = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        goals = [3, 1, 1, 1, 1, 1, 1, 1, 3]
        suit = all_tiles[0].suit
        if all_one_suit and isinstance(suit, Simples):
            for tile in all_tiles:
                counts[tile.number] += 1
            diff = 0
            for i in range(9):
                if counts[i] == goals[i]:
                    continue
                if counts[i] == goals[i] + 1:
                    diff += 1
                    continue
                break
            else:
                if diff == 1:
                    types |= WuFlag.NINE_GATES
        favorable = list({
            'long/1': WuFlag.RED_DRAGON,
            'long/2': WuFlag.GREEN_DRAGON,
            'long/3': WuFlag.WHITE_DRAGON
        }.items())
        if winds is not None:
            favorable.append((f'feng/{winds[0]+1}', WuFlag.SEAT_WIND))
            favorable.append((f'feng/{winds[1]+1}', WuFlag.PREVAILING_WIND))
        for meld in choice:
            for s, flag in favorable:
                if meld.tiles[0] == Tile.from_str(s):
                    types |= flag
        for tile in all_tiles:
            if isinstance(tile.suit, Honors):
                continue
            if tile.number in {0, 8}:
                continue
            break
        else:
            types |= WuFlag.MIXED_ORPHANS
        if not self.fixed_melds:
            types |= WuFlag.ALL_FROM_WALL
        # unset flags
        if WuFlag.SMALL_WINDS in types:
            types &= ~(WuFlag.SEAT_WIND | WuFlag.PREVAILING_WIND)
        if WuFlag.SELF_TRIPLETS in types:
            types &= ~(WuFlag.ALL_FROM_WALL | WuFlag.ALL_IN_TRIPLETS)
        if WuFlag.ALL_HONOR_TILES in types:
            types &= ~(WuFlag.ALL_IN_TRIPLETS)
        if WuFlag.ORPHANS in types:
            types &= ~(WuFlag.ALL_IN_TRIPLETS)
        if WuFlag.NINE_GATES in types:
            types &= ~(WuFlag.ALL_ONE_SUIT | WuFlag.ALL_FROM_WALL)
        if WuFlag.THIRTEEN_ORPHANS in types:
            types &= ~(WuFlag.MIXED_ORPHANS | WuFlag.ORPHANS)
        return types

    def faan(self, choice: Sequence[Meld],
             winds: Optional[Tuple[int, int]] = None) -> Tuple[int, WuFlag]:
        """Number of faan points the Wu is worth.

        Args:
            choice: Which combination of melds from the possible
                set to calculate the points for.
            winds: If specified as ``(seat, prevailing)``, this provides the
                necessary context to include the Seat Wind and Prevailing Wind
                Wu flags.

        Returns:
            ``(points, flags)`` - flags represents all of the features of a Wu
            that are true for this particular combination.
        """
        types = self.flags(choice, winds)
        return (faan(types), types)

    def max_faan(self, winds: Optional[Tuple[int, int]] = None
                 ) -> Tuple[List[Meld], int, WuFlag]:
        return max(
            ((choice, *self.faan(choice, winds)) for choice in self.melds),
            key=lambda trip: trip[1])

def faan(flags: WuFlag) -> int:
    points = 0
    for flag in WuFlag:
        if flag in flags:
            points += FLAG_FAAN[flag]
    return points

class _UncheckedWu(Wu):
    size: int = 14

    def __init__(
        self, tiles: Iterable[Tile],
        melds: Optional[Iterable[Meld]] = None, *_, **__
    ):
        """Don't check validity, that's the whole point"""
        self.tiles = tuple(sorted(tiles)) + tuple(
            tile for meld in (melds or []) for tile in meld.tiles)
        self.fixed_melds = []

if 0:
    # NOTE: An example of the non-atomicity of Wu() is the following:
    # 1.25s (3.94s when debug): tong/1|tong/1|tong/1|tong/2|tong/2|tong/2|tong/3|tong/3|tong/3|tong/4|tong/4|tong/4|tong/5|tong/5
    # Note that fixing even one meld reduces it to atomic:
    # 0.02s: tong/1|tong/1|tong/1 + tong/2|tong/2|tong/2|tong/3|tong/3|tong/3|tong/4|tong/4|tong/4|tong/5|tong/5
    # This happens because there's no way around the fact that:
    # 1. There are 5 ways to make eyes (a pair of 1s, 2s, 3s, 4s, or 5s)
    # 2. For each of those choices of eyes, there are 58, 45, 27, 39, and 57 different ways to form melds
    # 3. We have to check the validity of every choice of 4 melds out of those numerous ways, since no melds are fixed
    # 4. 58C4 + 45C4 + 27C4 + 39C4 + 57C4 = 1,068,076 which is enough to make a real difference in Python
    # Other timing tests follow
    # 0.00s: tong/1|tong/9|zhu/1|zhu/9|wan/1|wan/9|feng/1|feng/2|feng/3|feng/4|long/1|long/2|long/3|wan/2
    # 0.08s: wan/1|wan/1|wan/1|wan/2|wan/3|wan/4|wan/4|wan/5|wan/6|wan/7|wan/8|wan/9|wan/9|wan/9
    # 0.18s: tong/1|tong/2|tong/3|tong/2|tong/3|tong/4|tong/5|tong/6|tong/7|tong/8|tong/8|tong/8|tong/4|tong/4
    # 0.32s: feng/1|feng/1|feng/1|feng/1|feng/2|feng/2|feng/2|feng/2|feng/3|feng/3|feng/3|feng/3|feng/4|feng/4|feng/4|feng/4|long/1|long/1
    # 0.17s: tong/1|tong/1|tong/1|wan/9|wan/9|wan/9|zhu/5|zhu/5|zhu/5|tong/2|tong/2|tong/2|long/1|long/1
    # 0.00s: zhu/3|zhu/4|zhu/5,zhu/5|zhu/6|zhu/7,zhu/7|zhu/8|zhu/9 + feng/3|feng/3|zhu/4|zhu/5|zhu/6
    # 0.55s: wan/2|wan/2|wan/2|tong/1|tong/1|tong/1|tong/1|tong/2|tong/3|tong/2|tong/2|tong/2|tong/3|tong/3
    pass
