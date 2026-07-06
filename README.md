# LORRY Chess Engine

A compact Python chess engine scaffold with legal move generation, alpha-beta search, quiescence, iterative deepening, and a simple UCI-compatible command loop.

This project is intentionally small and maintainable; it is **not** a 30,000,000-line engine and does not claim to rival Stockfish. It provides a practical foundation for experimentation.

## Quick start

```bash
python -m lorry_engine.uci
```

Example UCI session:

```text
uci
isready
position startpos moves e2e4 e7e5
go depth 3
quit
```

## Tests

```bash
python -m pytest
```
