from time import sleep

from PyQt5.QtCore import QByteArray


def createQByteArray(svg):
    data = QByteArray()
    data.append(str(svg))
    return data

# Toggle generator. Returns a and b alternatingly on next()
# toggle=True/False: returns a/b on first call
def toggle(a, b, toggle=True):
	while True:
		(yield a) if toggle else (yield b)
		toggle = not toggle

