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

        self.commands = dict(
            # Exit application.
            qq = self.quit,
            # Save current board state to svg.
            sb = self.save_board,
            # Halt auto play.
            q  = self.game.halt,
            # Toggle edit mode.
            ee = self.game.toggle_edit_mode,
            # Check result.
            cc = (lambda: logger.info(self.game.board.result())),
            # Print legal moves.
            lm = (lambda: logger.info(', '.join([str(move) for move in self.game.board.legal_moves]))),
            # Print available commands.
            hh = (lambda: logger.info('Commands: ' + ', '.join(list(self.commands.keys()) + list(self.game.commands.keys()))))
        )

    def execute_command(self):
        cmd, *args = self.command.text().split(' ')
        self.command.clear()

        try:
            self.commands[cmd](*args)
        except KeyError:
            if self.game.auto_play:
                logger.info('Auto-play in progress. Send q to halt.')
            else:
                self.execute_game_command(cmd)
        except Exception as e:
            logger.exception(e)
            logger.error('cmd: {cmd}, args: {args}')
    
    def execute_game_command(self, cmd):
        self.game.execute(cmd)

    def closeEvent(self, event):
        super().closeEvent(event)
        self.game.stop()

    def quit(self):
        self.game.stop()
        sys.exit(0)

    def save_board(self, filename='board.svg'):
        filename = next(uniquename(filename))
        with open(filename, 'w') as file:
            file.write(str(self.game.get_svg_board()))
        logger.info('Board written to: ' + filename)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Main()
    window.setGeometry(150, 150, 800, 800)
    window.show()
    sys.exit(app.exec_())
