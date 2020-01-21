"""
Mahjong
-------

Abstract away the logic of mahjong games (for oh, it is complicated!)
Only worry about the representation.

Example Usage
=============

.. code-block:: python
    >>> game = mahjong.Game()
"""
import random
from enum import Enum

__version__ = "0.0.1"

PLAYERS = 4
HANDSIZE = 13

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

class Meld:
    """Represents a single meld of tiles."""
    def __init__(self, tiles):
        """Initialize the meld with its tiles and check validity."""
        self.tiles = tiles
        self.check_meld()

    def __str__(self):
        """str(meld) -> 'suit1/num1|suit2/num2|...'"""
        return '|'.join(map(str, self.tiles))
    __repr__ = __str__

    def check_meld(self):
        """Check validity of the meld. Raises ValueError upon failrue."""
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
    def check_meld(self):
        """Check validity as a Pong."""
        if len(self.tiles) != 3:
            raise ValueError('Pongs must be 3 tiles')
        self.check_num()

class Kong(_SameNum):
    """Represents a Kong meld (four identical tiles, counted as three)"""
    def check_meld(self):
        """Check validity as a Kong."""
        if len(self.tiles) != 4:
            raise ValueError('Kongs must be 4 tiles')
        self.check_num()

    def __str__(self):
        """Kongs are represented by one faceup, two stacked down, one up"""
        return '|'.join(map(str, [self.tiles[0], 'k', self.tiles[-1]]))

class Chow(Meld):
    """Represents a Chow meld (three tiles of the same suit with consecutive numbers)"""
    def check_meld(self):
        """Check validity as a Chow."""
        if len(self.tiles) != 3:
            raise ValueError('Chows must be 3 tiles')
        for tile in self.tiles:
            if not isinstance(tile.suit, Simples):
                raise ValueError(
                    'Chows must be Simples only, '
                    f'not {type(tile.suit).__name__}'
                )
        self.check_suit()
        self.tiles.sort()
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
    def check_meld(self):
        """Check validity as an Eyes."""
        if len(self.tiles) != 2:
            raise ValueError('Eyes must be 2 tiles')
        self.check_num()

class Player:
    """Represents operations on a specific player."""

    # pid/seat = 0 => initial east
    # pid/seat = 1 => initial south
    # pid/seat = 2 => initial west
    # pid/seat = 3 => initial north
    pid = seat = 0
    hand = shown = bonus = []
    draw = None

    def __init__(self, pid, root):
        self.pid = self.seat = pid
        self._root = root
        self.hand = []
        self.shown = []
        self.bonus = []

    def draw_starting_hand(self, wall):
        """Draw the starting 13 (or 14) tiles from the wall."""
        self.hand = wall[:HANDSIZE] #True == 1
        del wall[:HANDSIZE]
        self.hand.sort()
        if self.seat == 0:
            self.draw = wall.pop(0)

    def handle_bonuses(self, wall):
        """Handle bonus tiles.
        Move them to self.bonus and draw replacement tiles from the wall.
        """
        i = 0
        while i < HANDSIZE:
            if isinstance(self.hand[i].suit, Bonuses):
                # remove bonus from hand
                self.bonus.append(self.hand[i])
                del self.hand[i]
                # replenish hand with new tile from wall
                self.hand.append(wall.pop())
            i += 1

    #pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def won(self, _hand=None):
        """Check if this player has won with their current hand.
        If they have, returns number of points the hand is worth (not including
        winning condition points).
        If not, returns False.
        Note: if _hand is specified, self is ignored.
        """
        hand = _hand or self.hand[:]
        if len(hand) < 14: # winning is at least 14, at most 16
            return False
        shown = [] if _hand is not None else self.shown[:]
        hand = hand + shown
        shown = []
        hand.sort()
        # split hand into simples and non-simples,
        # because there's some optimization that can
        # be done on non-simples
        simples = [t for t in hand if isinstance(t.suit, Simples)]
        others = [t for t in hand if not isinstance(t.suit, Simples)]
        print(simples, others)
        eyes_checked = len(hand) == 16 # 16 tiles can only be four Kongs
        # Backtracking algorithm modified from https://stackoverflow.com/a/4941711/6605349
        winning = [] # indexes of winning tiles
        _shown = []
        def backtrack(i=0, chowq=True):
            nonlocal eyes_checked
            _winning = [bunch[j] for j in winning if 0 <= j < len(bunch)]
            _losing = [bunch[j] for j in range(len(bunch)) if j not in winning]
            print('tracking into', i, '\n winning:', _winning, '\n losing:', _losing)
            slen = len(bunch)
            if all(idx in winning for idx in range(slen)):
                print('bubbling')
                return True # bubble up
            while i < slen - 1: # slen - eyelen + 1
                if i in winning: # don't look at winning tiles
                    i += 1
                    continue
                try:
                    _shown.append(Kong(bunch[i:i+4]))
                except ValueError:
                    pass # not a Kong, next test
                else:
                    winning.extend(range(i, i+4)) # mark Kong tiles as winning
                    i += 4 # jump past winning tiles
                    print(' track into Kong')
                    if backtrack(i, chowq): # recursively backtrack
                        print('backtrack from Kong')
                        return True # return winning if recursive winning
                    del winning[-4:] # otherwise unmark as winning
                    if _shown:
                        del _shown[-1]
                try:
                    _shown.append(Pong(bunch[i:i+3]))
                except ValueError:
                    pass # you get the drill
                else:
                    winning.extend(range(i, i+3))
                    i += 3
                    print(' track into Pong')
                    if backtrack(i, chowq):
                        print('backtrack from Pong')
                        return True
                    del winning[-3:]
                    if _shown:
                        del _shown[-1]
                if chowq:
                    try:
                        _shown.append(Chow(bunch[i:i+3]))
                    except ValueError:
                        pass
                    else:
                        winning.extend(range(i, i+3))
                        i += 3
                        print(' track into Chow')
                        if backtrack(i, chowq):
                            print('backtrack from Chow')
                            return True
                        del winning[-3:]
                        if _shown:
                            del _shown[-1]
                if not eyes_checked: # there can only be one pair of Eyes
                    try:
                        _shown.append(Eyes(bunch[i:i+2]))
                    except ValueError:
                        pass
                    else:
                        winning.extend(range(i, i+2))
                        i += 2
                        print(' track into Eyes')
                        eyes_checked = True
                        if backtrack(i, chowq):
                            print('backtrack from Eyes')
                            return True
                        del winning[-2:]
                        if _shown:
                            del _shown[-1]
                            eyes_checked = False
                i += 1
            print('backtrack from none')
            return False # all combinations have been checked
        bunch = others
        otherwon = backtrack(chowq=False)
        print('others backtracked', otherwon)
        winning = []
        bunch = simples
        simplwon = False
        if not eyes_checked and simples:
            print('eyes not yet checked')
            # This algorithm from https://stackoverflow.com/a/4155177/6605349
            # It's specific to tiles that can Chow
            # sum of values of simples % 3 maps to possible
            # values of eyes tiles
            values = ((3, 6, 9), (2, 5, 8), (1, 4, 7))
            total = sum(t.number + 1 for t in simples)
            for eye_value in values[total % 3]:
                for i in range(len(simples) - 1): # slen - eyelen + 1
                    if simples[i].number != eye_value - 1 or eye_value - 1 != simples[i+1].number:
                        continue
                    print('===\nChecking Eyes in:', simples[i:i+2], '\n===')
                    try:
                        shown.append(Eyes(simples[i:i+2]))
                    except ValueError:
                        pass # not Eyes, try next
                    else:
                        del simples[i:i+2]
                        break # found Eyes, now time to try
                if shown and isinstance(shown[-1], Eyes):
                    if backtrack(): # valid winning hand!
                        simplwon = True
                        break
                    else:
                        # undo removal
                        print('===\nEyes', shown[-1].tiles, 'failed\n===')
                        simples.extend(shown[-1].tiles)
                        del shown[-1]
                        simples.sort()
        elif simples: # no eyes removal necessary
            print('eyes checked')
            if backtrack(): # valid winning hand!
                simplwon = True
            else:
                print('simples backtracked False')
                return False # invalid
        else: # no simples, default valid
            print('no simples')
            simplwon = True
        print('simpl ended', simplwon)
        wonning = otherwon and simplwon
        shown.extend(_shown)
        if not wonning: # still not valid as combination of melds
            # time to try the special case: Thirteen Orphans
            wonning = all(
                [Tile(suit, 0) in hand and Tile(suit, 8) in hand
                 for suit in Simples]
                + [Tile(Honors.FENG, i) in hand for i in range(4)]
                + [Tile(Honors.LONG, i) in hand for i in range(3)]
            )
            if wonning:
                print('Thirteen Orphans')
                if _hand is None:
                    self.hand = hand
                    self.shown = shown
                return 13 # 13 points for Thirteen Orphans
        if not wonning:
            return False
        # Time to start counting points!
        print('---')
        points = 0
        if all(isinstance(meld, (Chow, Eyes)) for meld in shown):
            print('common hand')
            points += 1 # Common Hand
        if all(isinstance(meld, (Pong, Eyes)) for meld in shown):
            print('all in triplets')
            points += 3 # All in Triplets
        suit = None
        hon = False
        for tile in hand:
            if isinstance(tile.suit, Honors):
                hon = True
                continue
            if suit is not None and tile.suit != suit:
                break
            suit = tile.suit
        else:
            if hon and suit is None:
                print('all honor tiles')
                points += 10 # All Honor Tiles
            elif not hon:
                print('all one suit')
                points += 7 # All One Suit
            else:
                print('mixed one suit')
                points += 3 # Mixed One Suit
        dragons = 0
        winds = 0
        drageyes = False
        windeyes = False
        for meld in shown:
            if isinstance(meld, Pong):
                if meld.tiles[0].suit == Honors.LONG:
                    dragons += 1
                elif meld.tiles[0].suit == Honors.FENG:
                    winds += 1
            if isinstance(meld, Eyes):
                if meld.tiles[0].suit == Honors.LONG:
                    drageyes = True
                elif meld.tiles[0].suit == Honors.FENG:
                    windeyes = True
        if dragons == 3:
            print('great dragons')
            points += 8 # Great Dragons
        elif dragons == 2 and drageyes:
            print('small dragons')
            points += 5 # Small Dragons
        if winds == 4:
            print('great winds')
            points += 13 # Great Winds
        elif winds == 3 and windeyes:
            print('small winds')
            points += 6 # Small Winds
        kongs = True
        pongs = True
        for meld in shown:
            if not isinstance(meld, Kong):
                kongs = False
            if not isinstance(meld, (Pong, Eyes)):
                pongs = False
            elif _hand is None and isinstance(meld, Pong) and meld in self.shown:
                pongs = False # Self Triplets must be concealed
        if kongs:
            print('all kongs')
            points += 13 # All Kongs
        if pongs:
            print('self triplets')
            points += 13 # Self Triplets
        orphans = True
        for meld in shown:
            if isinstance(meld, Chow):
                orphans = False
                break
            if not isinstance(meld.tiles[0].suit, Simples):
                orphans = False
                break
            if not meld.tiles[0].number in (0, 8):
                orphans = False
                break
        if orphans:
            print('orphans')
            points += 10 # Orphans
        if _hand is not None or not self.shown:
            counts = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            goals = [3, 1, 1, 1, 1, 1, 1, 1, 3]
            suit = None
            gates = True
            for tile in hand:
                if suit is not None and tile.suit != suit or not isinstance(tile.suit, Simples):
                    gates = False
                    break
                suit = tile.suit
                counts[tile.number] += 1
            deductions = 0
            for i in range(9):
                if counts[i] not in (goals[i], goals[i]+1):
                    gates = False
                    break
                if counts[i] == goals[i] + 1:
                    deductions += 1
            if deductions != 1:
                gates = False
            if gates:
                print('nine gates')
                points += 10 # Nine Gates
        # Time to score melds
        print('---')
        if _hand is None:
            for meld in shown:
                if isinstance(meld, (Pong, Kong)) and meld.suit == Honors.FENG:
                    if meld.tiles[0].number == self.seat:
                        print('seat wind')
                        points += 1 # Seat Wind
                    if meld.tiles[0].number == self._root.game.wind:
                        print('prevailing wind')
                        points += 1 # Prevailing Wind
        for meld in shown:
            if isinstance(meld, (Pong, Kong)) and meld.tiles[0].suit == Honors.LONG:
                print('dragon')
                points += 1 # Dragon
        orphans = True
        for tile in hand:
            if isinstance(tile.suit, Simples) and tile.number not in (0, 8):
                orphans = False
                break
        if orphans:
            print('mixed orphans')
            points += 1 # Mixed Orphans
        # update hand and shown, finally - scoring is done
        if _hand is None:
            self.hand = hand
            self.shown = shown
        return points

class Players:
    """Represents operations on all four players."""

    game = None
    players = []

    def __init__(self, game):
        """Initialize players."""
        self.game = game
        self.players = [Player(i, self) for i in range(PLAYERS)]
        for play in self.players:
            play.draw_starting_hand(self.game.wall)
        for play in self.players:
            play.handle_bonuses(self.game.wall)

    def __getitem__(self, idx):
        if not 0 < idx < PLAYERS:
            raise IndexError
        return self.players[idx]

    def shift(self, flag=None):
        """Shift play order after a round.

        flag = True => east winning, repeat
        flag = False => no winners, repeat
        flag = None => normal hand, continue
        Returns whether game is over.
        """
        if flag is not None:
            return False # can't win if the round needs to repeat
        self.players.insert(0, self.players.pop())
        for play in self.players:
            play.seat += 1
            play.seat %= PLAYERS
        if self[0].pid == self[0].seat: # back to starting order
            self.game.wind += 1
            self.game.wind %= PLAYERS
        if self.game.wind == 0: # back to east wind, game over
            return True
        return False

class Game:
    """Base game class."""

    wall = []
    players = None
    # wind = 0 => east wind
    # wind = 1 => south wind
    # wind = 2 => west wind
    # wind = 3 = north wind
    wind = 0

    def __init__(self):
        """Shuffle a new wall and initialize players."""
        self.shuffle()
        self.players = Players(self)

    def shuffle(self):
        """Create and shuffle a new wall. Called at initialization."""
        wall = []
        # simples
        for suit in Simples:
            for num in range(1, 10):
                wall.extend([Tile(suit, num) for _ in range(4)])
        # honors
        for wind in range(4): # east, south, west, north
            wall.extend([Tile(Honors.FENG, wind) for _ in range(4)])
        for dragon in range(3): # zhong, fa, ban
            wall.extend([Tile(Honors.LONG, dragon) for _ in range(4)])
        # bonuses
        for i in range(4):
            wall.append(Tile(Bonuses.HUA, i))
            wall.append(Tile(Bonuses.GUI, i))
        random.shuffle(wall)
        self.wall = wall

    def advance(self):
        """Advance one turn."""
        pass
