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