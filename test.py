import os
from time import clock
import random
import numpy as np

from chess import Board, Move
from stockfish import Stockfish


# Learning to beat stockfish
# Fra hver posisjon et steg fram spill sf vs sf til slutt og se resultatet. 

# Tren opp paa stockfish til stockfish er representert som policy
# Deretter tren med rf learning

board = Board()
stockfish = Stockfish(path='{}/stockfish-10-linux/stockfish_10_x64_modern'.format(os.getcwd()), depth=)
stockfish.set_fen_position(board.fen())
#print([str(p) for p in board.piece_map().values()])


def play_stockfish_move():
    stockfish.set_fen_position(board.fen())
    uci = stockfish.get_best_move()
    if uci:
        move = Move.from_uci(uci)
        board.push(move)

def play_random_move():
    uci = str(random.choice(list(board.legal_moves)))
    if uci:
        move = Move.from_uci(uci)
        board.push(move)


def play_sf_until_finished():
    i = 0
    while not board.is_game_over():
        play_stockfish_move()
        i += 1
    return i

def play_random_until_finished():
    i = 0
    while not board.is_game_over():
        try:
            play_random_move()
            i += 1
        except Exception as e:
            print(e)
    return i


# One move look-a-head, best-move checkmate check
def play_random_lookahead():
    i = 0
    while not board.is_game_over():
        play_stockfish_move()
        if board.is_game_over(): continue

        board.pop()
        play_random_move()
        i += 1
    return i
    

t0 = clock()
i = play_sf_until_finished()
dt = clock() - t0
print('elapsed time: ', round(dt*10, 2), 'iterations:', i)
board.reset()

t0 = clock()
i = play_random_until_finished()
dt = clock() - t0
print('elapsed time: ', round(dt*10, 2), 'iterations:', i)
board.reset()

t0 = clock()
i = play_random_lookahead()
dt = clock() - t0
print('elapsed time: ', round(dt*10, 2), 'iterations:', i)
