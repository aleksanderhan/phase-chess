from PyQt5.QtCore import QByteArray


def createQByteArray(svg):
    data = QByteArray()
    data.append(str(svg))
    return data

