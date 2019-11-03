import sys, os
import random
import numpy as np

from chess import Board, Move
from chess.svg import board as boardToSvg
from stockfish import Stockfish

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QGridLayout
from PyQt5.QtCore import QSize
from PyQt5.QtSvg import QSvgWidget

from helper.functions import createQByteArray
from helper.classes import EvenLayout


class BoardView(QWidget):

    def __init__(self, board, **kwargs):
        super().__init__(**kwargs)
        self.svgWidget = QSvgWidget()
        layout = EvenLayout(self)
        layout.addWidget(self.svgWidget, 0, 0)

        self.press_pos = None
        self.board = board
        self.refresh()

    def refresh(self):
        svg_board = boardToSvg(self.board)
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
                self.parent().do_move(move)

    def mouseMoveEvent(self, event):
        # TODO: Implement drag icon
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


class Main(QWidget):

    EXIT = set(['exit', 'quit', 'qq'])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.board = Board()
        self.sfish = Stockfish(os.getcwd() + '/stockfish-10-linux/Linux/stockfish_10_x64')
        self.sfish.set_fen_position(self.board.fen())

        self.board_view = BoardView(self.board, parent=self)
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
            print([str(move) for move in self.board.legal_moves])
        elif cmd == 'sb':
            with open('board.svg', 'w') as file:
                file.write(str(boardToSvg(self.board)))
            print('Board written to svg file.')
        elif cmd == 'rr':
            try:
                move = str(random.choice(list(self.board.legal_moves)))
                print('Playing random move:', move)
                self.do_move(move)
            except IndexError as ie:
                self.check_status()
        elif cmd == 'sf':
            move = self.sfish.get_best_move()
            if move:
                print('Playing stockfish move:', move)
                self.do_move(move)
            else:
                self.check_status()
        else:
            try:
                self.do_move(cmd)
            except ValueError as ve:
                print('Command not recognized.', ve)

    def do_move(self, uci):
        move = Move.from_uci(uci)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.board_view.refresh()
            self.sfish.set_fen_position(self.board.fen())
            self.check_status()
        else:
            print('Illegal move!')

    def check_status(self):
        if self.board.is_checkmate():
            print('Checkmate player {}!'.format('White' if self.board.turn else 'Black'))
        elif self.board.is_game_over():
            print('Game over!', self.board.result())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.setGeometry(150, 150, 800, 800)
    window.show()
    sys.exit(app.exec_())
