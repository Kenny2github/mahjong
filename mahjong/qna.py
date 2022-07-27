from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import (
    TYPE_CHECKING, ClassVar, Generator, List,
    Mapping, Optional, Tuple, Union
)

if TYPE_CHECKING:
    from .game import Hand
    from .melds import Wu, WuFlag, Meld, Kong
    from .players import Player
    from .tiles import Tile

__all__ = [
    'Question',
    'UserIO',
    'PlayeredIO',
    'ArrivedIO',
    'DiscardWhat',
    'MeldFromDiscardQ',
    'ReadyQ',
    'RobKongQ',
    'SelfDrawQ',
    'ShowEKFCP',
    'ShowEKFEP',
    'WhichWu',
    'UserIOType',

    'STOCK_TABLES',
    'HandResult',
    'HandEnding',
    'NormalHandEnding',
    'Goulash',
    'DealerWon',
    'HandEndingType',

    'YieldType',
]

def _answer(gen: Generator, ans=None) -> YieldType:
    """Send the answer to the internal generator."""
    try:
        return gen.send(ans)
    except StopIteration as exc:
        return exc.value

# UserIO

class Question(Enum):
    """The question that is being asked.

    .. deprecated:: 2.0.0

    Attributes:
        MELD_FROM_DISCARD_Q: :class:`MeldFromDiscardQ`
        SHOW_EKFCP_Q: :class:`ShowEKFCP`
        SHOW_EKFEP_Q: :class:`ShowEKFEP`
        DISCARD_WHAT: :class:`DiscardWhat`
        ROB_KONG_Q: :class:`RobKongQ`
        WHICH_WU: :class:`WhichWu`
        READY_Q: :class:`ReadyQ`
        SELF_DRAW_Q: :class:`SelfDrawQ`
    """
    MELD_FROM_DISCARD_Q = 16
    SHOW_EKFCP_Q = 23
    SHOW_EKFEP_Q = 24
    DISCARD_WHAT = 27
    ROB_KONG_Q = 33
    WHICH_WU = 40
    READY_Q = 0
    SELF_DRAW_Q = 13

@dataclass
class UserIO(ABC):
    """A question to be answered."""

    _question: ClassVar[Question]

    @property
    def question(self) -> Question:
        """The question that is being asked.

        .. deprecated:: 2.0.0
        """
        from warnings import warn
        warn('The question attribute is deprecated '
             'in favor of checking the type of the question '
             'using isinstance().', DeprecationWarning)
        return self._question

    gen: Generator

    def answer(self, ans=None):
        """Answer the question.

        Args:
            ans: The answer. See specific subclasses for details.
        """
        return _answer(self.gen, ans)

    def __repr__(self) -> str:
        args = ', '.join(f'{attr}={getattr(self, attr)}'
                         for attr in 'question melds arrived player'.split()
                         if hasattr(self, attr))
        return f'{type(self).__name__}({args})'

@dataclass
class PlayeredIO(UserIO, ABC):
    """A :class:`UserIO` with a :attr:`~PlayeredIO.player` attribute.

    Attributes:
        player: See specific subclasses' docs.
    """
    player: Player

    @property
    def hand(self) -> List[Tile]:
        """Shortcut to ``.player.hand``."""
        return self.player.hand

    @property
    def shown(self) -> List[Meld]:
        """Shortcut to ``.player.shown``."""
        return self.player.shown

@dataclass
class ArrivedIO(PlayeredIO, ABC):
    """A :class:`PlayeredIO` with an :attr:`arrived` attribute.

    Attributes:
        arrived: See specific subclasses' docs.
    """
    arrived: Tile

    @property
    def playable_hand(self) -> List[Tile]:
        """Shortcut to ``.player.hand``, with the :attr:`arrived`
        tile removed if present in the hand.
        """
        return [tile for tile in self.hand if tile is not self.arrived]

    @property
    def arrived_playable(self) -> bool:
        """Whether the :attr:`arrived` tile can be played
        from the hand (i.e. whether it was drawn, not stolen to meld).
        """
        return any(tile is self.arrived for tile in self.hand)

@dataclass
class DiscardWhat(ArrivedIO):
    """Which tile would you like to discard?

    Attributes:
        player: The player who needs to discard.
        arrived: The tile that was drawn or stolen, which may be either
            in the :attr:`hand` if it was drawn or in one of the
            :attr:`shown` melds' tiles.
        last_meld: The meld that was made most recently.
            :obj:`None` if purely a draw.
    """
    _question = Question.DISCARD_WHAT

    last_meld: Optional[Meld]

    def answer(self, ans: Tile):
        """Answer the question.

        Args:
            ans: The tile to discard.
                (Must be a reference to an item in the player's hand.)
        """
        return super().answer(ans)

@dataclass
class MeldFromDiscardQ(ArrivedIO):
    """What meld would you like to make from the last discard?

    Attributes:
        melds: Different possible melds that the player can make
            with the last discard.
        player: The player who can make the meld(s).
        arrived: The last discard in question
            (**not** present in the player's hand).
    """
    _question = Question.MELD_FROM_DISCARD_Q

    melds: List[Meld]

    def answer(self, ans: Optional[Meld] = None):
        """Answer the question.

        Args:
            ans: Which meld to make (must be a reference to an item from the
                provided list), or :obj:`None` to choose not to meld.
        """
        return super().answer(ans)

@dataclass
class ReadyQ(UserIO):
    """The round has just ended, are you ready to continue to the next one?"""
    _question = Question.READY_Q

    def answer(self):
        """Answer to continue."""
        return super().answer()

@dataclass
class RobKongQ(PlayeredIO):
    """Do you want to rob someone's Kong to win?

    Attributes:
        melds: A 1-list containing the winning hand that can be made.
        player: The player that can win with this hand.
    """
    _question = Question.ROB_KONG_Q

    melds: List[Wu]

    def answer(self, ans: bool):
        """Answer the question.

        Args:
            ans: Whether to rob the Kong to win.
        """
        return super().answer(ans)

@dataclass
class SelfDrawQ(ArrivedIO):
    """You have drawn a tile that you can win with, would you like to?

    Attributes:
        melds: One-element list containing the hand you can win with.
        player: The player that can win with this hand.
        arrived: The tile that was drawn (already in the :attr:`hand`).
    """
    _question = Question.SELF_DRAW_Q

    melds: List[Wu]

    def answer(self, ans: bool):
        """Answer the question.

        Args:
            ans: Whether to take this self-draw.
        """
        return super().answer(ans)

@dataclass
class ShowEKFCP(ArrivedIO):
    """Would you like to show an Exposed Kong From Concealed Pong?

    (Only covers EKFCP by draw; by theft is covered by
    :class:`MeldFromDiscardQ`.)

    Attributes:
        melds: Possible Kongs you could show.
        player: The player who can make the Kong(s).
        arrived: The last tile drawn (**already** present in the :attr:`hand`,
            may or may not be related to any of the offered Kongs).
    """
    _question = Question.SHOW_EKFCP_Q

    melds: List[Kong]

    def answer(self, ans: Optional[Kong] = None):
        """Answer the question.

        Args:
            ans: Which Kong to make (must be a reference to an item from the
                provided list), or :obj:`None` to choose not to meld.
        """
        return super().answer(ans)

@dataclass
class ShowEKFEP(ShowEKFCP):
    """Same deal as :class:`ShowEKFCP` but exposed Pong instead.

    Warning:
        This inherits from :class:`ShowEKFCP`, so call :func:`isinstance`
        on this class **first**, before the other one.
    """
    _question = Question.SHOW_EKFEP_Q

@dataclass
class WhichWu(UserIO):
    """There are multiple valid arrangements of tiles to win;
    which one do you want to win with?

    Not asked when there is only one arrangement.

    Attributes:
        melds: Each list of :class:`Meld` s is a valid combination of them
            to make a winning hand.
    """
    _question = Question.WHICH_WU

    melds: List[List[Meld]]

    def answer(self, ans: List[Meld]):
        return super().answer(ans)

UserIOType = Union[DiscardWhat, MeldFromDiscardQ, ReadyQ, RobKongQ, SelfDrawQ,
                   ShowEKFCP, ShowEKFEP, WhichWu]

# HandEnding

STOCK_TABLES = {
    'enwp': {
        1: 1, 2: 1, 3: 1,
        4: 2, 5: 2, 6: 2,
        7: 4, 8: 4, 9: 4,
        10: 8
    },
    'zhwp': {
        0: 1, 1: 2, 2: 4, 3: 8,
        4: 16, 5: 24, 6: 32, 7: 48,
        8: 64, 9: 96, 10: 128, 11: 192,
        12: 256, 13: 384
    },
    # in the app I play,
    # 3 faan = 1200c = 1x1200
    # 4 faan = 2400c = 2x1200
    # 5 faan = 3600c = 3x1200
    # 6 faan = 4800c = 4x1200
    # 7 faan = 7200c = 6x1200
    # 8 faan = 9600c = 8x1200
    # 9 faan =13200c =11x1200
    'random_app': {
        1: 1, 2: 1, 3: 1,
        4: 2, 5: 3, 6: 4,
        7: 6, 8: 8, 9: 11,
        10: 13
    }
}

class HandResult(Enum):
    """The result of a hand.

    .. deprecated:: 2.0.0

    Attributes:
        NORMAL: :class:`NormalHandEnding`
        GOULASH: :class:`Goulash`
        DEALER_WON: :class:`DealerWon`
    """
    NORMAL = 0
    GOULASH = 1
    DEALER_WON = 2

@dataclass
class HandEnding(ABC):
    """The ending conditions of a hand.

    The implied question is "The hand has just ended, are you ready to
    continue to the next one? Answer to continue."
    """
    _result: ClassVar[HandResult]

    @property
    def result(self) -> HandResult:
        """The result type.

        .. deprecated:: 2.0.0
        """
        from warnings import warn
        warn('The result attribute is deprecated '
             'in favor of checking the type of the result '
             'using isinstance().', DeprecationWarning)
        return self._result

    hand: Hand

    def answer(self):
        """Answer the ending and receive the next question
        (which can be :obj:`None` for a standalone hand).
        """
        return _answer(self.hand.gen)

@dataclass
class NormalHandEnding(HandEnding):
    """A normal win; play advances.

    Attributes:
        winner: The player who won the hand.
        wu: The winning hand.
        choice: The particular arrangement of melds to win.
    """
    _result = HandResult.NORMAL

    winner: Player
    wu: Wu
    choice: List[Meld]

    def faan(self) -> Tuple[int, WuFlag]:
        """Calculate the faan for this hand.

        Returns:
            ``(points, flags)``: Combined from :meth:`Wu.faan` (:attr:`wu`)
            and :meth:`Player.bonus_faan` (:attr:`winner`).
        """
        points = self.wu.faan(self.choice, (self.winner.seat, self.hand.wind))
        bonus = self.winner.bonus_faan()
        return (points[0] + bonus[0], points[1] | bonus[1])

    def points(self, min_faan: int = 3,
               table: Optional[Mapping[int, int]] = None
               ) -> Tuple[List[int], Optional[WuFlag]]:
        """Calculate the change in points for each player.

        Args:
            min_faan: Minimum faan for the hand to produce points.
            table: A translation table of faan to base points. The largest
                faan value is assumed to be the limit, and values larger than
                it will be mapped to it.

        Returns:
            ``([dp1, dp2, dp3, dp4], flags)`` where only one ``dpn`` is
            positive and ``flags`` represent ending flags.

        Returns:
            ``([0, 0, 0, 0], None)`` if ``min_faan`` is not met.
        """
        points = [0, 0, 0, 0]
        faan, flags = self.faan()
        if faan < min_faan:
            return (points, None)
        winner = self.winner
        wu = self.wu
        if table is None:
            table = STOCK_TABLES['random_app']
        limit = max(table.keys())
        base = table[min(faan, limit)]
        flags = wu.flags(self.choice)
        # special penalties that make the perpetrator pay
        # for everyone else on top of themselves
        if ((WuFlag.TWELVE_PIECE in flags and WuFlag.SELF_DRAW in flags)
                or (WuFlag.GAVE_KONG in flags and WuFlag.SELF_DRAW in flags)
                or WuFlag.GAVE_DRAGON in flags) and wu.discarder is not None:
            points[winner.seat] += base * 3
            points[wu.discarder] -= base * 3
        # loser pays double in normal losing conditions
        elif wu.discarder is not None:
            points[winner.seat] += base * 2
            points[wu.discarder] -= base * 2
        # self draw means everyone pays
        elif WuFlag.SELF_DRAW in flags:
            for i in range(4):
                if i == winner.seat:
                    points[i] += base * 3
                else:
                    points[i] -= base
        else:
            raise ValueError('Somehow, nobody gets points. '
                             'Possibly report to maintainer with '
                             'the following information: '
                             + str(self.wu.__dict__)
                             + ' ;; ' + str(self.winner.__dict__))
        return (points, flags)

@dataclass
class Goulash(HandEnding):
    """The hand ended in a draw (goulash hand),
    so an extra round will be played with the seat winds unchanged
    (unless that rule is disabled).

    No attributes.
    """
    _result = HandResult.GOULASH

    def faan(self) -> Tuple[int, None]:
        """Goulash endings have no faan and no flags.

        Returns:
            ``(0, None)``
        """
        return (0, None)

    def points(self, min_faan: int = 3,
               table: Optional[Mapping[int, int]] = None
               ) -> Tuple[List[int], None]:
        """Goulash endings give nobody points and have no flags.

        Returns:
            ``([0, 0, 0, 0], None)``
        """
        return ([0, 0, 0, 0], None)

class DealerWon(NormalHandEnding):
    """The player in the prevailing wind seat won,
    so an extra round will be played with the seat winds unchanged
    (unless that rule is disabled).

    Same attributes as :class:`NormalHandEnding`.

    Warning:
        This inherits from :class:`NormalHandEnding`, so call
        :func:`isinstance` on this class **first**, before the other one.
    """
    _result = HandResult.DEALER_WON

HandEndingType = Union[NormalHandEnding, Goulash, DealerWon]

YieldType = Union[UserIOType, HandEndingType, None]
