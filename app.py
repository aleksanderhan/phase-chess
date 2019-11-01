import sys
import numpy as np

from chess import Board, Move
from chess.svg import board as boardToSvg

from PyQt5.QtWidgets import QApplication, QLineEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import QByteArray
from PyQt5.QtSvg import QSvgWidget


class BoardView(QSvgWidget):

    def __init__(self, board):
        super().__init__()
        self.board = board

    def mousePressEvent(self, event):
        board_pos = self.calculate_board_position(event)

    def mouseReleaseEvent(self, event):
        print(event)

    def mouseMoveEvent(self, event):
        board_pos = self.calculate_board_position(event)

    # return the board position as an algebraic notation string, or None
    def calculate_board_position(self, event):
        x = event.pos().x()
        y = event.pos().y()
        print(x, y)

    def refresh(self):
        svg_board = boardToSvg(self.board)
        data = self.create_QByteArray(svg_board)
        self.load(data)

    @staticmethod
    def create_QByteArray(svg):
        data = QByteArray()
        data.append(str(svg))
        return data


class Main(QWidget):

    EXIT = set(['quit', 'exit', 'qq'])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = Board()

        self.board_view = BoardView(self.board)
        self.command = QLineEdit()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.board_view)
        self.layout.addWidget(self.command)

        self.setLayout(self.layout)
        self.setGeometry(150, 150, 800, 800)
        self.board_view.refresh()
        self.show()

        # Signaling
        self.command.returnPressed.connect(self.execute_command)

    def execute_command(self):
        cmd = self.command.text()
        self.command.clear()
        if cmd.lower() in self.EXIT:
            exit(0)
        elif cmd == 'tt':
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
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
