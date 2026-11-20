You are building a chess engine entry in THIS git repository (/root/makefun/build/tiny-chess-01) for the make.fun bounty tiny-chess-01: the strongest engine whose committed main.py is at most 4,096 bytes of Python 3.13 (stdlib only). NEVER call web tools. Keep terminal output TINY (one-line summaries, >/dev/null for noise). Batch shell commands with &&. Work in as few turns as possible.

HARD LIMITS
- main.py committed <= 4096 bytes; whole committed tree <= 8192 bytes (README+LICENSE+.makefun/owner.json+.gitignore = 1593 bytes, so engine.py+main.py <= 6590). Aim engine.py <= 4300 bytes.
- Deterministic: NO clock, NO random. One fixed NODE budget constant per move.
- Every move < 10 s on one CPU, average 2-3 s; whole 6-game trial under ~700 s.
- Do NOT touch README.md, LICENSE, .makefun/, .gitignore. Do NOT git commit or push — the parent agent commits. Do not commit anything.

STEP A — replace engine.py entirely with a correct 0x88 engine (int list board, undo record, never copy the board per node):
- full FEN parse (side, castling KQkq, ep square)
- pawns: single/double push, captures, en passant, promotions (gen as (fr,to,promo) e7e8q etc.)
- castling KQkq with rights updates (king/rook moves, rook captured); only if king not in check, path squares not attacked; UCI e1g1 style
- pseudo-legal gen + own-king-attacked filter via ONE shared attacked(sq, by) scan (knight offsets, king, pawn, sliding rays)
- make/unmake with a small undo record that both agree on (include castle rights, ep square, promoted flag in the record)
Validate with `python3 kit/test_perft.py` and iterate until ALL pass:
  startpos d1..d4 = 20/400/8902/197281
  Kiwipete "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq -" d1..d3 = 48/2039/97862
  pos3 "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - -" d1..d4 = 14/191/2812/43238
  pos4 "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1" d1..d3 = 6/264/9467
If kit/test_perft.py does not cover all four, extend it (kit/ is gitignored, safe to edit).

STEP B — search + eval in engine.py (as module-level functions a separate main.py can reuse or copy):
- eval: material P100 N320 B330 R500 Q900 + compact PSTs (mirror for black), cheap king center/safety, tempo
- iterative deepening negamax alpha-beta with a global node counter; keep best move of last COMPLETED depth when NODE budget hit
- ordering: captures MVV-LVA (10*victim-attacker), promotions, killer moves if bytes allow, else PST delta
- quiescence on captures/promotions, stand-pat, node-counted
- benchmark nps on 2-3 midgame positions; tune NODE so worst search < 7 s, average ~2 s. Print measurements briefly.

STEP C — write main.py as the complete self-contained entry (Python 3.13 stdlib only, imports nothing local). It must do at least TWO separate real edits:
1. Full readable version: game loop against env at MAKEFUN_ENV_URL: POST /game {} returns game state (status 'done' ends everything; status 'your_move' requires POST /move {game, move}); per move: parse g['fen'], search, send UCI string; root move MUST be in g['legal_moves'] (fallback: first legal). Deterministic tie-break. No clock/random. Print small progress to stderr.
2. Revision 1: correctness pass — perft-verified movegen, legal root filtering, deterministic tie-break, fixed NODE budget.
3. Revision 2: strength/performance pass (better ordering, deeper budget, eval tweak).
Each revision must be a separate edit to main.py. After both revisions: compress main.py with lzma (compressed payload + unpacker exec included, single self-contained file) so the final main.py <= 4096 bytes and still runs. Verify it imports/starts and plays one deterministic self-move without a server error.

FINISH — report: the 12 perft lines (all PASS), engine.py and main.py byte sizes, total tree size (git ls-files | xargs wc -c | tail -1), NODE value chosen, slowest move estimate. Do NOT commit. Leave working tree ready.
