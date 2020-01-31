"""Contains the Game and Round classes."""

import random
from collections import namedtuple
from .melds import Kong, Pong, Chow, Wu
from .tiles import Honors, Simples, Bonuses, Tile
from .players import Players, PLAYERS

__version__ = "0.0.1"

Turn = namedtuple('Turn', [
    'next', 'discard', 'jump'
])
Turn.__doc__ = """
    0 - next player whose turn it is
    1 - index in previous player's hand, of previous player's discard
    2 - (player, meld_type)s who could steal the turn, in priority order
"""

def meld_possible(hand, meld_type=None, frozen=None):
    """If a meld of meld_type is possible, return (that meld, index found).
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
            possible = (meld_type(hand[i:i + meld_type.size + dsize] + frozen), i)
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

        Every generator iteration accepts one send() value, a 2-tuple of:
        0 - the index in the last player's hand of the tile discarded by last player
        1 - None, or a 2-tuple of:
            0 - the player to skip to (could still be next player in line)
            1 - the type of meld that they can make

        Yields a Turn namedtuple.

        The flow of the game is as follows.
        Note: "yielded" is equivalent to "returned from advance()"
         1. (Player X, index of tile discarded in previous player's hand,
            (player to jump to, meld they could make)s) yielded
            * When returned from first_turn(), 2nd element is None
            * Player.draw contains index in Player.hand of tile
              drawn from wall. Can be None
         2. If 3rd element is non-empty, ask each player in it whether
            they want to do that meld. If Player J does:
             1. Ask Player J which tile to discard (which cannot be in the meld)
             2. Send (index of tile discarded in Player J's hand,
                3rd element element containing Player J) to generator
             3. Meld is added to Player J's shown melds and discard tile is discarded
             4. Back to root 1, where X=J+1
         3. Otherwise, ask Player X which tile to discard
         4. Send (index of tile discarded in Player X's hand, None) to generator
         5. Back to 1, where X=X+1
        """
        seat = 0
        play = self.players[seat]
        discard, jump = yield Turn(
            play, None,
            # only Kong possible to reveal from draw
            [(play, Kong)] if meld_possible(play.hand, Kong) else []
        )
        if jump is not None:
            raise ValueError('Cannot jump to a player before first turn')
        while 1:
            cont = True
            discard_tile = play.hand.pop(discard)
            while (jump is None and cont) or (jump is not None and play != jump[0]):
                seat += 1
                seat %= PLAYERS
                play = self.players[seat]
                cont = False
            if jump is None: # truly discarded
                self.discard.append(discard_tile)
                draw = self.wall.pop(0)
                while isinstance(draw.suit, Bonuses):
                    play.bonus.append(draw)
                    draw = self.wall.pop(0)
                play.hand.append(draw)
                play.draw = play.hand.index(draw)
            else:
                possible, idx = meld_possible(play.hand, jump[1])
                play.shown.append(possible)
                del play.hand[idx:idx+jump[1].size]
                if jump[1] is Kong:
                    # creating a Kong reduces your effective tile count by 1
                    # so replenish a tile from the end of the wall
                    play.hand.append(self.wall.pop())
            jumpers = [
                None, # win
                None, # pong/kong
                None, # chow
            ]
            idxx = self.players.players.index(play)
            for idx, i in enumerate(self.players):
                if meld_possible(i.hand, Wu, discard_tile):
                    jumpers[0] = (i, Wu)
                elif meld_possible(i.hand, Kong, discard_tile):
                    jumpers[1] = (i, Kong)
                elif meld_possible(i.hand, Pong, discard_tile):
                    jumpers[1] = (i, Pong)
                # chow can only be by next player
                elif idx == idxx + 1 and meld_possible(i.hand, Chow, discard_tile):
                    jumpers[2] = (i, Chow)
            discard, jump = yield Turn(
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
