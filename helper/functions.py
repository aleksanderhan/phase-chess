from PyQt5.QtCore import QByteArray


def create_QByteArray(svg):
    data = QByteArray()
    data.append(str(svg))
    return data

