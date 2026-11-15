import sys
import json
import os
import urllib.request

# Constants
EMPTY = 0
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
WHITE, BLACK = 8, 16
PIECE_VALUES = {
    PAWN | WHITE: 100, KNIGHT | WHITE: 320, BISHOP | WHITE: 330, ROOK | WHITE: 500, QUEEN | WHITE: 900, KING | WHITE: 10000,
    PAWN | BLACK: -100, KNIGHT | BLACK: -320, BISHOP | BLACK: -330, ROOK | BLACK: -500, QUEEN | BLACK: -900, KING | BLACK: -10000,
}
OFFSETS = {
    KNIGHT: [-18, -33, -31, -14, 14, 31, 33, 18],
    BISHOP: [-17, -15, 15, 17],
    ROOK: [-16, -1, 1, 16],
    QUEEN: [-17, -16, -15, -1, 1, 15, 16, 17],
    KING: [-17, -16, -15, -1, 1, 15, 16, 17]
}

class Board:
    def __init__(self):
        self.squares = [0] * 128
        self.side = WHITE

    def parse_fen(self, fen):
        parts = fen.split()
        self.squares = [0] * 128
        rank, file = 7, 0
        for char in parts[0]:
            if char == '/': rank -= 1; file = 0
            elif char.isdigit(): file += int(char)
            else:
                color = WHITE if char.isupper() else BLACK
                piece = {'p':PAWN,'n':KNIGHT,'b':BISHOP,'r':ROOK,'q':QUEEN,'k':KING}[char.lower()]
                self.squares[rank * 16 + file] = piece | color
                file += 1
        self.side = WHITE if parts[1] == 'w' else BLACK

    def get_legal_moves(self):
        moves = []
        for sq in range(128):
            if not (sq & 0x88):
                p = self.squares[sq]
                if p and (p & self.side):
                    pt = p & 7
                    if pt == PAWN:
                        d = 16 if self.side == WHITE else -16
                        if not self.squares[sq+d]:
                            moves.append((sq, sq+d))
                            if (self.side == WHITE and 16 <= sq <= 23) or (self.side == BLACK and 96 <= sq <= 103):
                                if not self.squares[sq+2*d]: moves.append((sq, sq+2*d))
                    elif pt in OFFSETS:
                        for offset in OFFSETS[pt]:
                            to = sq + offset
                            while not (to & 0x88):
                                target = self.squares[to]
                                if not target: moves.append((sq, to))
                                elif (target & self.side): break
                                else: moves.append((sq, to)); break
                                if pt in [KNIGHT, KING]: break
                                to += offset
        return moves

    def make_move(self, move):
        fr, to = move
        self.squares[to] = self.squares[fr]
        self.squares[fr] = EMPTY
        self.side = BLACK if self.side == WHITE else WHITE

def evaluate(board):
    score = 0
    for sq in range(128):
        if not (sq & 0x88):
            piece = board.squares[sq]
            if piece: score += PIECE_VALUES.get(piece, 0)
    return score if board.side == WHITE else -score

def negamax(board, depth, alpha, beta):
    if depth == 0: return evaluate(board)
    max_eval = -1000000
    for move in board.get_legal_moves():
        orig_board = list(board.squares)
        orig_side = board.side
        board.make_move(move)
        eval = -negamax(board, depth - 1, -beta, -alpha)
        board.squares = orig_board
        board.side = orig_side
        if eval > max_eval: max_eval = eval
        alpha = max(alpha, eval)
        if alpha >= beta: break
    return max_eval

def uci_to_move(uci):
    fr = (ord(uci[0]) - ord('a')) + (int(uci[1]) - 1) * 16
    to = (ord(uci[2]) - ord('a')) + (int(uci[3]) - 1) * 16
    return (fr, to)

def move_to_uci(move):
    fr, to = move
    return f"{chr(ord('a') + (fr % 16))}{fr // 16 + 1}{chr(ord('a') + (to % 16))}{to // 16 + 1}"

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")

def post(path, body):
    req = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req) as res:
        return json.load(res)

board = Board()
while True:
    g = post("/game", {})
    if g["status"] == "done":
        break
    while g["status"] == "your_move":
        board.parse_fen(g["fen"])
        # Simple search for now
        legal_moves = [uci_to_move(m) for m in g["legal_moves"]]
        best_move = max(legal_moves, key=lambda move: -negamax(board, 2, -1000000, 1000000))
        g = post("/move", {"game": g["game"], "move": move_to_uci(best_move)})
