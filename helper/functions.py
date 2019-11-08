from time import sleep
import numpy as np

from PyQt5.QtCore import QByteArray


def createQByteArray(svg):
    data = QByteArray()
    data.append(str(svg))
    return data

# Toggle generator. Returns a and b alternatingly on next()
def toggle(a, b, yield_a=True):
	while True:
		(yield a) if yield_a else (yield b)
		yield_a = not yield_a


def parse_fen_to_nparray(fen):
	np.array(np.mat('1 2; 3 4'), subok=True)