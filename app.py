import sys
import numpy as np

from chess import Board, Move
from chess.svg import board as boardToSvg

from PyQt5.QtWidgets import QApplication, QLineEdit, QGridLayout, QWidget
from PyQt5.QtCore import QByteArray, Qt
from PyQt5.QtSvg import QSvgWidget

from helper.functions import create_QByteArray
from helper.classes import EvenLayout


class BoardView(QWidget):

    def __init__(self, board):
        super().__init__()
        self.svgWidget = QSvgWidget()
        layout = EvenLayout(self)
        layout.addWidget(self.svgWidget, 0, 0)

        self.board = board
        self.refresh()

    def mousePressEvent(self, event):
        print(self.svgWidget.size())
        board_pos = self.calculate_board_position(event)

    def mouseReleaseEvent(self, event):
        # print(event)
        pass

    def mouseMoveEvent(self, event):
        board_pos = self.calculate_board_position(event)

    # TODO: return the board position as an algebraic notation string, or None
    def calculate_board_position(self, event):
        screen_width = self.size().width()
        screen_height = self.size().height()
        x = screen_width - event.pos().x()
        y = screen_height - event.pos().y()
        print(x, y)

    def refresh(self):
        svg_board = boardToSvg(self.board)
        data = create_QByteArray(svg_board)
        self.svgWidget.load(data)


class Main(QWidget):

    EXIT = set(['exit', 'quit', 'qq'])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = Board()

        self.board_view = BoardView(self.board)
        self.command = QLineEdit()
        layout = QGridLayout(self)
        layout.addWidget(self.board_view)
        layout.addWidget(self.command)

        # Signaling
        self.command.returnPressed.connect(self.execute_command)

    def execute_command(self):
        cmd = self.command.text()
        self.command.clear()
        if cmd.lower() in self.EXIT:
            exit(0)
        elif cmd == 'lm':
            print(self.board.legal_moves)
        elif cmd == 'ss':
            print(self.board_view.size())
        else:
            try: 
                move = Move.from_uci(cmd)
                if move in self.board.legal_moves:
                    self.board.push(move)
                    self.board_view.refresh()
                else:
                    print('Illegal move!')
            except ValueError as ve:
                print('Command not recognized.', ve)


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = Main()
        window.setGeometry(150, 150, 800, 800)
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
