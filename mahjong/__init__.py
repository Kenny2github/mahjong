"""
Mahjong
-------

Abstract away the logic of mahjong games (for oh, it is complicated!)
Only worry about the representation.

Example Usage
=============

.. code-block:: python
    >>> game = mahjong.Game()
"""

__version__ = "1.0.0"
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