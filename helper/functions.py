import os
import numpy as np
from time import sleep

from PyQt5.QtCore import QByteArray


def createQByteArray(svg):
    data = QByteArray()
    data.append(str(svg))
    return data

# Toggle generator. Returns a or b alternatingly on next()
def toggle(a, b, yield_a=True):
    while True:
        (yield a) if yield_a else (yield b)
        yield_a = not yield_a


def parse_fen_to_nparray(fen):
    np.array(np.mat('1 2; 3 4'), subok=True)

def create_board_np_array(board):
    b = []
    for j in range(8):
        l = [] 
        for i in range(8):
            p = board.piece_at(i + 8*j)
            if not p: p = '.'
            l.append(str(p))
        b.append(l)
    print(np.array(b))

def uniquename(wish):
    parts = wish.split('.')
    i = 0
    while True:
        name = '.'.join(parts[:-1]) + (str(i) if i > 0 else '') + '.' + parts[-1]
        if os.path.isfile(name):
            i += 1
        else:
            yield name


