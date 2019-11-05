import os
import random
import queue

from chess import Board, Move
from chess.svg import board as boardToSvg
from stockfish import Stockfish

from threading import Thread
from time import sleep

from helper.functions import toggle


class GameEngine(Thread, Game):

    def __init__(self):
        super().__init__()
        self.stop_flag = False
        self.halt_flag = False
        self.auto_play = False
        self.commands = queue.Queue()

        self.board = Board()
        self.board_view = None
        self.stockfish = Stockfish(path='{}/stockfish.bin'.format(os.getcwd()), depth=9)
        self.stockfish.set_fen_position(self.board.fen())

    def run(self):
        while not self.stop_flag:
            cmd = self.commands.get(block=True)
            if cmd is None: break
            self.switch(cmd)()
            self.commands.task_done() # 
            if self.halt_flag: self.toggle_halt_flag()

    def stop(self):
        if not self.halt_flag: self.toggle_halt_flag()
        self.stop_flag = True
        self.commands.put(None)

    def execute(self, cmd):
        self.commands.put(cmd)

    def switch(self, cmd):
        if not self.auto_play:
            if   cmd == 'sf':  return self.play_best_move
            elif cmd == 're':  return self.reset_board
            elif cmd == 'rr':  return self.play_random_move
            elif cmd == 'ff':  return self.fast_forward
            elif cmd == 'psf': return self.play_stockfish
            elif cmd == 'pr':  return self.play_random
            elif cmd == 'rev': return self.reverse_move
            else:              return (lambda cmd=cmd: self.do_move(cmd))
        else:
            print('Auto-play in progress. Send q to halt.')

    def fast_forward(self):
        print('Playing fast forward mode.')
        self.sequential_automatic_play(
            next(toggle(self.play_best_move, self.play_random_move)), 
            (lambda t=0.5: sleep(t))
        )

    def play_stockfish(self):
        print('Playing stockfish vs stockfish.')
        self.sequential_automatic_play(self.play_best_move, (lambda t=1: sleep(t)))

    def play_random(self):
        print('Playing random moves.')
        self.sequential_automatic_play(self.play_random_move, (lambda t=1: sleep(t)))

    def sequential_automatic_play(self, *functions):
        self.auto_play = True
        while not self.board.is_game_over() and not self.halt_flag and self.auto_play:
            for f in functions: f()
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
        try:
            move = Move.from_uci(uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.refresh_view()
                self.check_status()
            else:
                print('Illegal move!')
        except ValueError as ve:
            print('Command not recognized.', ve)

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

    def toggle_halt_flag(self):
        self.halt_flag = not self.halt_flag



class Game(object):
    """docstring for SimplePlay"""
    def __init__(self, arg):
        super().__init__()
        self.arg = arg
        