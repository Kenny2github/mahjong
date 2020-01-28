"""Contains Player(s) classes."""

from .melds import Kong, Pong, Chow, Eyes
from .tiles import Simples, Honors, Bonuses, Tile

PLAYERS = 4
HANDSIZE = 13

class Player:
    """Represents operations on a specific player."""

    # pid/seat = 0 => initial east
    # pid/seat = 1 => initial south
    # pid/seat = 2 => initial west
    # pid/seat = 3 => initial north
    pid = seat = 0
    hand = shown = bonus = []
    draw = None # index in hand of drawn tile

    def __init__(self, pid, root):
        self.pid = self.seat = pid
        self._root = root # Players object to refer through
        self.hand = []
        self.shown = []
        self.bonus = []

    def draw_starting_hand(self, wall):
        """Draw the starting 13 (or 14) tiles from the wall."""
        self.hand = wall[:HANDSIZE] #True == 1
        del wall[:HANDSIZE]
        self.hand.sort()
        if self.seat == 0:
            draw = wall.pop(0)
            self.hand.append(draw)
            self.hand.sort()
            self.draw = self.hand.index(draw)

    def handle_bonuses(self, wall):
        """Handle bonus tiles.
        Move them to self.bonus and draw replacement tiles from the wall.
        """
        found = True
        while found:
            found = False
            i = 0
            while i < len(self.hand):
                if isinstance(self.hand[i].suit, Bonuses):
                    # remove bonus from hand
                    self.bonus.append(self.hand[i])
                    del self.hand[i]
                    # replenish hand with new tile from wall
                    self.hand.append(wall.pop())
                    found = True
                else:
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
                values = (tuple(range(1, 10)))
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
                return 13 # 13 points for Thirteen Orphans
        if not wonning:
            return False
        ##########################################################
        # Time to start counting points!
        # Rules from https://en.wikipedia.org/wiki/Hong_Kong_Mahjong_scoring_rules
        print('---', shown)
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
            if not isinstance(meld, (Kong, Eyes)):
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
        # scoring done, return
        return points

class Players:
    """Represents operations on all four players."""

    game = None
    players = []

    def __init__(self, game):
        """Initialize players."""
        self.game = game
        self.players = [Player(i, self) for i in range(PLAYERS)]
        self.init_players()

    def init_players(self):
        """Starting machinations for a round."""
        for play in self.players:
            play.draw_starting_hand(self.game.wall)
        for play in self.players:
            play.handle_bonuses(self.game.wall)

    def __getitem__(self, idx):
        if not idx < PLAYERS:
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
