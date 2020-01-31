"""Contains the Meld class and its subclasses."""

from .tiles import Tile, Simples, Honors, Bonuses, Misc

class Meld:
    """Represents a meld of tiles."""

    @property
    def size(self):
        """Size of this meld."""
        raise NotImplementedError

    def __init__(self, tiles):
        """Initialize the meld with its tiles and check validity."""
        self.tiles = tiles[:]
        self.tiles.sort()
        self.check_meld()

    def __str__(self):
        """str(meld) -> 'suit1/num1|suit2/num2|...'"""
        return '|'.join(map(str, self.tiles))
    __repr__ = __str__

    def __eq__(self, other):
        # not implemented for non-meld,
        # but not equal for melds of different types
        if not isinstance(other, Meld):
            return NotImplemented
        if not isinstance(other, type(self)):
            return False
        return sorted(self.tiles) == sorted(other.tiles)

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

    @property
    def size(self):
        """Size of the same-numbered meld."""
        raise NotImplementedError

    def check_meld(self):
        """Check validity of the meld."""
        if len(self.tiles) != self.size:
            raise ValueError(f'{type(self).__name__}s must be '
                             f'{self.size} tiles, not {len(self.tiles)}')
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

class Kong(_SameNum):
    """Represents a Kong meld (four identical tiles, counted as three)"""

    size = 4

    def __str__(self):
        """Kongs are represented by one faceup, two stacked down, one up"""
        #pylint: disable=no-member
        return '|'.join(map(str, [self.tiles[0], Misc.HIDDEN.value, self.tiles[-1]]))
        #pylint: enable=no-member

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

class _CachedAttribute: # pylint: disable=too-few-public-methods
    '''Computes attribute value and caches it in the instance.
    From the Python Cookbook (Denis Otkidach)
    This decorator allows you to create a property which can be computed once
    and accessed many times. Sort of like memoization.
    '''
    def __init__(self, method, name=None):
        """Initialize the cached attribute."""
        # record the unbound-method and the name
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__
    def __get__(self, inst, cls):
        """Get the cached attribute."""
        # self: <__main__._CachedAttribute object at 0xb781340c>
        # inst: <__main__.Foo object at 0xb781348c>
        # cls: <class '__main__.Foo'>
        if inst is None:
            # instance attribute accessed on class, return self
            # You get here if you write `Foo.bar`
            return self
        # compute, cache and return the instance's attribute value
        result = self.method(inst)
        # setattr redefines the instance's attribute so this doesn't get called again
        setattr(inst, self.name, result)
        return result

class Wu(Meld):
    """Represents a winning hand. Only meld that consists of sub-melds"""

    size = range(14, 19, 2) # winning is at least 14, at most 18
    melds = [] # melds present in the hand

    #pylint: disable=too-many-branches,too-many-statements,too-many-locals
    def check_meld(self):
        """Check whether this hand is a winning hand."""
        hand = self.tiles
        if len(hand) not in self.size:
            raise ValueError('Wus must be between 14 and 18, '
                             'and a multiple of 2.')
        shown = []
        # split hand into simples and non-simples,
        # because there's some optimization that can
        # be done on non-simples
        simples = [t for t in hand if isinstance(t.suit, Simples)]
        others = [t for t in hand if not isinstance(t.suit, Simples)]
        print(simples, others)
        eyes_checked = False # 16 tiles can only be four Kongs
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
            while i < slen - Eyes.size + 1:
                if i in winning: # don't look at winning tiles
                    i += 1
                    continue
                try:
                    _shown.append(Kong(bunch[i:i+Kong.size]))
                except ValueError:
                    pass # not a Kong, next test
                else:
                    winning.extend(range(i, i+Kong.size)) # mark Kong tiles as winning
                    i += Kong.size # jump past winning tiles
                    print(' track into Kong')
                    if backtrack(i, chowq): # recursively backtrack
                        print('backtrack from Kong')
                        return True # return winning if recursive winning
                    del winning[-Kong.size:] # otherwise unmark as winning
                    if _shown:
                        del _shown[-1]
                try:
                    _shown.append(Pong(bunch[i:i+Pong.size]))
                except ValueError:
                    pass # you get the drill
                else:
                    winning.extend(range(i, i+Pong.size))
                    i += Pong.size
                    print(' track into Pong')
                    if backtrack(i, chowq):
                        print('backtrack from Pong')
                        return True
                    del winning[-Pong.size:]
                    if _shown:
                        del _shown[-1]
                if chowq:
                    try:
                        _shown.append(Chow(bunch[i:i+Chow.size]))
                    except ValueError:
                        pass
                    else:
                        winning.extend(range(i, i+Chow.size))
                        i += Chow.size
                        print(' track into Chow')
                        if backtrack(i, chowq):
                            print('backtrack from Chow')
                            return True
                        del winning[-Chow.size:]
                        if _shown:
                            del _shown[-1]
                if not eyes_checked: # there can only be one pair of Eyes
                    try:
                        _shown.append(Eyes(bunch[i:i+Eyes.size]))
                    except ValueError:
                        pass
                    else:
                        winning.extend(range(i, i+Eyes.size))
                        i += Eyes.size
                        print(' track into Eyes')
                        eyes_checked = True
                        if backtrack(i, chowq):
                            print('backtrack from Eyes')
                            return True
                        del winning[-Eyes.size:]
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
            if len(hand) == 14:
                values = ((3, 6, 9), (2, 5, 8), (1, 4, 7))
                divisor = 3
            elif len(hand) == 16:
                values = (tuple(range(1, 10)),)
                divisor = 1
            elif len(hand) == 18:
                values = ((2, 4, 6, 8), (), (1, 3, 5, 7, 9), ())
                divisor = 4
            total = sum(t.number + 1 for t in simples)
            print(f'total: {total} divisor: {divisor} remainder: {total % divisor}'
                  f' result: {values[total % divisor]}')
            for eye_value in values[total % divisor]:
                for i in range(len(simples) - Eyes.size + 1):
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
                raise ValueError('Simples tiles in this hand '
                                 'invalidate a winning hand',
                                 simples)
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
        if not wonning:
            raise ValueError('Not a winning hand', hand)
        self.melds = shown

    @_CachedAttribute
    def points(self):
        """Number of points the hand is worth.
        (Not including situational points or wind points.)
        """
        # Rules from https://en.wikipedia.org/wiki/Hong_Kong_Mahjong_scoring_rules
        hand = self.tiles
        shown = self.melds
        print('---', shown)
        points = 0
        if all(
                [Tile(suit, 0) in hand and Tile(suit, 8) in hand
                 for suit in Simples]
                + [Tile(Honors.FENG, i) in hand for i in range(4)]
                + [Tile(Honors.LONG, i) in hand for i in range(3)]
        ):
            print('thirteen orphans')
            points += 13 # Thirteen Orphans
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
            if not isinstance(meld, (Kong, Eyes)):
                kongs = False
            if not isinstance(meld, (Pong, Eyes)):
                pongs = False
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
        # scoring done, return
        return points

    def situational_points(self, player):
        """Number of points gained from the situation."""
        shown = self.melds
        points = 0
        # wind points
        for meld in shown:
            if isinstance(meld, (Pong, Kong)) and meld.suit == Honors.FENG:
                if meld.tiles[0].number == player.seat:
                    print('seat wind')
                    points += 1 # Seat Wind
                #pylint: disable=protected-access
                if meld.tiles[0].number == player._root.game.wind:
                    print('prevailing wind')
                    points += 1 # Prevailing Wind
        # Self Triplets are assumed concealed in self.points,
        # so deduct the points value here if they turn out
        # to be revealed.
        pongs = True
        for meld in shown:
            if not isinstance(meld, (Pong, Eyes)):
                pongs = False
            elif isinstance(meld, Pong) and meld in player.shown:
                pongs = False # Self Triplets must be concealed
        if not pongs:
            print('deduct self triplets')
            points -= 13
        # bonus points
        hua = [False, False, False, False]
        gui = hua[:]
        for tile in player.bonus:
            if tile.number == player.seat:
                points += 1
            if tile.suit == Bonuses.HUA:
                hua[tile.number] = True
            if tile.suit == Bonuses.GUI:
                gui[tile.number] = True
        if all(hua):
            points += 1
        if all(gui):
            points += 1
        return points
