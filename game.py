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
            sf  = self._play_stockfish_move,
            rr  = self._play_random_move,
            ff  = self._auto_play_fast_forward,
            psf = self._auto_play_stockfish,
            pr  = self._auto_play_random,
            re  = self._reset_board,
            rev = self._reverse_move,
            tt  = self._test,
            ai  = self._play_against_ai,
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
                    self._do_move(cmd)
                except ValueError:
                    logger.warning('Command not recognized:' + cmd)
            except TypeError as te:
                logger.warning('Too many arguments. ' + str(te))
            except Exception as e:
                logger.exception(e)
            finally:
                self.command_queue.task_done()
                self.halt_flag = False

    def stop(self):
        self.halt_flag = True
        self.stop_flag = True
        self.command_queue.put(None)

    def check_status(self):
        if self.board.is_checkmate():
            logger.info('Checkmate player {}!'.format('White' if self.board.turn else 'Black'))
        elif self.board.is_game_over():
            logger.info(f'Game over! {self.board.result()}')

    def get_svg_board(self):
        return boardToSvg(self.board)

    def get_piece_at_pos(self, uci):
        x = 'abcdefgh'.index(uci[0])
        y = int(uci[1]) - 1
        return str(self.board.piece_at(x + y*8))

    def __refresh_view(self):
        if self.board_view:
            self.board_view.refresh(self.get_svg_board())
            sleep(0.1)

    def _do_move(self, uci, refresh=True):
        move = Move.from_uci(uci)
        if move in self.board.legal_moves or self.edit_mode:
            if self.edit_mode: 
                piece = self.get_piece_at_pos(uci)
                if ((piece.isupper() and not self.board.turn) or
                    (piece.islower() and self.board.turn)):
                    self.board.turn = not self.board.turn
                    self.board.push(move)
                    self.board.turn = not self.board.turn
            else:
                self.board.push(move)

            if refresh: self.__refresh_view()
            self.check_status()
        else:
            logger.info('Illegal move!')

    def _reverse_move(self):
        logger.info(f'Popping {self.board.pop()} move off stack.')
        self.__refresh_view()

    def _reset_board(self, refresh=True):
        logger.info('Resetting board.')
        self.board.reset()
        if refresh: self.__refresh_view()

    def _play_stockfish_move(self, refresh=True):
        move = self.stockfish.get_best_move(self.board.fen())
        if move:
            self._do_move(move, refresh)
        else:
            self.check_status()

    def _play_random_move(self, refresh=True):
        try:
            move = str(random.choice(list(self.board.legal_moves)))
            self._do_move(move, refresh)
        except IndexError as ie:
            self.check_status()

    # One move look-a-head, best-move checkmate check
    def _play_random_lookahead(self, refresh=True):
        move = self.stockfish.get_best_move(self.board.fen(), depth=1)
        self._do_move(move, False)
        if self.board.is_game_over(): return

        self.board.pop()
        self.play_random_move(refresh)

    def _play_worst_move(self, refresh=True):
        # Can stockfish do it?
        pass

    def _auto_play(self, function, refresh=True):
        self.auto_play = True
        i = 0
        
        while not (self.board.is_game_over() or self.halt_flag):
            function(refresh)
            i += 1
        
        self.auto_play = False
        return i

    def _auto_play_fast_forward(self, refresh=True):
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

    def _auto_play_stockfish(self, refresh=True):
        logger.info('Playing stockfish vs stockfish.')
        return self.auto_play(self.play_stockfish_move(refresh))
        
    def _auto_play_random(self, refresh=True):
        logger.info('Playing random moves.')
        return self.auto_play(self.play_random_move(refresh))

    def _auto_play_random_lookahead(self, refresh=True):
        logger.info('Playing random with look-a-head.')
        return self.auto_play(self.play_random_lookahead(refresh))

    def _test(self):
        logger.info('Running benchmarks.')
        durations = [[] for _ in range(4)]
        iterations = [[] for _ in range(4)]
        N = 100

        self.reset_board(True)
        logger.setLevel(logging.WARNING)
        functions = [self.auto_play_stockfish, self.auto_play_random, self.auto_play_fast_forward, self.auto_play_random_lookahead]
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

    def _play_against_ai(self, ai='sf', d=1):
        if ai == 'sf':
            engine = self.stockfish.get_best_move(self.board.fen(), d)
        else:
            raise Exception(f'ai argument {ai} not known.')



