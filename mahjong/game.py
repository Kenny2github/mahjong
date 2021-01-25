"""All game-process-related classes."""
from __future__ import annotations
from enum import Enum
from typing import Generator, List, Mapping, NamedTuple, Optional, Tuple, TypeVar, Union
from itertools import combinations
import random
from .tiles import BonusTile, Bonuses, Honors, Simples, Tile, Wind
from .melds import Chow, Kong, Meld, Pong, Wu, WuFlag
from .players import Player

# This is a really big file, but there's no way around it:
# All of the classes depend on each other, so there's
# a lot of circular imports if they are in different files.

__all__ = [
    'TurnEnding',
    'HandEnding',
    'Question',
    'UserIO',
    'HandResult',

    'Game',
    'Round',
    'Hand',
    'Turn',
]

# data classes

class Answerable:
    """ABC for yielded objects that passthru generator sending."""
    gen: Generator
    def answer(self: YieldType, ans=None) -> YieldType:
        """Send the answer to the internal generator."""
        try:
            return self.gen.send(ans)
        except StopIteration:
            return None

class TurnEnding(NamedTuple):
    winner: Optional[Player] = None
    discard: Optional[Tile] = None
    seat: Optional[int] = None
    wu: Optional[Wu] = None
    jumped_with: Optional[Meld] = None
    offered: bool = False

class HandEnding(NamedTuple):
    result: HandResult
    gen: Generator
    winner: Optional[Player] = None
    wu: Optional[Wu] = None
    choice: Optional[List[Meld]] = None

    def answer(self, ans=None):
        return Answerable.answer(self, ans)

class Question(Enum):
    MELD_FROM_DISCARD_Q = 16
    SHOW_EKFCP_Q = 23
    SHOW_EKFEP_Q = 24
    DISCARD_WHAT = 27
    ROB_KONG_Q = 33
    WHICH_WU = 40
    READY_Q = 0

class UserIO(NamedTuple, Answerable):
    question: Question
    gen: Generator
    melds: Union[List[Meld], List[List[Meld]], None] = None
    player: Optional[Player] = None
    arrived: Optional[Tile] = None
    last_meld: Optional[Meld] = None

    @property
    def hand(self) -> List[Tile]:
        """Shortcut to .player.hand"""
        return self.player.hand

    @property
    def shown(self) -> List[Meld]:
        """Shortcut to .player.shown"""
        return self.player.shown

    def answer(self, ans=None):
        return Answerable.answer(self, ans)

    def __repr__(self) -> str:
        return f'UserIO(question={self.question}, melds={self.melds}, '\
            f'arrived={self.arrived}, player={self.player})'

class HandResult(Answerable, Enum):
    """The result of a hand."""
    NORMAL = 0
    GOULASH = 1
    DEALER_WON = 2

YieldType = Union[UserIO, HandEnding, Answerable, None]

# game process classes

class Game:
    """Represents an entire game (consisting of at least 16 Rounds)."""

    round: Round

    def __init__(self, **house_rules):
        self.init_players()
        self.extra_hands = house_rules.pop('extra_hands', True)

    def play(self) -> UserIO:
        """Play the game!

        Starts and stores a generator.
        Returns the first request for user input.
        """
        if hasattr(self, 'gen'):
            raise RuntimeError('Game already started!')
        self.gen = self.execute()
        question = next(self.gen)
        if isinstance(question, UserIO):
            return question
        raise RuntimeError('This should never happen. Contact the developer.')

    def execute(self):
        """Generator-coroutine-based interface to play the game."""
        for i in range(4): # Step 01, 03
            self.round = Round(self)
            yield from self.round.execute(i) # Step 02
            yield UserIO(Question.READY_Q, self.gen)


    def init_players(self) -> None:
        """Setup players."""
        self.players = [Player(i) for i in range(4)]

class Round:
    """Represents one four-hand round of Mahjong."""

    hand: Hand
    game: Game
    wind: Wind

    def __init__(self, game: Game):
        self.game = game

    def execute(self, wind: int):
        """Play at least four hands."""
        self.wind = Wind(wind)
        i = int(self.wind)
        j = 0
        while j < 4: # Step 07
            self.hand = Hand(self)
            result: HandEnding = (yield from self.hand.execute(i)) # Step 05
            if result.result is HandResult.NORMAL: # Step 06
                i += 1 # Step 04
                j += 1
            elif not self.game.extra_hands: # house rules
                i += 1
                j += 1
            i %= 4
            yield result

class Hand:
    """Represents one full hand of Mahjong."""

    turn: Turn
    round: Round
    wall: List[Tile]
    discarded: List[Tile]
    ending: Optional[TurnEnding] = None
    turncount: Optional[int] = None

    def __init__(self, round: Round):
        self.round = round

    def execute(self, wind: int):
        """Play a hand till it ends."""
        self.wind = Wind(wind)
        self.shuffle() # Step 08
        self.deal() # Step 09
        # Sets up Step 12
        ending: TurnEnding = TurnEnding(seat=self.wind)
        self.turncount = 0
        while ending.winner is None and self.wall:
            self.turn = Turn(self)
            # Step 13
            ending = (yield from self.turn.execute(ending, self.turncount))
            self.turncount += 1
        self.ending = ending
        # Step 15
        if ending.winner is None and not self.wall:
            # tie
            return HandEnding(HandResult.GOULASH, self.round.game.gen)
        if len(self.wall) <= 1:
            ending.wu.flags |= WuFlag.LAST_CATCH
        if len(ending.wu.melds) > 1:
            question = UserIO(Question.WHICH_WU, self.round.game.gen,
                              melds=ending.wu.melds)
            answer = (yield question)
        else:
            answer = ending.wu.melds[0]
        if ending.winner is self.round.game.players[self.wind]:
            return HandEnding(
                HandResult.DEALER_WON, self.round.game.gen,
                ending.winner, ending.wu, answer)
        return HandEnding(
            HandResult.NORMAL, self.round.game.gen, ending.winner, ending.wu, answer)

    def shuffle(self):
        """Generate and shuffle a new wall."""
        wall = []
        # simples
        for suit in Simples:
            for num in range(9):
                wall.extend([Tile(suit, num) for _ in range(4)])
        # honors
        for wind in range(4):
            wall.extend([Tile(Honors.FENG, wind) for _ in range(4)])
        for dragon in range(3):
            wall.extend([Tile(Honors.LONG, dragon) for _ in range(4)])
        # bonuses
        for i in range(4):
            wall.append(BonusTile(Bonuses.HUA, i))
            wall.append(BonusTile(Bonuses.GUI, i))
        random.shuffle(wall)
        self.wall = wall
        self.discarded = []

    def deal(self):
        players = self.round.game.players
        for player in players:
            player.__init__(player.seat)
        # Step 09
        for _ in range(13):
            for player in players:
                player.draw(self.wall)
        for player in players:
            player.hand.sort()

class Turn:
    """Handles the turn."""

    hand: Hand

    def __init__(self, hand: Hand):
        self.hand = hand
        self.players = self.hand.round.game.players
        self.gen = self.hand.round.game.gen

    def execute(self, last_ending: TurnEnding, turncount: int):
        if last_ending.seat is None:
            raise ValueError('Must have valid seat')
        player = self.players[last_ending.seat]
        meld: Optional[Meld] = None
        if last_ending.jumped_with is not None and last_ending.discard is not None:
            meld = last_ending.jumped_with
            self.hand.discarded.pop() # Step 18
            player.show_meld(last_ending.discard, meld)
        elif last_ending.discard is not None and not last_ending.offered:
            # Step 16
            meld: Optional[Meld] = (yield from self.melds_from_discard(
                player, last_ending))
        if isinstance(meld, Wu):
            if turncount == 1:
                meld.flags |= WuFlag.EARTHLY
            return TurnEnding(winner=player, wu=meld)
        if isinstance(meld, Kong):
            wu, winner = (yield from self.check_kong_robbers(meld, player))
            if wu is not None:
                return TurnEnding(winner=winner, wu=wu)
        if isinstance(meld, Kong) or meld is None:
            arrived = None
            kong: Optional[Kong] = None
            tries = 0
            wu, winner = None, None
            while 1:
                try:
                    drawn = player.draw(self.hand.wall) # Step 20
                except IndexError: # goulash time
                    return TurnEnding()
                try:
                    flags = WuFlag.SELF_DRAW
                    if tries == 0 and turncount == 0:
                        flags |= WuFlag.HEAVENLY
                    elif tries == 1:
                        flags |= WuFlag.BY_KONG
                    elif tries > 1:
                        flags |= WuFlag.DOUBLE_KONG
                    return TurnEnding(winner=player, wu=Wu(
                        player.hand, player.shown, drawn, flags))
                except ValueError:
                    pass
                arrived = drawn
                kong = (yield from self.check_ekfp(drawn, player))
                if kong is None:
                    break
                player.shown.append(kong)
                wu, winner = (yield from self.check_kong_robbers(kong, player))
                if wu is not None:
                    return TurnEnding(winner=winner, wu=wu)
                tries += 1
            del tries, flags, kong, wu, winner
        else:
            arrived = last_ending.discard
        player.hand.sort() # Step 26
        question = UserIO(Question.DISCARD_WHAT, self.gen,
                          player=player, arrived=arrived, last_meld=meld)
        answer: Tile = (yield question) # Step 27
        # Step 28
        player.hand.remove(answer)
        self.hand.discarded.append(answer)
        # Step 29
        thief, meld = (yield from self.check_others_melds(answer, player))
        if thief is None and isinstance(meld, bool):
            # Step 14
            return TurnEnding(discard=answer, offered=meld,
                          seat=(player.seat + 1) % 4)
        # Step 31
        if isinstance(meld, Wu):
            return TurnEnding(winner=thief, wu=meld)
        return TurnEnding(discard=answer, seat=thief.seat, jumped_with=meld)

    def melds_from_discard(self, player: Player, last_ending: TurnEnding):
        """Check for possible melds to make from the discard tile."""
        if last_ending.discard is None:
            return None
        melds: List[Meld] = []
        for pair in combinations(player.hand, 2):
            meld = Wu.get_triplet([*pair, last_ending.discard])
            if meld is not None and meld not in melds:
                melds.append(meld)
        for triplet in combinations(player.hand, 3):
            if all(tile == last_ending.discard for tile in triplet):
                # Exposed Kong
                meld = Kong([*triplet, last_ending.discard])
                if meld not in melds:
                    melds.append(meld)
        if melds:
            # Step 17
            question = UserIO(Question.MELD_FROM_DISCARD_Q, self.gen,
                              melds, player, last_ending.discard)
            answer: Optional[Meld] = (yield question)
            if answer is not None:
                self.hand.discarded.pop() # Step 18
                player.show_meld(last_ending.discard, answer)
            return answer
        try:
            return Wu(player.hand, player.shown, last_ending.discard)
        except ValueError:
            return None

    def check_ekfp(self, draw: Tile, player: Player):
        """Check whether an Exposed Kong From (any) Pong is possible."""
        kongs: List[Meld] = []
        for quadruplet in combinations(player.hand, 4):
            if all(tile == quadruplet[0] for tile in quadruplet):
                # Exposed Kong From Concealed Pong
                kong = Kong(quadruplet)
                kongs.append(kong)
        if kongs:
            question = UserIO(Question.SHOW_EKFCP_Q, self.gen,
                              melds=kongs, player=player, arrived=draw)
            answer: Optional[Kong] = (yield question)
            if answer is not None:
                for tile in answer.tiles:
                    player.hand.remove(tile)
                return answer
            kongs = []
        for meld in player.shown:
            if not isinstance(meld, Pong):
                continue
            try:
                match = player.hand.index(meld.tiles[0])
            except ValueError:
                continue
            if meld.tiles[0] in player.hand:
                kong = Kong(meld.tiles + (player.hand[match],))
                kongs.append(kong)
        if kongs:
            question = UserIO(Question.SHOW_EKFEP_Q, self.gen,
                              melds=kongs, player=player, arrived=draw)
            answer: Optional[Kong] = (yield question)
            if answer is not None:
                player.shown.remove(Pong(answer.tiles[:3]))
                player.hand.remove(answer.tiles[0])
            return answer
        return None

    def check_kong_robbers(self, kong: Kong, victim: Player):
        """Check for anyone who could potentially rob the Kong for a win."""
        tile = kong.tiles[0] # any tile will do
        for p in self.players:
            if p is victim:
                continue
            try:
                wu = Wu(p.hand + [tile], p.shown, tile, WuFlag.ROBBING_KONG)
            except ValueError:
                continue
            question = UserIO(Question.ROB_KONG_Q, self.gen,
                              melds=[wu], player=p)
            answer: bool = (yield question)
            if answer:
                return (wu, p)
        return (None, None)

    def check_others_melds(self, discard: Tile, victim: Player):
        """Check for anyone who could potentially meld from the discard."""
        overall: Mapping[Player, List[Meld]] = {}
        for player in self.players:
            if player is victim:
                continue
            melds: List[Meld] = overall.setdefault(player, [])
            for pair in combinations(player.hand, 2):
                try:
                    meld = Pong([*pair, discard])
                except ValueError:
                    pass
                else:
                    if meld not in melds:
                        melds.append(meld)
                if player is self.players[(victim.seat + 1) % 4]:
                    try:
                        meld = Chow([*pair, discard])
                    except ValueError:
                        continue
                    if meld not in melds:
                        melds.append(meld)
            for triplet in combinations(player.hand, 3):
                try:
                    meld = Kong([*triplet, discard])
                except ValueError:
                    continue
                if meld not in melds:
                    melds.append(meld)
            try:
                wu = Wu([*player.hand, discard], player.shown, discard)
            except ValueError:
                pass
            else:
                if wu not in melds:
                    melds.append(wu)
        for melds in overall.values():
            melds.sort()
        pairs: List[Tuple[Player, Meld]] = [
            (p, melds[0]) for p, melds in overall.items() if melds]
        pairs.sort(key=lambda i: i[1])
        for player, meld in pairs:
            # Step 30, 32
            question = UserIO(
                Question.MELD_FROM_DISCARD_Q, self.gen, melds=overall[player],
                player=player, arrived=discard)
            answer: Optional[Meld] = (yield question)
            if answer is not None:
                return (player, answer)
        return (None, bool(overall[self.players[(victim.seat + 1) % 4]]))
