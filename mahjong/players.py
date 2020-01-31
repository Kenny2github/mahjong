"""Contains Player(s) classes."""

from .melds import Wu
from .tiles import Bonuses

PLAYERS = 4
HANDSIZE = 13

class Player: #pylint: disable=too-many-instance-attributes
    """Represents operations on a specific player."""

    # pid/seat = 0 => (initial) east
    # pid/seat = 1 => (initial) south
    # pid/seat = 2 => (initial) west
    # pid/seat = 3 => (initial) north
    _pid = _seat = 0
    _hand = _shown = _bonus = []
    _draw = None

    # apparently pylint doesn't understand property setters, so...
    #pylint: disable=E0102,C0111,E0202
    @property
    def pid(self):
        """Initial seat"""
        return self._pid

    @property
    def seat(self):
        """Current seat"""
        return self._seat
    @seat.setter
    def seat(self, value):
        self._seat = value

    @property
    def hand(self):
        """List of Tiles in this player's hand."""
        return self._hand
    @hand.setter
    def hand(self, value):
        self._hand = value

    @property
    def shown(self):
        """List of Melds shown to other players."""
        return self._shown
    @shown.setter
    def shown(self, value):
        self._shown = value

    @property
    def bonus(self):
        """List of Bonuses acquired during the game."""
        return self._bonus
    @bonus.setter
    def bonus(self, value):
        self._bonus = value

    @property
    def draw(self):
        """Index in player's hand of tile drawn from wall."""
        return self._draw
    @draw.setter
    def draw(self, value):
        self._draw = value
    #pylint: enable=E0102,C0111,E0202

    def __init__(self, pid, root):
        self._pid = self.seat = pid
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

    def won(self):
        """Check if this player has won with their current hand.
        If they have, returns number of points the hand is worth (not including
        winning condition points).
        If not, returns False.
        """
        try:
            meld = Wu(self.hand + sum((i.tiles for i in self.shown), []))
        except ValueError: # not a winning hand
            return False
        else:
            points = meld.points
            points += meld.situational_points(self)
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
