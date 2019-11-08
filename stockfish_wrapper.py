
from stockfish import Stockfish


class StockfishAPI(Stockfish):

	def __init__(self, *args, **kwargs):
		super().__init__(self, path: str = "stockfish", depth: int = 2, params: dict = None)