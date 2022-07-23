from typing import Optional, Type, Union
import pytest
import mahjong.tiles as tiles

@pytest.mark.parametrize('ending_type', (
    tiles.Simples, tiles.Honors, tiles.Bonuses, tiles.Misc
))
def test_Suit(ending_type: Type[tiles.Suit]):
    assert issubclass(ending_type, tiles.Suit), "incorrect inheritance"

def test_Tile():
    tile = tiles.Tile(tiles.Simples.TONG, tiles.Wind.EAST)
    assert not isinstance(tile.number, tiles.Wind), "not converted"
    assert tile.number == 0, "converted incorrectly"
    tile = tiles.Tile(tiles.Honors.FENG, 0)
    assert isinstance(tile.number, tiles.Wind), "not converted"
    assert tile.number == tiles.Wind.EAST, "converted incorrectly"
    tile = tiles.Tile(tiles.Honors.LONG, 0)
    assert isinstance(tile.number, tiles.Dragon), "not converted"
    assert tile.number == tiles.Dragon.RED, "converted incorrectly"

    with pytest.raises(ValueError):
        tile = tiles.Tile(tiles.Bonuses.GUI, 0)
    with pytest.raises(ValueError):
        tile = tiles.Tile(tiles.Misc.UNKNOWN, 0)

@pytest.mark.parametrize(('tile_str', 'correct_tile', 'should_raise'), (
    ('tong/1', tiles.Tile(tiles.Simples.TONG, 0), None),
    ('zhu/2', tiles.Tile(tiles.Simples.ZHU, 1), None),
    ('long/3', tiles.Tile(tiles.Honors.LONG, 2), None),
    ('feng/4', tiles.Tile(tiles.Honors.FENG, 3), None),
    ('wan/5', tiles.Tile(tiles.Simples.WAN, 4), None),
    ('tong/10', None, ValueError),
    ('feng/5', None, ValueError),
    ('gui/4', tiles.BonusTile(tiles.Bonuses.GUI, 3), None),
    ('gui/5', None, ValueError),
))
def test_Tile_from_str(tile_str: str, correct_tile: Optional[tiles.Tile],
                       should_raise: Optional[Type[Exception]]):
    if should_raise is not None:
        with pytest.raises(should_raise):
            assert tiles.Tile.from_str(tile_str) == correct_tile
    else:
        assert tiles.Tile.from_str(tile_str) == correct_tile, "incorrect tile"


@pytest.mark.parametrize(('correct_str', 'tile'), (
    ('tong/1', tiles.Tile(tiles.Simples.TONG, 0)),
    ('zhu/2', tiles.Tile(tiles.Simples.ZHU, 1)),
    ('long/3', tiles.Tile(tiles.Honors.LONG, 2)),
    ('feng/4', tiles.Tile(tiles.Honors.FENG, 3)),
    ('wan/5', tiles.Tile(tiles.Simples.WAN, 4)),
    ('gui/1', tiles.BonusTile(tiles.Bonuses.GUI, 0)),
    ('hua/2', tiles.BonusTile(tiles.Bonuses.HUA, 1)),
))
def test_Tile_str_repr(correct_str: str, tile: tiles.Tile):
    assert str(tile) == repr(tile) == correct_str

@pytest.mark.parametrize(('tile1', 'tile2', 'value'), (
    (tiles.Tile(tiles.Simples.TONG, 0), tiles.Tile.from_str('tong/1'), True),
    (tiles.Tile(tiles.Simples.ZHU, 1), tiles.Tile.from_str('zhu/2'), True),
    (tiles.Tile(tiles.Honors.LONG, 2), tiles.Tile.from_str('long/3'), True),
    (tiles.Tile(tiles.Honors.FENG, 3), tiles.Tile.from_str('feng/4'), True),
    (tiles.Tile(tiles.Simples.WAN, 4), tiles.Tile.from_str('wan/5'), True),

    (tiles.Tile(tiles.Simples.TONG, 1), tiles.Tile.from_str('tong/1'), False),
    (tiles.Tile(tiles.Honors.LONG, 2), tiles.Tile.from_str('long/2'), False),
    (tiles.Tile(tiles.Honors.FENG, 3), tiles.Tile.from_str('feng/3'), False),
    (tiles.Tile(tiles.Simples.ZHU, 4), tiles.Tile.from_str('zhu/4'), False),
    (tiles.Tile(tiles.Simples.WAN, 5), tiles.Tile.from_str('wan/5'), False),

    (tiles.BonusTile(tiles.Bonuses.GUI, 0), tiles.Tile.from_str('gui/1'), True),
    (tiles.BonusTile(tiles.Bonuses.HUA, 0), tiles.Tile.from_str('hua/1'), True),
    (tiles.BonusTile(tiles.Bonuses.GUI, 1), tiles.Tile.from_str('gui/1'), False),
    (tiles.BonusTile(tiles.Bonuses.HUA, 1), tiles.Tile.from_str('hua/1'), False),
))
def test_Tile_eq(tile1: tiles.Tile, tile2: tiles.Tile, value: bool):
    if value:
        assert tile1 == tile2, "should be equal"
    else:
        assert tile1 != tile2, "should be inequal"

@pytest.mark.parametrize(('tile1', 'tile2', 'value_or_exc'), (
    (tiles.Tile.from_str('feng/1'), tiles.Tile.from_str('feng/2'), True),
    (tiles.Tile.from_str('long/2'), tiles.Tile.from_str('long/3'), True),
    (tiles.Tile.from_str('tong/3'), tiles.Tile.from_str('tong/4'), True),
    (tiles.Tile.from_str('zhu/4'), tiles.Tile.from_str('zhu/5'), True),
    (tiles.Tile.from_str('wan/5'), tiles.Tile.from_str('wan/6'), True),
    (tiles.Tile.from_str('gui/1'), tiles.Tile.from_str('gui/2'), True),
    (tiles.Tile.from_str('hua/2'), tiles.Tile.from_str('hua/3'), True),

    (tiles.Tile.from_str('feng/1'), tiles.Tile.from_str('feng/1'), False),
    (tiles.Tile.from_str('long/2'), tiles.Tile.from_str('long/2'), False),
    (tiles.Tile.from_str('tong/3'), tiles.Tile.from_str('tong/3'), False),
    (tiles.Tile.from_str('zhu/4'), tiles.Tile.from_str('zhu/4'), False),
    (tiles.Tile.from_str('wan/5'), tiles.Tile.from_str('wan/5'), False),
    (tiles.Tile.from_str('gui/1'), tiles.Tile.from_str('gui/1'), False),
    (tiles.Tile.from_str('hua/2'), tiles.Tile.from_str('hua/2'), False),

    (tiles.Tile.from_str('wan/9'), tiles.Tile.from_str('tong/1'), True),
    (tiles.Tile.from_str('tong/9'), tiles.Tile.from_str('zhu/1'), True),
    (tiles.Tile.from_str('zhu/9'), tiles.Tile.from_str('feng/1'), True),
    (tiles.Tile.from_str('feng/4'), tiles.Tile.from_str('long/1'), True),

    (tiles.Tile.from_str('gui/1'), tiles.Tile.from_str('hua/2'), False),
    (tiles.Tile.from_str('hua/1'), tiles.Tile.from_str('gui/2'), False),

    (tiles.Tile.from_str('tong/1'), 'tong/2', TypeError),
    (tiles.Tile.from_str('wan/8'), 'wan/9', TypeError),
))
def test_Tile_lt(tile1: tiles.Tile, tile2: tiles.Tile,
                 value_or_exc: Union[bool, Type[Exception]]):
    if isinstance(value_or_exc, bool):
        if value_or_exc:
            assert tile1 < tile2, "should be less"
        else:
            assert not (tile1 < tile2), "should not be less"
    else:
        with pytest.raises(value_or_exc):
            assert tile1 < tile2

def test_BonusTile():
    tile = tiles.BonusTile(tiles.Bonuses.GUI, 0)
    assert isinstance(tile.number, tiles.Season), "not converted"
    assert tile.number == tiles.Season.SPRING, "converted incorrectly"
    tile = tiles.BonusTile(tiles.Bonuses.HUA, 0)
    assert isinstance(tile.number, tiles.Flower), "not converted"
    assert tile.number == tiles.Flower.MEI, "converted incorrectly"

    with pytest.raises(ValueError):
        # testing typecheck; ignoring types
        tile = tiles.BonusTile(tiles.Simples.WAN, 0) # type: ignore
