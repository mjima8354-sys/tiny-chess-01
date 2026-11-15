class Board:
    def __init__(self):
        self.b = [0] * 128
        self.side = 0
        self.castle = 15
        self.ep = -1
        self.king_sq = [0, 0]

    def parse_fen(self, fen):
        p = fen.split()
        r, c = 7, 0
        for char in p[0]:
            if char == '/': r -= 1; c = 0
            elif char.isdigit(): c += int(char)
            else:
                sq = r * 16 + c
                piece = {'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6,'p':9,'n':10,'b':11,'r':12,'q':13,'k':14}[char]
                self.b[sq] = piece
                if piece == 6: self.king_sq[0] = sq
                elif piece == 14: self.king_sq[1] = sq
                c += 1
        self.side = 0 if p[1] == 'w' else 1
        self.castle = (1 if 'K' in p[2] else 0) | (2 if 'Q' in p[2] else 0) | (4 if 'k' in p[2] else 0) | (8 if 'q' in p[2] else 0)
        self.ep = -1 if p[3] == '-' else (ord(p[3][0])-97) + (int(p[3][1])-1)*16

    def generate_moves(self):
        moves = []
        for i in range(128):
            if i & 0x88: continue
            p = self.b[i]
            if not p or (p > 8) != self.side: continue
            
            # Pawn moves
            if p == 1: # White Pawn
                if i + 16 < 128 and not self.b[i+16]:
                    moves.append((i, i+16))
                    if 16 <= i < 32 and not self.b[i+32]:
                        moves.append((i, i+32))
            elif p == 9: # Black Pawn
                if i - 16 >= 0 and not self.b[i-16]:
                    moves.append((i, i-16))
                    if 96 <= i < 112 and not self.b[i-32]:
                        moves.append((i, i-32))
            # Knight moves
            elif p in [2, 10]:
                for d in [-33, -31, -18, -14, 14, 18, 31, 33]:
                    to = i + d
                    if not (to & 0x88):
                        target = self.b[to]
                        if not target or (target > 8) != self.side:
                            moves.append((i, to))
            # ... other pieces
        return moves

    def make_move(self, move):
        fr, to = move
        p = self.b[fr]
        self.b[to] = p
        self.b[fr] = 0
        return None

    def unmake_move(self, move, record):
        fr, to = move
        p = self.b[to]
        self.b[fr] = p
        self.b[to] = 0

    def perft(self, depth):
        if depth == 0: return 1
        nodes = 0
        for move in self.generate_moves():
            record = self.make_move(move)
            nodes += self.perft(depth - 1)
            self.unmake_move(move, record)
        return nodes
