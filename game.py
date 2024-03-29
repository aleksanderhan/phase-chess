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
from helper.functions import toggle, parse_int


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
            si  = (lambda: logger.info(self.stockfish.info))
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
            except (TypeError, ValueError) as tve:
                logger.warning(f'Command arguments error. {tve}')
            except Exception as e:
                logger.exception(e)
            finally:
                self.command_queue.task_done()
                self.halt_flag = False

    def stop(self):
        self.halt_flag = True
        self.stop_flag = True
        self.command_queue.put(None)

    def halt(self):
        logger.debug('Halting auto-play.')
        self.halt_flag = True

    def toggle_edit_mode(self):
        logger.info(f'{"Disabling edit mode." if self.edit_mode else "Enabling edit mode."}')
        self.edit_mode = not self.edit_mode

    def check_status(self):
        if self.board.is_checkmate():
            logger.info(f'Checkmate player {"White" if self.board.turn else "Black"}!')
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

    def _play_stockfish_move(self, refresh=True, depth=None):
        move = self.stockfish.get_best_move(self.board.fen(), parse_int(depth))
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
        self._play_random_move(refresh)

    def _play_worst_move(self, refresh=True):
        # Can stockfish do it?
        pass

    def __auto_play(self, function, **kwargs):
        self.auto_play = True
        i = 0
        
        while not (self.board.is_game_over() or self.halt_flag):
            function(**kwargs)
            i += 1
        
        self.auto_play = False
        return i

    def _auto_play_fast_forward(self, refresh=True):
        logger.info('Playing fast forward mode.')
        move = toggle(
            (lambda r: self._play_stockfish_move(r)), 
            (lambda r: self._play_random_move(r))
        )
        return self.__auto_play((lambda t, r: next(t)(r)), t=move, r=refresh)

    def _auto_play_stockfish(self, refresh=True):
        logger.info('Playing stockfish vs stockfish.')
        return self.__auto_play(self._play_stockfish_move, refresh=refresh)
        
    def _auto_play_random(self, refresh=True):
        logger.info('Playing random moves.')
        return self.__auto_play(self._play_random_move, refresh=refresh)

    def _auto_play_random_lookahead(self, refresh=True):
        logger.info('Playing random with look-a-head.')
        return self.__auto_play(self._play_random_lookahead, refresh=refresh)

    def _test(self, N=100):
        N = parse_int(N)
        logger.info(f'Running benchmarks. N={N}')
        functions = [self._auto_play_stockfish, self._auto_play_random, self._auto_play_fast_forward, self._auto_play_random_lookahead]
        durations = [[] for _ in range(len(functions))]
        iterations = [[] for _ in range(len(functions))]

        self._reset_board(True)
        logger.setLevel(logging.WARNING)
        for f in range(len(functions)):
            for _ in range(N):
                self._reset_board(False)
                t0 = clock()
                i = functions[f](False)
                dt = clock() - t0
                durations[f].append(dt)
                iterations[f].append(i)

        self._reset_board(False)
        logger.setLevel(logging.INFO)
        try:
            logger.info(f'stockfish        - avg elapsed time: {round((sum(durations[0])*10)/N, 2)} avg iterations: {sum(iterations[0])/N}')
            logger.info(f'random           - avg elapsed time: {round((sum(durations[1])*10)/N, 2)} avg iterations: {sum(iterations[1])/N}')
            logger.info(f'fast forward     - avg elapsed time: {round((sum(durations[2])*10)/N, 2)} avg iterations: {sum(iterations[2])/N}')
            logger.info(f'random lookahead - avg elapsed time: {round((sum(durations[3])*10)/N, 2)} avg iterations: {sum(iterations[3])/N}')    
        except:
            pass

    def _play_against_ai(self, ai='sf', depth=None):
        if ai == 'sf':
            move = self.stockfish.get_best_move(self.board.fen(), depth)
        else:
            raise Exception(f'ai argument {ai} not known.')



