import sys
import numpy as np

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QGridLayout

from view import BoardView
from game import GameEngine


class Main(QWidget):

    EXIT = set(['exit', 'quit', 'qq'])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game = GameEngine()
        self.board_view = BoardView(self.game.get_svg_board(), parent=self)
        self.game.set_board_view(self.board_view)
        self.game.start()
        self.command = QLineEdit()
        layout = QGridLayout(self)
        layout.addWidget(self.board_view)
        layout.addWidget(self.command)

        # Signaling
        self.command.returnPressed.connect(self.execute_command)

    def execute_command(self):
        cmd = self.command.text()
        self.command.clear()
        if cmd.lower() in self.EXIT: # exit
            self.game.stop()
            sys.exit(0)
        elif cmd == 'lm': # legal moves
            print([str(move) for move in self.game.board.legal_moves])
        elif cmd == 'sb': # save board
            with open('board.svg', 'w') as file:
                file.write(str(self.game.get_svg_board()))
            print('Board written to svg file.')
        else:
            self.execute_game_command(cmd)

    def execute_game_command(self, cmd):
        self.game.execute(cmd)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.setGeometry(150, 150, 800, 800)
    window.show()
    sys.exit(app.exec_())
