"""
Mahjong
-------

Abstract away the logic of Mahjong games (for oh, it is complicated!)
Only worry about the representation.

Example Usage
=============

.. code-block:: python

    >>> import mahjong
    >>> game = mahjong.Game()
    >>> question = game.play()
    >>> next_question = question.answer(...)
    >>> ...

For full usage see the docs:
https://github.com/Kenny2github/mahjong/wiki
"""

__version__ = "2.0.0rc1"
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

    'Suit',
    'Simples',
    'Honors',
    'Bonuses',
    'Misc',
    'Wind',
    'Dragon',
    'Flower',
    'Season',
    'ORDER',
    'Number',

    'Tile',
    'BonusTile',

    'WuFlag',
    'Meld',
    'Pong',
    'Kong',
    'Chow',
    'Eyes',
    'Wu',
]

from .players import *
from .melds import *
from .tiles import *
from .game import *
