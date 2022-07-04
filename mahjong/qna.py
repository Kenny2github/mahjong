from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, ClassVar, Generator, List, Mapping, Optional, Tuple, Union

if TYPE_CHECKING:
    from .game import Hand
    from .melds import Wu, WuFlag, Meld, Kong
    from .players import Player
    from .tiles import Tile

def _answer(gen: Generator, ans=None) -> YieldType:
    """Send the answer to the internal generator."""
    try:
        return gen.send(ans)
    except StopIteration as exc:
        return exc.value

# UserIO

class Question(Enum):
    MELD_FROM_DISCARD_Q = 16
    SHOW_EKFCP_Q = 23
    SHOW_EKFEP_Q = 24
    DISCARD_WHAT = 27
    ROB_KONG_Q = 33
    WHICH_WU = 40
    READY_Q = 0
    SELF_DRAW_Q = 13

@dataclass
class UserIO:
    _question: ClassVar[Question]

    @property
    def question(self) -> Question:
        from warnings import warn
        warn('The question attribute is deprecated '
             'in favor of checking the type of the question '
             'using isinstance().', DeprecationWarning)
        return self._question

    gen: Generator

    def answer(self, ans=None):
        return _answer(self.gen, ans)

    def __repr__(self) -> str:
        args = ', '.join(f'{attr}={getattr(self, attr)}'
                         for attr in 'question melds arrived player'.split()
                         if hasattr(self, attr))
        return f'{type(self).__name__}({args})'

@dataclass
class PlayeredIO(UserIO):
    player: Player

    @property
    def hand(self) -> List[Tile]:
        """Shortcut to .player.hand"""
        return self.player.hand

    @property
    def shown(self) -> List[Meld]:
        """Shortcut to .player.shown"""
        return self.player.shown

@dataclass
class ArrivedIO(PlayeredIO):
    arrived: Tile

    @property
    def playable_hand(self) -> List[Tile]:
        """Shortcut to .player.hand, with the arrived tile removed
        if present in the hand.
        """
        return [tile for tile in self.hand if tile is not self.arrived]

    @property
    def arrived_playable(self) -> bool:
        """Whether the .arrived tile can be played from the hand
        (i.e. whether it was drawn, not stolen to meld).
        """
        return any(tile is self.arrived for tile in self.hand)

@dataclass
class DiscardWhat(ArrivedIO):
    _question = Question.DISCARD_WHAT

    last_meld: Optional[Meld]

    def answer(self, ans: Tile):
        return super().answer(ans)

@dataclass
class MeldFromDiscardQ(ArrivedIO):
    _question = Question.MELD_FROM_DISCARD_Q

    melds: List[Meld]

    def answer(self, ans: Optional[Meld] = None):
        return super().answer(ans)

@dataclass
class ReadyQ(UserIO):
    _question = Question.READY_Q

    def answer(self):
        return super().answer()

@dataclass
class RobKongQ(PlayeredIO):
    _question = Question.ROB_KONG_Q

    melds: List[Wu]

    def answer(self, ans: bool):
        return super().answer(ans)

@dataclass
class SelfDrawQ(ArrivedIO):
    _question = Question.SELF_DRAW_Q

    melds: List[Wu]

    def answer(self, ans: bool):
        return super().answer(ans)

@dataclass
class ShowEKFCP(ArrivedIO):
    _question = Question.SHOW_EKFCP_Q

    melds: List[Kong]

    def answer(self, ans: Optional[Kong] = None):
        return super().answer(ans)

@dataclass
class ShowEKFEP(ArrivedIO):
    _question = Question.SHOW_EKFEP_Q

    melds: List[Kong]

    def answer(self, ans: Optional[Kong] = None):
        return super().answer(ans)

@dataclass
class WhichWu(UserIO):
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
    """The result of a hand."""
    NORMAL = 0
    GOULASH = 1
    DEALER_WON = 2

@dataclass
class HandEnding:
    _result: ClassVar[HandResult]

    @property
    def result(self) -> HandResult:
        from warnings import warn
        warn('The result attribute is deprecated '
             'in favor of checking the type of the result '
             'using isinstance().', DeprecationWarning)
        return self._result

    hand: Hand

    def answer(self, ans=None):
        return _answer(self.hand.gen, ans)

@dataclass
class NormalHandEnding(HandEnding):
    _result = HandResult.NORMAL

    winner: Player
    wu: Wu
    choice: List[Meld]

    def faan(self) -> Tuple[int, WuFlag]:
        """Calculate the faan for this hand."""
        points = self.wu.faan(self.choice, (self.winner.seat, self.hand.wind))
        bonus = self.winner.bonus_faan()
        return (points[0] + bonus[0], points[1] | bonus[1])

    def points(self, min_faan: int = 3,
               table: Optional[Mapping[int, int]] = None
               ) -> Tuple[List[int], Optional[WuFlag]]:
        """Calculate the change in points for each player.

        Args:
        min_faan: Minimum faan for hand to be recognized as valid winning hand.
        table: Mapping of faan to base points. The largest faan value is assumed
            to be the limit, and values larger than it will be mapped to it.

        Returns:
            A list of four point deltas, representing each player, and
            the flags that apply to this hand. If the faan is not enough,
            ``([0, 0, 0, 0], None)`` is returned.
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
    _result = HandResult.GOULASH

    def faan(self) -> Tuple[int, None]:
        """Goulash endings have no faan and no flags."""
        return (0, None)

    def points(self, min_faan: int = 3,
               table: Optional[Mapping[int, int]] = None
               ) -> Tuple[List[int], None]:
        return ([0, 0, 0, 0], None)

class DealerWon(NormalHandEnding):
    _result = HandResult.DEALER_WON

HandEndingType = Union[NormalHandEnding, Goulash, DealerWon]

YieldType = Union[UserIOType, HandEndingType, None]
