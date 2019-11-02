from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtCore import QRect


class EvenLayout(QGridLayout):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSpacing(0)

    def setGeometry(self, oldRect):
        # assuming that the minimum size is 50 pixel, find the minimum possible
        # "extent" based on the geometry provided
        minSize = max(50 * 8, min(oldRect.width(), oldRect.height()))
        # create a new squared rectangle based on that size
        newRect = QRect(0, 0, minSize, minSize)
        # move it to the center of the old one
        newRect.moveCenter(oldRect.center())
        super().setGeometry(newRect)
