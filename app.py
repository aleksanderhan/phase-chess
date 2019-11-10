import sys
import logging
import numpy as np

from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QGridLayout

from view import BoardView
from game import GameEngine

from helper.functions import uniquename


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Main(QWidget):

    EXIT = {'exit', 'quit', 'qq'}

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
        elif cmd == 'q':
            logger.info('Halt automatic play.')
            self.game.halt_flag = True
        elif cmd == 'lm': # legal moves
            logger.info(', '.join([str(move) for move in self.game.board.legal_moves]))
        elif cmd == 'sb': # save board
            filename = next(uniquename('board.svg'))
            with open(filename, 'w') as file:
                file.write(str(self.game.get_svg_board()))
            logger.info('Board written to: ' +filename)
        elif cmd == 'cc':
            logger.info(self.game.board.result())
        elif cmd == 'ee':
            self.game.edit_mode = not self.game.edit_mode
        elif cmd == 'hh':
            logger.info('Commands: ' + ', '.join(self.game.commands.keys()))
        else:
            if not self.game.auto_play:
                self.execute_game_command(cmd)
            else:
                logger.info('Auto-play in progress. Send q to halt.')
    
    def execute_game_command(self, cmd):
        self.game.execute(cmd)

    def closeEvent(self, event):
        super().closeEvent(event)
        self.game.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.setGeometry(150, 150, 800, 800)
    window.show()
    sys.exit(app.exec_())
