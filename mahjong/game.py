"""Contains the Game and Round classes."""

import random
from .melds import Kong, Pong, Chow
from .tiles import Honors, Simples, Bonuses, Tile
from .players import Players, PLAYERS

__version__ = "0.0.1"

def meld_possible(hand, meld_type=None, frozen=None):
    """If a meld of meld_type is possible, return that meld.
    Otherwise, return None.

    If meld_type is None, checks all meld types except Eyes,
    in Mahjong order of precedence: Kong, Pong, Chow.
    """
    hand.sort()
    if meld_type is None:
        for mtype in (Kong, Pong, Chow):
            possible = meld_possible(hand, mtype, frozen)
            if possible is not None:
                return possible
        return None
    if frozen is not None:
        frozen = [frozen]
        dsize = -1
    else:
        frozen = []
        dsize = 0
    for i in range(len(hand) - meld_type.size + 1 + dsize):
        try:
            possible = meld_type(hand[i:i + meld_type.size + dsize] + frozen)
        except ValueError:
            pass
        else:
            break
    else:
        possible = None
    return possible

class Round:
    """Represents one round/hand of Mahjong."""

    wall = []
    discard = []
    players = None
    # wind = 0 => east wind
    # wind = 1 => south wind
    # wind = 2 => west wind
    # wind = 3 => north wind
    wind = 0
    game_gen = None # generator that powers the game
    end = None # end results

    def __init__(self, wind=0):
        """Shuffle a new wall and initialize players."""
        self.wind = wind
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

    def run(self):
        """Run the game. Returns a generator

        Every generator iteration accepts one send() value:
        the index in the last player's hand of the tile discarded by last player
        (decision of player specified in previous yield)

        Yields a 4-tuple of:
        0 - next player whose turn it is
        1 - previous send() value
        2 - possible meld that the next player can make with the discard
        3 - players who could steal the turn, in priority order
        """
        seat = 0
        play = self.players[seat]
        discard, jump = yield (
            play, play.draw,
            # only Kong possible to reveal from draw
            meld_possible(play.hand, Kong), []
        )
        if jump is not None:
            raise ValueError('Cannot jump to a player before first turn')
        discard_tile = play.hand.pop(discard)
        while 1:
            cont = True
            while (jump is None and cont) or (jump is not None and play != jump):
                seat += 1
                seat %= PLAYERS
                play = self.players[seat]
                cont = False
            if jump is None: # truly discarded
                self.discard.append(discard_tile)
            discard_tile = self.players[seat-1].hand.pop(discard)
            jumpers = [
                None, # win
                None, # pong/kong
                None, # chow
            ]
            for i in self.players:
                i.hand.append(discard_tile)
                i.hand.sort()
                i.draw = i.hand.index(discard_tile)
                if i is play:
                    continue
                if i.won():
                    jumpers[0] = i
                elif meld_possible(i.hand, Kong):
                    jumpers[1] = i
                elif meld_possible(i.hand, Pong):
                    jumpers[1] = i
                elif meld_possible(i.hand, Chow):
                    jumpers[2] = i
                i.hand.remove(discard_tile)
                i.draw = None
            discard, jump = yield (
                play, discard,
                meld_possible(play.hand),
                [i for i in jumpers if i is not None]
            )

    def start(self):
        """Start the game (make it ready for use with first_turn() and advance()"""
        self.game_gen = self.run()

    def first_turn(self):
        """Advance the first turn.
        Return value is run() yield value.
        """
        if self.game_gen is None:
            self.start()
        return next(self.game_gen)

    def advance(self, discard, jump=None):
        """Advance one turn.
        Return value is run() yield value,
        discard parameter is run() send value.
        Raises StopIteration when game is over - look at .end value
        """
        if self.game_gen is None:
            raise RuntimeError('Trying to advance turns in a nonexistent game')
        try:
            return self.game_gen.send((discard, jump))
        except StopIteration as exc:
            self.end = exc.value
            raise

class Game:
    """Represents an entire game (consisting of at least 16 Rounds)."""

    def __init__(self):
        """Get everything ready to start the game."""
        self.round = Round()

    def next_round(self):
        """Prepare for the next round of the game."""
        self.round.wind += 1
        self.round.shuffle()
        self.round.players.init_players()

    def start(self):
        """Start the next round."""
        self.round.start()
