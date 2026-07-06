"""Minimal chess board, legal move generation, and FEN support."""
from __future__ import annotations

from dataclasses import dataclass

FILES = "abcdefgh"
RANKS = "12345678"
WHITE = "w"
BLACK = "b"
START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}

KNIGHT_DELTAS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING_DELTAS = ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1))
BISHOP_DELTAS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DELTAS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def idx(file: int, rank: int) -> int:
    return rank * 8 + file


def file_of(square: int) -> int:
    return square % 8


def rank_of(square: int) -> int:
    return square // 8


def in_bounds(file: int, rank: int) -> bool:
    return 0 <= file < 8 and 0 <= rank < 8


def square_name(square: int) -> str:
    return FILES[file_of(square)] + RANKS[rank_of(square)]


def parse_square(name: str) -> int:
    return idx(FILES.index(name[0]), RANKS.index(name[1]))


def color_of(piece: str) -> str:
    return WHITE if piece.isupper() else BLACK


def opponent(color: str) -> str:
    return BLACK if color == WHITE else WHITE


@dataclass(frozen=True)
class Move:
    from_sq: int
    to_sq: int
    promotion: str = ""

    def uci(self) -> str:
        return f"{square_name(self.from_sq)}{square_name(self.to_sq)}{self.promotion.lower()}"

    @classmethod
    def from_uci(cls, text: str) -> "Move":
        return cls(parse_square(text[:2]), parse_square(text[2:4]), text[4:].upper())


@dataclass(frozen=True)
class State:
    captured: str
    castling: str
    ep_square: int | None
    halfmove: int
    fullmove: int


class Board:
    def __init__(self, fen: str = START_FEN) -> None:
        self.squares = [""] * 64
        self.turn = WHITE
        self.castling = "KQkq"
        self.ep_square: int | None = None
        self.halfmove = 0
        self.fullmove = 1
        self.set_fen(fen)

    def set_fen(self, fen: str) -> None:
        placement, turn, castling, ep, halfmove, fullmove = fen.split()[:6]
        self.squares = [""] * 64
        for fen_rank, row in enumerate(placement.split("/")):
            rank = 7 - fen_rank
            file = 0
            for char in row:
                if char.isdigit():
                    file += int(char)
                else:
                    self.squares[idx(file, rank)] = char
                    file += 1
        self.turn = turn
        self.castling = "" if castling == "-" else castling
        self.ep_square = None if ep == "-" else parse_square(ep)
        self.halfmove = int(halfmove)
        self.fullmove = int(fullmove)

    def fen(self) -> str:
        rows = []
        for rank in range(7, -1, -1):
            empty = 0
            row = ""
            for file in range(8):
                piece = self.squares[idx(file, rank)]
                if piece:
                    if empty:
                        row += str(empty)
                        empty = 0
                    row += piece
                else:
                    empty += 1
            rows.append(row + (str(empty) if empty else ""))
        return " ".join([
            "/".join(rows), self.turn, self.castling or "-",
            "-" if self.ep_square is None else square_name(self.ep_square),
            str(self.halfmove), str(self.fullmove),
        ])

    def piece_at(self, square: int) -> str:
        return self.squares[square]

    def make_move(self, move: Move) -> State:
        piece = self.squares[move.from_sq]
        captured = self.squares[move.to_sq]
        state = State(captured, self.castling, self.ep_square, self.halfmove, self.fullmove)
        self.squares[move.to_sq] = move.promotion if move.promotion and self.turn == WHITE else move.promotion.lower() if move.promotion else piece
        self.squares[move.from_sq] = ""
        if piece.upper() == "P" and move.to_sq == self.ep_square and not captured:
            cap_sq = move.to_sq + (-8 if self.turn == WHITE else 8)
            captured = self.squares[cap_sq]
            self.squares[cap_sq] = ""
        if piece.upper() == "K" and abs(move.to_sq - move.from_sq) == 2:
            rook_from, rook_to = (move.to_sq + 1, move.to_sq - 1) if move.to_sq > move.from_sq else (move.to_sq - 2, move.to_sq + 1)
            self.squares[rook_to], self.squares[rook_from] = self.squares[rook_from], ""
        self._update_castling(piece, move)
        self.ep_square = None
        if piece.upper() == "P" and abs(move.to_sq - move.from_sq) == 16:
            self.ep_square = (move.from_sq + move.to_sq) // 2
        self.halfmove = 0 if piece.upper() == "P" or captured else self.halfmove + 1
        if self.turn == BLACK:
            self.fullmove += 1
        self.turn = opponent(self.turn)
        return state

    def unmake_move(self, move: Move, state: State) -> None:
        self.turn = opponent(self.turn)
        if self.turn == BLACK:
            self.fullmove -= 1
        piece = self.squares[move.to_sq]
        original = "P" if move.promotion and self.turn == WHITE else "p" if move.promotion else piece
        self.squares[move.from_sq] = original
        self.squares[move.to_sq] = state.captured
        if original.upper() == "P" and move.to_sq == state.ep_square and not state.captured:
            cap_sq = move.to_sq + (-8 if self.turn == WHITE else 8)
            self.squares[cap_sq] = "p" if self.turn == WHITE else "P"
        if original.upper() == "K" and abs(move.to_sq - move.from_sq) == 2:
            rook_from, rook_to = (move.to_sq + 1, move.to_sq - 1) if move.to_sq > move.from_sq else (move.to_sq - 2, move.to_sq + 1)
            self.squares[rook_from], self.squares[rook_to] = self.squares[rook_to], ""
        self.castling, self.ep_square, self.halfmove, self.fullmove = state.castling, state.ep_square, state.halfmove, state.fullmove

    def legal_moves(self) -> list[Move]:
        legal = []
        for move in self.pseudo_legal_moves():
            state = self.make_move(move)
            if not self.in_check(opponent(self.turn)):
                legal.append(move)
            self.unmake_move(move, state)
        return legal

    def pseudo_legal_moves(self) -> list[Move]:
        moves = []
        for square, piece in enumerate(self.squares):
            if not piece or color_of(piece) != self.turn:
                continue
            kind = piece.upper()
            if kind == "P":
                self._pawn_moves(square, moves)
            elif kind == "N":
                self._jump_moves(square, KNIGHT_DELTAS, moves)
            elif kind == "B":
                self._slide_moves(square, BISHOP_DELTAS, moves)
            elif kind == "R":
                self._slide_moves(square, ROOK_DELTAS, moves)
            elif kind == "Q":
                self._slide_moves(square, BISHOP_DELTAS + ROOK_DELTAS, moves)
            elif kind == "K":
                self._jump_moves(square, KING_DELTAS, moves)
                self._castle_moves(square, moves)
        return moves

    def in_check(self, color: str) -> bool:
        king = "K" if color == WHITE else "k"
        king_sq = self.squares.index(king)
        return self.is_attacked(king_sq, opponent(color))

    def is_attacked(self, square: int, by_color: str) -> bool:
        sf, sr = file_of(square), rank_of(square)
        pawn_dir = -1 if by_color == WHITE else 1
        pawn = "P" if by_color == WHITE else "p"
        for df in (-1, 1):
            f, r = sf + df, sr + pawn_dir
            if in_bounds(f, r) and self.squares[idx(f, r)] == pawn:
                return True
        for df, dr in KNIGHT_DELTAS:
            f, r = sf + df, sr + dr
            if in_bounds(f, r) and self.squares[idx(f, r)] == ("N" if by_color == WHITE else "n"):
                return True
        for deltas, attackers in ((BISHOP_DELTAS, "BQ"), (ROOK_DELTAS, "RQ")):
            for df, dr in deltas:
                f, r = sf + df, sr + dr
                while in_bounds(f, r):
                    piece = self.squares[idx(f, r)]
                    if piece:
                        if color_of(piece) == by_color and piece.upper() in attackers:
                            return True
                        break
                    f += df; r += dr
        for df, dr in KING_DELTAS:
            f, r = sf + df, sr + dr
            if in_bounds(f, r) and self.squares[idx(f, r)] == ("K" if by_color == WHITE else "k"):
                return True
        return False

    def _pawn_moves(self, square: int, moves: list[Move]) -> None:
        piece = self.squares[square]
        direction = 1 if piece.isupper() else -1
        start_rank = 1 if piece.isupper() else 6
        promote_rank = 7 if piece.isupper() else 0
        f, r = file_of(square), rank_of(square)
        one = idx(f, r + direction) if in_bounds(f, r + direction) else None
        if one is not None and not self.squares[one]:
            self._add_pawn_move(square, one, promote_rank, moves)
            two_rank = r + 2 * direction
            if r == start_rank and not self.squares[idx(f, two_rank)]:
                moves.append(Move(square, idx(f, two_rank)))
        for df in (-1, 1):
            tf, tr = f + df, r + direction
            if not in_bounds(tf, tr):
                continue
            target = idx(tf, tr)
            if (self.squares[target] and color_of(self.squares[target]) != self.turn) or target == self.ep_square:
                self._add_pawn_move(square, target, promote_rank, moves)

    def _add_pawn_move(self, from_sq: int, to_sq: int, promote_rank: int, moves: list[Move]) -> None:
        if rank_of(to_sq) == promote_rank:
            moves.extend(Move(from_sq, to_sq, p) for p in "QRBN")
        else:
            moves.append(Move(from_sq, to_sq))

    def _jump_moves(self, square: int, deltas: tuple[tuple[int, int], ...], moves: list[Move]) -> None:
        f, r = file_of(square), rank_of(square)
        for df, dr in deltas:
            tf, tr = f + df, r + dr
            if in_bounds(tf, tr):
                target = self.squares[idx(tf, tr)]
                if not target or color_of(target) != self.turn:
                    moves.append(Move(square, idx(tf, tr)))

    def _slide_moves(self, square: int, deltas: tuple[tuple[int, int], ...], moves: list[Move]) -> None:
        f, r = file_of(square), rank_of(square)
        for df, dr in deltas:
            tf, tr = f + df, r + dr
            while in_bounds(tf, tr):
                target_sq = idx(tf, tr)
                target = self.squares[target_sq]
                if not target:
                    moves.append(Move(square, target_sq))
                else:
                    if color_of(target) != self.turn:
                        moves.append(Move(square, target_sq))
                    break
                tf += df; tr += dr

    def _castle_moves(self, square: int, moves: list[Move]) -> None:
        if self.in_check(self.turn):
            return
        rights = (("K", 5, 6), ("Q", 3, 2), ("k", 61, 62), ("q", 59, 58))
        for right, through, dest in rights:
            if right not in self.castling or color_of(self.squares[square]) != (WHITE if right.isupper() else BLACK):
                continue
            empty = {"K": [5, 6], "Q": [1, 2, 3], "k": [61, 62], "q": [57, 58, 59]}[right]
            if all(not self.squares[s] for s in empty) and not self.is_attacked(through, opponent(self.turn)) and not self.is_attacked(dest, opponent(self.turn)):
                moves.append(Move(square, dest))

    def _update_castling(self, piece: str, move: Move) -> None:
        if piece == "K": self.castling = self.castling.replace("K", "").replace("Q", "")
        if piece == "k": self.castling = self.castling.replace("k", "").replace("q", "")
        for sq, right in ((0, "Q"), (7, "K"), (56, "q"), (63, "k")):
            if move.from_sq == sq or move.to_sq == sq:
                self.castling = self.castling.replace(right, "")
