from time import sleep

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

