import os
import random
import queue

from threading import Thread
from time import sleep

from chess import Board, Move
from chess.svg import board as boardToSvg
from stockfish import Stockfish

from helper.functions import toggle


class GameEngine(Thread):

    def __init__(self):
        super().__init__()
        self.stop_flag = False
        self.halt_flag = False
        self.auto_play = False
        self.command_queue = queue.Queue(maxsize=1)

        self.board = Board()
        self.board_view = None
        self.stockfish = Stockfish(path='{}/stockfish.bin'.format(os.getcwd()), depth=9)
        self.stockfish.set_fen_position(self.board.fen())

        # Command map
        self.commands = dict(
            sf  = self.play_best_move,
            rr  = self.play_random_move,
            ff  = self.auto_fast_forward,
            psf = self.auto_play_stockfish,
            pr  = self.auto_play_random,
            re  = self.reset_board,
            rev = self.reverse_move,
            pm  = (lambda pos=None: self.get_piece_at_position(pos)),
        )

    def run(self):
        while not self.stop_flag:
            cmd = self.command_queue.get(block=True)
            if cmd is None: break

            try:
                self.commands[cmd]() # Command call
            except KeyError:
                try:
                    self.do_move(cmd)
                except ValueError:
                    print('Command not recognized.' )
            self.command_queue.task_done()
            self.halt_flag = False

    def stop(self):
        self.halt_flag = True
        self.stop_flag = True
        self.command_queue.put(None)

    def execute(self, cmd):
        try:
            self.command_queue.put(cmd, block=False)
        except Exception as e:
            print(e)

    def auto_fast_forward(self):
        print('Playing fast forward mode.')
        self.auto_play = True
        move = toggle(self.play_best_move, self.play_random_move)
        while not (self.board.is_game_over() or self.halt_flag):
            next(move)()
            sleep(0.5)
        self.auto_play = False

    def auto_play_stockfish(self):
        print('Playing stockfish vs stockfish.')
        self.auto_play = True
        while (self.board.is_game_over() or self.halt_flag):
            self.play_best_move
            sleep(1)
        self.auto_play = False

    def auto_play_random(self):
        print('Playing random moves.')
        self.auto_play = True
        while not (self.board.is_game_over() or self.halt_flag):
            self.play_random_move
            sleep(1)
        self.auto_play = False

    def play_best_move(self):
        move = self.get_best_move()
        if move:
            print('Playing stockfish move:', move)
            self.do_move(move)
        else:
            self.check_status()

    def play_random_move(self):
        try:
            move = str(random.choice(list(self.board.legal_moves)))
            print('Playing random move:', move)
            self.do_move(move)
        except IndexError as ie:
            self.check_status()

    def play_worst_move(self):
        # Can stockfish do it?
        pass

    def get_best_move(self):
        self.stockfish.set_fen_position(self.board.fen())
        return self.stockfish.get_best_move()

    def reset_board(self):
        print('Resetting board.')
        self.board.reset()
        self.refresh_view()

    def do_move(self, uci):
        move = Move.from_uci(uci)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.refresh_view()
            self.check_status()
        else:
            print('Illegal move!')

    def reverse_move(self):
        print('Popping {} move off stack'.format(self.board.pop()))
        self.refresh_view()

    def refresh_view(self):
        if self.board_view:
            self.board_view.refresh(self.get_svg_board())
            sleep(0.1)

    def check_status(self):
        if self.board.is_checkmate():
            print('Checkmate player {}!'.format('White' if self.board.turn else 'Black'))
        elif self.board.is_game_over():
            print('Game over!', self.board.result())

    def set_board_view(self, board_view):
        self.board_view = board_view

    def get_svg_board(self):
        return boardToSvg(self.board)



        