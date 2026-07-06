from lorry_engine.board import Board, Move, START_FEN
from lorry_engine.search import Engine


def test_start_position_has_twenty_legal_moves():
    board = Board(START_FEN)
    assert len(board.legal_moves()) == 20


def test_make_and_unmake_restores_fen():
    board = Board(START_FEN)
    original = board.fen()
    move = Move.from_uci("e2e4")
    legal = {candidate.uci(): candidate for candidate in board.legal_moves()}
    state = board.make_move(legal[move.uci()])
    board.unmake_move(legal[move.uci()], state)
    assert board.fen() == original


def test_engine_finds_a_legal_move():
    board = Board(START_FEN)
    result = Engine().best_move(board, depth=2)
    assert result.move in board.legal_moves()
