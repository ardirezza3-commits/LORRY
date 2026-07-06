"""Tiny UCI protocol front-end."""
from __future__ import annotations

import sys

from .board import START_FEN, Board, Move
from .search import Engine


def apply_position(board: Board, tokens: list[str]) -> Board:
    if not tokens:
        return board
    if tokens[0] == "startpos":
        board = Board(START_FEN)
        tokens = tokens[1:]
    elif tokens[0] == "fen":
        move_index = tokens.index("moves") if "moves" in tokens else len(tokens)
        board = Board(" ".join(tokens[1:move_index]))
        tokens = tokens[move_index:]
    if tokens and tokens[0] == "moves":
        for move_text in tokens[1:]:
            move = Move.from_uci(move_text)
            legal = {candidate.uci(): candidate for candidate in board.legal_moves()}
            board.make_move(legal.get(move.uci(), move))
    return board


def main() -> None:
    board = Board()
    engine = Engine()
    for raw in sys.stdin:
        line = raw.strip()
        if line == "uci":
            print("id name LORRY Python")
            print("id author OpenAI")
            print("uciok")
        elif line == "isready":
            print("readyok")
        elif line.startswith("position"):
            board = apply_position(board, line.split()[1:])
        elif line.startswith("go"):
            tokens = line.split()
            depth = int(tokens[tokens.index("depth") + 1]) if "depth" in tokens else 3
            movetime = int(tokens[tokens.index("movetime") + 1]) if "movetime" in tokens else None
            result = engine.best_move(board, depth=depth, movetime_ms=movetime)
            print(f"info depth {result.depth} score cp {result.score} nodes {result.nodes}")
            print(f"bestmove {result.move.uci() if result.move else '0000'}")
        elif line == "ucinewgame":
            board = Board()
        elif line == "quit":
            break
        sys.stdout.flush()


if __name__ == "__main__":
    main()
