"""
Mahjong
=======

Abstract away the logic of Mahjong games (for oh, it is complicated!)
Only worry about the representation.

Example Usage
-------------

.. code-block:: python

    >>> import mahjong
    >>> game = mahjong.Game()
    >>> question = game.play()
    >>> next_question = question.answer(...)
    >>> ...

For full usage see the docs:
https://github.com/Kenny2github/mahjong/wiki
"""

__version__ = "2.0.0rc3"

__all__ = [
    'Game',
    'Hand',

    'players',
    'melds',
    'tiles',
    'game',
    'qna',
]

from . import players
from . import melds
from . import tiles
from . import game
from . import qna

from .game import Game, Hand
