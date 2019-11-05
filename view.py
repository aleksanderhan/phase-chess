from PyQt5.QtWidgets import QWidget, QGridLayout
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtSvg import QSvgWidget

from helper.functions import createQByteArray


class BoardView(QWidget):

    def __init__(self, svg_board, **kwargs):
        super().__init__(**kwargs)
        self.svgWidget = QSvgWidget()
        layout = EvenLayout(self)
        layout.addWidget(self.svgWidget, 0, 0)

        self.press_pos = None
        self.refresh(svg_board)

    def refresh(self, svg_board):
        data = createQByteArray(svg_board)
        self.svgWidget.load(data)

    def mousePressEvent(self, event):
        self.press_pos = self.calculate_board_position(event)

    def mouseReleaseEvent(self, event):
        if self.press_pos is not None:
            release_pos = self.calculate_board_position(event)
            if release_pos is not None:
                move = self.press_pos + release_pos
                if self.press_pos == release_pos:
                    move = '0000' # uci null move
                self.parent().execute_game_command(move)

    def mouseMoveEvent(self, event):
        # TODO: Implement drag piece-icon
        pass

    # Returns the board position as an algebraic notation string, or None
    def calculate_board_position(self, event):
        margin = self.svgWidget.size()*0.05 + QSize(2, 2)
        square = (self.svgWidget.size() - 2*margin)/8
        offset = (self.size() - self.svgWidget.size())/2. + margin
        x_coordinate =  event.pos().x() - offset.width()
        y_coordinate = offset.height() + 8*square.height() - event.pos().y()
        x_pos = int(1 + x_coordinate/square.width())
        y_pos = int(1 + y_coordinate/square.height())

        if (x_pos > 8 or x_pos < 1 or y_pos > 8 or y_pos < 1):
            return None
        else:
            return 'abcdefgh'[x_pos - 1] + str(y_pos)


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
