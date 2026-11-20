class Board:
    def __init__(self):
        self.b, self.side, self.castle, self.ep, self.king_sq = [0]*128, 0, 15, -1, [0,0]
    def parse_fen(self, fen):
        p = fen.split()
        r, c = 7, 0
        for char in p[0]:
            if char == '/': r -= 1; c = 0
            elif char.isdigit(): c += int(char)
            else:
                sq = r * 16 + c
                self.b[sq] = {'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6,'p':9,'n':10,'b':11,'r':12,'q':13,'k':14}[char]
                if self.b[sq] == 6: self.king_sq[0] = sq
                elif self.b[sq] == 14: self.king_sq[1] = sq
                c += 1
        self.side = 0 if p[1] == 'w' else 1
        self.castle = (1 if 'K' in p[2] else 0) | (2 if 'Q' in p[2] else 0) | (4 if 'k' in p[2] else 0) | (8 if 'q' in p[2] else 0)
        self.ep = -1 if p[3] == '-' else (ord(p[3][0])-97) + (int(p[3][1])-1)*16
    def is_attacked(self, sq, by):
        for d in [-33,-31,-18,-14,14,18,31,33]:
            if not ((sq+d)&0x88) and self.b[sq+d] == (2+(by*8)): return True
        for d in ([-17,-15] if by==0 else [15,17]):
            if not ((sq+d)&0x88) and self.b[sq+d] == (1+(by*8)): return True
        for d in [-17,-16,-15,-1,1,15,16,17]:
            t = sq + d
            while not (t & 0x88):
                if self.b[t]:
                    if self.b[t] == (6+(by*8)) and d in [-17,-16,-15,-1,1,15,16,17]: return True
                    if self.b[t] in ([3,5] if by==0 else [11,13]) and d in [-17,-15,15,17]: return True
                    if self.b[t] in ([4,5] if by==0 else [12,13]) and d in [-16,-1,1,16]: return True
                    break
                t += d
        return False
    def generate_moves(self):
        moves = []
        for i in range(128):
            if i & 0x88 or not self.b[i] or (self.b[i]>8)!=self.side: continue
            # ... simplified for brevity, will implement fully ...
        return moves
    def make_move(self, move):
        fr, to = move[:2]
        p, cap = self.b[fr], self.b[to]
        self.b[to], self.b[fr] = p, 0
        if p in [6,14]: self.king_sq[0 if p==6 else 1] = to
        old_side = self.side
        self.side = 1 - self.side
        return (cap, old_side)
    def unmake_move(self, move, record):
        fr, to = move[:2]
        cap, old_side = record
        p = self.b[to]
        self.b[fr], self.b[to] = p, cap
        if p in [6,14]: self.king_sq[0 if p==6 else 1] = fr
        self.side = old_side
    def perft(self, depth):
        if depth == 0: return 1
        n = 0
        for m in self.generate_moves():
            r = self.make_move(m)
            if not self.is_attacked(self.king_sq[1-self.side], self.side): n += self.perft(depth-1)
            self.unmake_move(m, r)
        return n
