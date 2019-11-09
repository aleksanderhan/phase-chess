import os
import random
import queue

from threading import Thread
from time import sleep, clock

import numpy as np

from chess import Board, Move
from chess.svg import board as boardToSvg

from stockfish_api import StockfishAPI
from helper.functions import toggle


class GameEngine(Thread):

    def __init__(self):
        super().__init__()
        self.stop_flag = False
        self.halt_flag = False
        self.auto_play = False
        self.edit_mode = False
        self.command_queue = queue.Queue(maxsize=1)

        self.board = Board()
        self.board_view = None
        self.stockfish = StockfishAPI(path='{}/stockfish-10-linux/stockfish_10_x64_modern'.format(os.getcwd()), depth=5)

        # Command map
        self.commands = dict(
            sf  = self.play_stockfish_move,
            rr  = self.play_random_move,
            ff  = self.auto_fast_forward,
            psf = self.auto_play_stockfish,
            pr  = self.auto_play_random,
            re  = self.reset_board,
            rev = self.reverse_move,
            tt  = self.test,
        )

    def execute(self, cmd):
        try:
            self.command_queue.put(cmd, block=False)
        except Exception as e:
            print(e)

    def set_board_view(self, board_view):
        self.board_view = board_view

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
                    print('Command not recognized:', cmd)
            self.command_queue.task_done()
            self.halt_flag = False

    def stop(self):
        self.halt_flag = True
        self.stop_flag = True
        self.command_queue.put(None)

    def _refresh_view(self):
        if self.board_view:
            self.board_view.refresh(self.get_svg_board())
            sleep(0.1)

    def check_status(self):
        if self.board.is_checkmate():
            print('Checkmate player {}!'.format('White' if self.board.turn else 'Black'))
        elif self.board.is_game_over():
            print('Game over!', self.board.result())

    def get_svg_board(self):
        return boardToSvg(self.board)

    def do_move(self, uci, refresh=True):
        move = Move.from_uci(uci)
        if move in self.board.legal_moves or self.edit_mode:
            if self.edit_mode: 
                x0 = 'abcdefgh'.index(uci[0])
                y0 = int(uci[1]) - 1
                piece = str(self.board.piece_at(x0 + y0*8))
                if ((piece.isupper() and not self.board.turn) or
                    (piece.islower() and self.board.turn)):
                    self.board.turn = not self.board.turn
                    self.board.push(move)
                    self.board.turn = not self.board.turn
            else:
                self.board.push(move)

            if refresh: self._refresh_view()
            self.check_status()
        else:
            print('Illegal move!')

    def reverse_move(self):
        print('Popping {} move off stack'.format(self.board.pop()))
        self._refresh_view()

    def reset_board(self, refresh=True):
        print('Resetting board.')
        self.board.reset()
        if refresh: self._refresh_view()

    def play_stockfish_move(self, refresh=True):
        move = self.stockfish.get_best_move(self.board.fen())
        if move:
            self.do_move(move, refresh)
        else:
            self.check_status()

    def play_random_move(self, refresh=True):
        try:
            move = str(random.choice(list(self.board.legal_moves)))
            self.do_move(move, refresh)
        except IndexError as ie:
            self.check_status()

    def play_worst_move(self, refresh=True):
        # Can stockfish do it?
        pass

    def auto_fast_forward(self, refresh=True):
        print('Playing fast forward mode.')
        self.auto_play = True
        move = toggle(
            lambda r: self.play_stockfish_move(r), 
            lambda r: self.play_random_move(r)
        )
        i = 0
        
        while not (self.board.is_game_over() or self.halt_flag):
            next(move)(refresh)
            i += 1
        
        self._refresh_view()
        self.auto_play = False
        return i

    def auto_play_stockfish(self, refresh=True):
        print('Playing stockfish vs stockfish.')
        self.auto_play = True
        i = 0
        
        while not (self.board.is_game_over() or self.halt_flag):
            self.play_stockfish_move(refresh)
            i += 1
        
        self._refresh_view()
        self.auto_play = False
        return i

    def auto_play_random(self, refresh=True):
        print('Playing random moves.')
        self.auto_play = True
        i = 0
        
        while not (self.board.is_game_over() or self.halt_flag):
            self.play_random_move(refresh)
            i += 1

        self._refresh_view()
        self.auto_play = False
        return i

    # One move look-a-head, best-move checkmate check
    def auto_play_random_lookahead(self, refresh=True):
        print('Playing random with look-a-head.')
        self.auto_play = True
        i = 0

        while not (self.board.is_game_over() or self.halt_flag):
            move = self.stockfish.get_best_move(self.board.fen(), depth=1)
            self.do_move(move, False)
            if self.board.is_game_over() or self.halt_flag: continue

            self.board.pop()
            self.play_random_move(refresh)
            i += 1

        self._refresh_view()
        self.auto_play = False
        return i


    def test(self):
        self.reset_board(True)
        t0 = clock()
        i = self.auto_play_stockfish(False)
        dt = clock() - t0
        print('elapsed time: ', round(dt*10, 2), 'iterations:', i)
        print()    
        
        self.reset_board(False)
        t0 = clock()
        i = self.auto_play_random(False)
        dt = clock() - t0
        print('elapsed time: ', round(dt*10, 2), 'iterations:', i)
        print()    

        self.reset_board(False)
        t0 = clock()
        i = self.auto_fast_forward(False)
        dt = clock() - t0
        print('elapsed time: ', round(dt*10, 2), 'iterations:', i)
        print()    
        
        self.reset_board(False)
        t0 = clock()
        i = self.auto_play_random_lookahead(False)
        dt = clock() - t0
        print('elapsed time: ', round(dt*10, 2), 'iterations:', i)
        print()    

