''' # comment out this opening triple quote to time Wu computation
import mahjong, time
start = time.time()
w = mahjong.melds.Wu.from_str("""
tong/4|tong/4|tong/4|tong/5|tong/6|tong/6|tong/6|tong/7
""".strip(),
melds=[mahjong.Pong.from_str('zhu/3|zhu/3|zhu/3'), mahjong.Chow.from_str('wan/1|wan/2|wan/3')],
arrived=mahjong.Tile.from_str('tong/4')
#map(mahjong.Chow.from_str, 'zhu/3|zhu/4|zhu/5,zhu/5|zhu/6|zhu/7,zhu/7|zhu/8|zhu/9'.split(','))
)
end = time.time()
print('\n'.join(f'{w.faan(meld)}: ' + ', '.join(str(i) for i in meld)
                for meld in set(tuple(meld) for meld in w.melds)))
print(w.max_faan())
print(f'in {end-start:.2f}s')
#'''
''' # comment out this opening triple quote to test dealing
from mahjong import Game, Round, Hand
game = Game()
round = Round(game)
hand = Hand(round)
hand.shuffle()
hand.deal()
for p in game.players:
    print('|'.join(map(str, p.hand)))
    print(', '.join(map(str, p.bonus)))
#'''
#''' # uncomment this opening triple quote when commenting out one elsewhere
import sys
from mahjong.game import Game, Hand
from mahjong import qna

if '--game' in sys.argv:
    game = Game(extra_hands=False)
else:
    game = Hand(None)
print('Note: all indexes are **1-based**.')
print('This is a rudimentary text-based mahjong implementation.')
print("It's purely as a proof-of-concept/manual testing method.")
print("It requires trust that each player won't look at the other's privacy.")
print("Please don't actually use this. Make something even a tiny bit better.")
print("With that said, let's start.")

question: qna.YieldType = game.play()
while question is not None:
    if isinstance(question, qna.UserIO):
        if isinstance(question, qna.ReadyQ):
            input('Hit Enter when ready for the next round.')
            question = question.answer()
            continue
        assert isinstance(question, qna.ArrivedIO)
        hand_minus_tile = [tile for tile in question.player.hand
                           if tile is not question.arrived]
        print('Question for Player #%s' % question.player.seat.value)
        print('Draw/Last discard: %s;' % question.arrived, 'Concealed:',
              ', '.join(map(str, hand_minus_tile)))
        print('Shown:', '\t'.join(map(str, question.shown)),
              '- Bonuses:', '|'.join(map(str, question.player.bonus)))
        if isinstance(question, qna.DiscardWhat):
            idx = int(input('Enter index of card to discard. 0 for draw. '))
            if idx == 0:
                if question.arrived in question.hand:
                    tile = question.arrived
                else:
                    tile = hand_minus_tile[0]
            elif idx > 0:
                tile = hand_minus_tile[idx-1]
            elif idx < 0:
                tile = hand_minus_tile[idx]
            else:
                tile = hand_minus_tile[0]
            print('Discarding', tile)
            question = question.answer(tile)
        elif isinstance(question, qna.MeldFromDiscardQ):
            print('Available melds to meld:', '\t'.join(map(str, question.melds)))
            try:
                idx = int(input('Enter index of meld to meld, or blank to not meld: '))
            except ValueError:
                question = question.answer(None)
            else:
                question = question.answer(question.melds[idx-1])
        elif isinstance(question, qna.ShowEKFEP):
            print('Available Kongs to expose from exposed Pongs:',
                  '\t'.join(map(str, question.melds)))
            try:
                idx = int(input('Enter index of Kong to expose, or blank to not expose: '))
            except ValueError:
                question = question.answer(None)
            else:
                question = question.answer(question.melds[idx-1])
        elif isinstance(question, qna.ShowEKFCP):
            print('Available Kongs to expose from concealed Pongs:',
                  '\t'.join(map(str, question.melds)))
            try:
                idx = int(input('Enter index of Kong to expose, or blank to not expose: '))
            except ValueError:
                question = question.answer(None)
            else:
                question = question.answer(question.melds[idx-1])
        elif isinstance(question, qna.SelfDrawQ):
            print('You can win by self-draw with:', question.melds[0])
            inp = '?'
            while inp not in {'y', 'n'}:
                inp = input('Do you want to? (y/n) ').casefold()
            question = question.answer(inp == 'y')
        elif isinstance(question, qna.RobKongQ):
            print('You can rob the last Kong to win with:', question.melds[0])
            inp = '?'
            while inp not in {'y', 'n'}:
                inp = input('Do you want to? (y/n) ').casefold()
            question = question.answer(inp == 'y')
        elif isinstance(question, qna.WhichWu):
            idx = int(input('Which Wu combo (enter index) do you want to win with? '))
            question = question.answer(question.melds[idx-1])
    elif isinstance(question, qna.HandEnding):
        if isinstance(question, qna.Goulash):
            print('Goulash! Nobody wins. Starting next game...')
        else:
            print('Player #%s won with %s (%s faan; %s points; %s)! Starting next game...' % (
                question.winner.seat.value, ','.join(map(str, question.choice)),
                question.faan()[0], *question.points(1)
            ))
        question = question.answer()
print('Game Over!')
#'''
