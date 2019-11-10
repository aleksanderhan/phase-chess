
from stockfish import Stockfish


class StockfishAPI(Stockfish):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info = None

    def __put(self, command):
        self.stockfish.stdin.write(f'{command}\n')
        self.stockfish.stdin.flush()

    def get_best_move(self, fen, depth=None):
        if depth is None: depth = self.depth
        self.set_fen_position(fen)
        self.__put(f'go depth {depth}')
        # print(f'Getting best move at depth: {depth}')

        last_text: str = ''
        while True:
            text = self.stockfish.stdout.readline().strip()
            splitted_text = text.split(" ")
            # print(splitted_text)
            if splitted_text[0] == 'bestmove':
                if splitted_text[1] == '(none)':
                    return None
                self.info = last_text
                return splitted_text[1]
            last_text = text