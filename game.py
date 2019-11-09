import os
import random
import queue
import logging

from threading import Thread
from time import sleep, clock

import numpy as np

from chess import Board, Move
from chess.svg import board as boardToSvg

from stockfish_api import StockfishAPI
from helper.functions import toggle


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        self.stockfish = StockfishAPI(path=f'{os.getcwd()}/stockfish-10-linux/stockfish_10_x64_modern', depth=5)

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
            ai  = self.play_against_ai,
            si  = lambda: logger.info(self.stockfish.info)
        )

    def execute(self, cmd):
        try:
            self.command_queue.put(cmd, block=False)
        except Exception as e:
            logger.exception(e)

    def set_board_view(self, board_view):
        self.board_view = board_view

    def run(self):
        while not self.stop_flag:
            cmd = self.command_queue.get(block=True)
            if cmd is None: break
            cmd, *args = cmd.split(' ')

            try:
                self.commands[cmd](*args) # Command call
            except KeyError:
                try:
                    self.do_move(cmd)
                except ValueError:
                    logger.warning('Command not recognized:', cmd)
            except TypeError as te:
                logger.warning(te)
            except Exception as e:
                logger.exception(e)
            finally:
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
            logger.info('Checkmate player {}!'.format('White' if self.board.turn else 'Black'))
        elif self.board.is_game_over():
            logger.info('Game over!', self.board.result())

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
            logger.info('Illegal move!')

    def reverse_move(self):
        logger.info(f'Popping {self.board.pop()} move off stack.')
        self._refresh_view()

    def reset_board(self, refresh=True):
        logger.info('Resetting board.')
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
        logger.info('Playing fast forward mode.')
        self.auto_play = True
        move = toggle(
            lambda r: self.play_stockfish_move(r), 
            lambda r: self.play_random_move(r)
        )
        i = 0
        
        while not (self.board.is_game_over() or self.halt_flag):
            next(move)(refresh)
            i += 1
        
        self.auto_play = False
        return i

    def auto_play_stockfish(self, refresh=True):
        logger.info('Playing stockfish vs stockfish.')
        self.auto_play = True
        i = 0
        
        while not (self.board.is_game_over() or self.halt_flag):
            self.play_stockfish_move(refresh)
            i += 1
        
        self.auto_play = False
        return i

    def auto_play_random(self, refresh=True):
        logger.info('Playing random moves.')
        self.auto_play = True
        i = 0
        
        while not (self.board.is_game_over() or self.halt_flag):
            self.play_random_move(refresh)
            i += 1

        self.auto_play = False
        return i

    # One move look-a-head, best-move checkmate check
    def auto_play_random_lookahead(self, refresh=True):
        logger.info('Playing random with look-a-head.')
        self.auto_play = True
        i = 0

        while not (self.board.is_game_over() or self.halt_flag):
            move = self.stockfish.get_best_move(self.board.fen(), depth=1)
            self.do_move(move, False)
            if self.board.is_game_over() or self.halt_flag: continue

            self.board.pop()
            self.play_random_move(refresh)
            i += 1

        self.auto_play = False
        return i

    def test(self):
        logger.info('Running benchmarks.')
        durations = [[] for _ in range(4)]
        iterations = [[] for _ in range(4)]
        N = 100

        self.reset_board(True)
        logger.setLevel(logging.WARNING)
        functions = [self.auto_play_stockfish, self.auto_play_random, self.auto_fast_forward, self.auto_play_random_lookahead]
        for f in range(len(functions)):
            for _ in range(N):
                self.reset_board(False)
                t0 = clock()
                i = functions[f](False)
                dt = clock() - t0
                durations[f].append(dt)
                iterations[f].append(i)

        self.reset_board(False)
        logger.setLevel(logging.INFO)
        try:
            logger.info(''.join(['stockfish        - avg elapsed time: ', str(round((sum(durations[0])*10)/N, 2)), ' avg iterations: ', str(sum(iterations[0])/N)]))
            logger.info(''.join(['random           - avg elapsed time: ', str(round((sum(durations[1])*10)/N, 2)), ' avg iterations: ', str(sum(iterations[1])/N)]))
            logger.info(''.join(['forward          - avg elapsed time: ', str(round((sum(durations[2])*10)/N, 2)), ' avg iterations: ', str(sum(iterations[2])/N)]))
            logger.info(''.join(['random_lookahead - avg elapsed time: ', str(round((sum(durations[3])*10)/N, 2)), ' avg iterations: ', str(sum(iterations[3])/N)]))
        except:
            pass

    def play_against_ai(self, a, b=1):
        print(a, b)

