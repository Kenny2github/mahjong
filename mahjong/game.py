"""All game-process-related classes."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Mapping, Optional, \
    Tuple, Union, Dict, overload
from itertools import combinations
import random
from .tiles import BonusTile, Bonuses, Honors, Simples, Tile, Wind
from .melds import Chow, Kong, Meld, Pong, Wu, WuFlag
from .players import Player
from . import qna

__all__ = [
    'Game',
    'Round',
    'Hand',
    'Turn',
]

# data classes

class TurnEnding:
    pass

@dataclass
class HandStart(TurnEnding):
    seat: Wind

@dataclass
class TurnNext(TurnEnding):
    discard: Tile
    seat: Wind
    prev_seat: Wind

@dataclass
class NextSeat(TurnNext):
    offered: bool = False

@dataclass
class JumpSeat(TurnNext):
    jumped_with: Meld

@dataclass
class TurnTied(TurnEnding):
    pass

@dataclass
class TurnWon(TurnEnding):
    winner: Player
    wu: Wu

# game process classes

class Game:
    """Represents an entire game (consisting of 4 Rounds)."""

    round: Round
    players: List[Player]

    def __init__(self, **house_rules):
        self.init_players()
        self.extra_hands = house_rules.pop('extra_hands', True)

    def play(self) -> Union[qna.UserIOType, qna.HandEndingType]:
        """Play the game!

        Starts and stores a generator.
        Returns the first request for user input.
        """
        if hasattr(self, 'gen'):
            raise RuntimeError('Game already started!')
        self.gen = self.execute()
        question = next(self.gen)
        return question

    def execute(self):
        """Generator-coroutine-based interface to play the game."""
        for i in range(4): # Step 01, 03
            self.round = Round(self)
            yield from self.round.execute(i) # Step 02
            yield qna.ReadyQ(gen=self.gen)

    def init_players(self: Union[Game, Hand]) -> None:
        """Setup players."""
        self.players = [Player(i) for i in range(4)]

class Round:
    """Represents one four(+)-hand round of Mahjong."""

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
            result: qna.HandEndingType = (
                yield from self.hand.execute(i)) # Step 05
            if isinstance(result, qna.NormalHandEnding): # Step 06
                i += 1 # Step 04
                j += 1
            elif not self.game.extra_hands: # house rules
                i += 1
                j += 1
            i %= 4
            yield result

class Hand:
    """Represents one full hand of Mahjong."""

    wind: Wind
    turn: Turn
    round: Optional[Round]
    wall: List[Tile]
    discarded: List[Tile]
    discarders: List[Player]
    ending: Optional[TurnEnding] = None
    turncount: int = 0

    # key got last meld from value, and then self drew
    _12_piece: Dict[Player, Player]
    # key got last dragon meld from value, and then self drew
    _gave_dragon: Dict[Player, Player]
    # key got kong from value, and then self drew from the kong
    _gave_kong: Dict[Player, Player]

    @overload
    def __init__(self, round_or_players: Round):
        """Setup a hand.

        Pass the :class:`Round`_ explicitly if you have control over Round
        machinery *and* Game machinery (it will reach into the round's game
        attribute to get the game's players).

        Otherwise, this is the default invocation by the Round machinery.
        """

    @overload
    def __init__(self, round_or_players: List[Player]):
        """Setup a hand.

        Pass ``[p1, p2, p3, p4]`` if you want more control over how hands
        are played and have control over the players list.
        """

    @overload
    def __init__(self, round_or_players: None):
        """Setup a hand.

        Pass ``None`` if this hand is intended to be played standalone.
        The players will be initialized automagically.
        """

    def __init__(self, round_or_players: Union[Round, List[Player], None]):
        """Setup a hand."""
        if isinstance(round_or_players, Round):
            self.round = round_or_players
            self.players = self.round.game.players
        elif isinstance(round_or_players, list):
            self.round = None
            self.players = round_or_players
        else:
            self.round = None
            Game.init_players(self)
        self._12_piece = {}
        self._gave_dragon = {}
        self._gave_kong = {}

    def play(self, wind: Wind = Wind.EAST
             ) -> Union[qna.UserIOType, qna.HandEndingType]:
        """Play the hand standalone.

        ``wind``: The prevailing wind for this hand.

        Starts and stores a generator.
        Returns the first request for user input.
        """
        if hasattr(self, 'gen'):
            raise RuntimeError('Game already started!')
        if self.round is not None:
            raise RuntimeError('This Hand is part of a Round '
                               'and cannot be played standalone.')
        self.gen = self.execute(wind)
        try:
            question = next(self.gen)
        except StopIteration as exc:
            return exc.value
        return question

    def execute(self, wind: int):
        """Play a hand till it ends."""
        if not hasattr(self, 'gen') and self.round is not None:
            self.gen = self.round.game.gen
        self.wind = Wind(wind)
        self.shuffle() # Step 08
        self.deal() # Step 09
        # Sets up Step 12
        ending: TurnEnding = HandStart(seat=self.wind)
        self.turncount = 0
        while not isinstance(ending, (TurnTied, TurnWon)) and self.wall:
            self.turn = Turn(self)
            # Step 13
            ending = (yield from self.turn.execute(ending, self.turncount))
            self.turncount += 1
        self.ending = ending
        # Step 15
        if isinstance(ending, TurnTied) or not self.wall:
            # tie
            return qna.Goulash(hand=self)
        assert isinstance(ending, TurnWon)
        if len(self.wall) <= 0:
            ending.wu.base_flags |= WuFlag.LAST_CATCH
        if ending.winner in self._gave_dragon:
            ending.wu.base_flags |= WuFlag.GAVE_DRAGON
            ending.wu.discarder = self._gave_dragon[ending.winner].seat
        if WuFlag.SELF_DRAW in ending.wu.base_flags \
                and ending.winner in self._12_piece:
            ending.wu.base_flags |= WuFlag.TWELVE_PIECE
            ending.wu.discarder = self._12_piece[ending.winner].seat
        if len(ending.wu.melds) > 1:
            question = qna.WhichWu(gen=self.gen, melds=ending.wu.melds)
            answer: List[Meld] = (yield question)
        else:
            answer = ending.wu.melds[0]
        if ending.winner is self.players[self.wind]:
            return qna.DealerWon(hand=self, winner=ending.winner,
                                 wu=ending.wu, choice=answer)
        return qna.NormalHandEnding(hand=self, winner=ending.winner,
                                    wu=ending.wu, choice=answer)

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
        self.discarders = []

    def deal(self):
        players = self.players
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
        self.players = self.hand.players
        self.gen = self.hand.gen

    def execute(self, last_ending: Union[HandStart, TurnNext], turncount: int):
        if last_ending.seat is None:
            raise ValueError('Must have valid seat')
        player = self.players[last_ending.seat]
        meld: Union[Meld, bool, None] = None
        if isinstance(last_ending, JumpSeat):
            meld = last_ending.jumped_with
            self.hand.discarded.pop() # Step 18
            self.hand.discarders.pop()
            old_count = len(player.shown)
            old_drag = self.all_dragons(player)
            player.show_meld(last_ending.discard, meld)
            if old_count == 3 and len(player.shown) == 4:
                self.hand._12_piece[player] = self.players[
                    last_ending.prev_seat]
            if not old_drag and self.all_dragons(player):
                self.hand._gave_dragon[player] = self.players[
                    last_ending.prev_seat]
            del old_count, old_drag
        elif isinstance(last_ending, NextSeat) and not last_ending.offered:
            # Step 16
            meld = (yield from self.melds_from_discard(player, last_ending))
        if isinstance(meld, Wu):
            if turncount == 1:
                meld.base_flags |= WuFlag.EARTHLY
            return TurnWon(winner=player, wu=meld)
        if isinstance(meld, Kong):
            wu, winner = (yield from self.check_kong_robbers(meld, player))
            if wu is not None and winner is not None:
                return TurnWon(winner=winner, wu=wu)
        arrived = None
        if isinstance(meld, Kong) or meld is None:
            kong: Optional[Kong] = None
            tries = 0
            wu, winner = None, None
            while 1:
                try:
                    drawn = player.draw(self.hand.wall) # Step 20
                except IndexError: # goulash time
                    return TurnTied()
                try:
                    flags = WuFlag.SELF_DRAW
                    if tries == 0 and turncount == 0:
                        flags |= WuFlag.HEAVENLY
                    elif tries == 1:
                        flags |= WuFlag.BY_KONG
                    elif tries > 1:
                        flags |= WuFlag.DOUBLE_KONG
                    if (WuFlag.BY_KONG in flags or WuFlag.DOUBLE_KONG in flags) \
                            and player in self.hand._gave_kong:
                        flags |= WuFlag.GAVE_KONG
                        discarder = self.hand._gave_kong[player].seat
                    else:
                        discarder = None
                    wu = Wu(player.hand, player.shown, drawn, discarder, flags)
                except ValueError:
                    pass
                else:
                    question = qna.SelfDrawQ(gen=self.gen, player=player,
                                             arrived=drawn, melds=[wu])
                    ans: bool = (yield question)
                    if ans:
                        return TurnWon(winner=player, wu=wu)
                    del ans
                arrived = drawn
                kong = (yield from self.check_ekfp(drawn, player))
                if kong is None:
                    self.hand._gave_kong.pop(player, None)
                    break
                player.shown.append(kong)
                wu, winner = (yield from self.check_kong_robbers(kong, player))
                if wu is not None and winner is not None:
                    return TurnWon(winner=winner, wu=wu)
                tries += 1
            del tries, flags, kong, wu, winner
        elif isinstance(last_ending, TurnNext):
            arrived = last_ending.discard
        player.hand.sort() # Step 26
        assert arrived is not None
        question = qna.DiscardWhat(gen=self.gen, player=player,
                                   arrived=arrived, last_meld=meld)
        answer: Tile = (yield question) # Step 27
        # Step 28
        player.hand.remove(answer)
        self.hand.discarded.append(answer)
        self.hand.discarders.append(player)
        # Step 29
        thief, meld = (yield from self.check_others_melds(answer, player))
        if thief is None or isinstance(meld, bool):
            assert isinstance(meld, bool)
            # Step 14
            return NextSeat(
                discard=answer, offered=meld,
                seat=Wind((player.seat + 1) % 4), prev_seat=player.seat)
        # Step 31
        if isinstance(meld, Wu):
            return TurnWon(winner=thief, wu=meld)
        return JumpSeat(discard=answer, seat=thief.seat,
                        jumped_with=meld, prev_seat=player.seat)

    @staticmethod
    def all_dragons(player: Player) -> bool:
        dragons = [False, False, False]
        for m in player.shown:
            if m.tiles[0].suit == Honors.LONG:
                dragons[m.tiles[0].number] = True
        return all(dragons)

    def melds_from_discard(self, player: Player, last_ending: TurnNext):
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
        try:
            wu = Wu([*player.hand, last_ending.discard], player.shown,
                    last_ending.discard, last_ending.prev_seat)
        except ValueError:
            pass
        else:
            melds.append(wu)
        if melds:
            # Step 17
            question = qna.MeldFromDiscardQ(gen=self.gen, player=player,
                                            arrived=last_ending.discard,
                                            melds=melds)
            answer: Optional[Meld] = (yield question)
            if answer is not None:
                self.hand.discarded.pop() # Step 18
                self.hand.discarders.pop()
                player.show_meld(last_ending.discard, answer)
            return answer
        return None

    def check_ekfp(self, draw: Tile, player: Player):
        """Check whether an Exposed Kong From (any) Pong is possible."""
        kongs: List[Kong] = []
        for quadruplet in combinations(player.hand, 4):
            if all(tile == quadruplet[0] for tile in quadruplet):
                # Exposed Kong From Concealed Pong
                kong = Kong(quadruplet)
                kongs.append(kong)
        if kongs:
            question = qna.ShowEKFCP(gen=self.gen, melds=kongs,
                                     player=player, arrived=draw)
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
            question = qna.ShowEKFEP(
                gen=self.gen, melds=kongs, player=player, arrived=draw)
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
                wu = Wu(p.hand + [tile], p.shown, tile, victim.seat, WuFlag.ROBBING_KONG)
            except ValueError:
                continue
            question = qna.RobKongQ(gen=self.gen, melds=[wu], player=p)
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
                wu = Wu([*player.hand, discard], player.shown, discard, victim.seat)
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
            question = qna.MeldFromDiscardQ(
                gen=self.gen, melds=overall[player],
                player=player, arrived=discard)
            answer: Optional[Meld] = (yield question)
            if answer is not None:
                if isinstance(answer, Kong) \
                        and discard not in self.hand.discarded[:-1]:
                    self.hand._gave_kong[player] = victim
                return (player, answer)
        return (None, bool(overall[self.players[(victim.seat + 1) % 4]]))
