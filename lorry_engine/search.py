"""Search and evaluation for the LORRY chess engine."""
from __future__ import annotations

import math
import time
from dataclasses import dataclass

from .board import BLACK, PIECE_VALUES, WHITE, Board, Move, color_of

MATE = 100_000


@dataclass
class SearchResult:
    move: Move | None
    score: int
    depth: int
    nodes: int


class Engine:
    def __init__(self) -> None:
        self.nodes = 0
        self.deadline = math.inf

    def best_move(self, board: Board, depth: int = 3, movetime_ms: int | None = None) -> SearchResult:
        self.deadline = time.monotonic() + (movetime_ms / 1000) if movetime_ms else math.inf
        best = SearchResult(None, -MATE, 0, 0)
        for current_depth in range(1, depth + 1):
            self.nodes = 0
            score, move = self._root(board, current_depth)
            if time.monotonic() > self.deadline:
                break
            best = SearchResult(move, score, current_depth, self.nodes)
        return best

    def _root(self, board: Board, depth: int) -> tuple[int, Move | None]:
        alpha = -MATE
        beta = MATE
        best_move = None
        moves = self._ordered_moves(board)
        if not moves:
            return (-MATE if board.in_check(board.turn) else 0), None
        for move in moves:
            state = board.make_move(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, 1)
            board.unmake_move(move, state)
            if score > alpha:
                alpha = score
                best_move = move
        return alpha, best_move

    def _negamax(self, board: Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        if time.monotonic() > self.deadline:
            return self.evaluate(board)
        self.nodes += 1
        if depth <= 0:
            return self._quiescence(board, alpha, beta)
        moves = self._ordered_moves(board)
        if not moves:
            return -MATE + ply if board.in_check(board.turn) else 0
        value = -MATE
        for move in moves:
            state = board.make_move(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.unmake_move(move, state)
            value = max(value, score)
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        return value

    def _quiescence(self, board: Board, alpha: int, beta: int) -> int:
        stand_pat = self.evaluate(board)
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)
        for move in self._ordered_moves(board):
            if not board.piece_at(move.to_sq):
                continue
            state = board.make_move(move)
            score = -self._quiescence(board, -beta, -alpha)
            board.unmake_move(move, state)
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha

    def evaluate(self, board: Board) -> int:
        score = 0
        for square, piece in enumerate(board.squares):
            if not piece:
                continue
            value = PIECE_VALUES[piece.upper()]
            score += value if color_of(piece) == WHITE else -value
        return score if board.turn == WHITE else -score

    def _ordered_moves(self, board: Board) -> list[Move]:
        def move_score(move: Move) -> int:
            victim = board.piece_at(move.to_sq)
            attacker = board.piece_at(move.from_sq)
            capture = 10 * PIECE_VALUES.get(victim.upper(), 0) - PIECE_VALUES.get(attacker.upper(), 0) if victim else 0
            promotion = PIECE_VALUES.get(move.promotion, 0)
            return capture + promotion
        return sorted(board.legal_moves(), key=move_score, reverse=True)
