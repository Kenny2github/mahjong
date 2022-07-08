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

For full usage see the docs: https://mahjong.rtfd.io
"""

__version__ = "2.0.0rc3"

from . import players
from . import melds
from . import tiles
from . import game
from . import qna
from .players import *
from .melds import *
from .tiles import *
from .game import *
from .qna import *

__all__ = [
    *players.__all__,
    *melds.__all__,
    *tiles.__all__,
    *game.__all__,
    *qna.__all__,
]
