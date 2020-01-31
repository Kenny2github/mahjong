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

__version__ = "0.0.1"
__all__ = [
    'Game',
    'Round',
    'Turn',
    'Players',
    'Player',
    'Pong',
    'Kong',
    'Chow',
    'Eyes',
    'Wu',
    'Tile',
    'Simples',
    'Honors',
    'Bonuses',
    'Misc',
    'Meld',
]

from .game import Game, Round, Turn
from .players import Players, Player
from .melds import Meld, Pong, Kong, Chow, Eyes, Wu
from .tiles import Tile, Simples, Honors, Bonuses, Misc
