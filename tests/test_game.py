from typing import Type
import pytest
import mahjong.game as game

@pytest.mark.parametrize('ending_type', (
    game.HandStart, game.TurnNext, game.NextSeat,
    game.JumpSeat, game.TurnTied, game.TurnWon
))
def test_TurnEnding(ending_type: Type[game.TurnEnding]):
    assert issubclass(ending_type, game.TurnEnding), "incorrect inheritance"

def test_Game():
    gm = game.Game()
    assert isinstance(gm.players, list), "did not set players"
    assert all(isinstance(p, game.Player) for p in gm.players), \
        "players are not Players"
