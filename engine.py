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

    def is_attacked(self, sq, by_side):
        # Attacker side: 0=White, 1=Black
        knight_off = [-33, -31, -18, -14, 14, 18, 31, 33]
        king_off = [-17, -16, -15, -1, 1, 15, 16, 17]
        pawn_off = [-17, -15] if by_side == 0 else [15, 17]

        # Check Knights
        for d in knight_off:
            t = sq + d
            if not (t & 0x88) and self.b[t] == (2 + (by_side * 8)): return True

        # Check Pawns
        for d in pawn_off:
            t = sq + d
            if not (t & 0x88) and self.b[t] == (1 + (by_side * 8)): return True

        # Sliding pieces + King
        for d in [-17, -16, -15, -1, 1, 15, 16, 17]:
            t = sq + d
            while not (t & 0x88):
                p = self.b[t]
                if p:
                    # Check for King
                    if p == (6 + (by_side * 8)) and d in king_off: return True
                    # Check for Sliding
                    if p in ([3, 5] if by_side == 0 else [11, 13]): # Bishop/Queen
                        if d in [-17, -15, 15, 17]: return True
                    if p in ([4, 5] if by_side == 0 else [12, 13]): # Rook/Queen
                        if d in [-16, -1, 1, 16]: return True
                    break # Blocked
                t += d
        return False

    def generate_moves(self):
        moves = []
        for i in range(128):
            if i & 0x88: continue
            p = self.b[i]
            if not p or (p > 8) != self.side: continue

            # ... (omitted) ...

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
            # Sliding piece moves (Bishop, Rook, Queen)
            elif p in [3, 4, 5, 11, 12, 13]:
                # Define directions
                dirs = []
                if p in [3, 5, 11, 13]: dirs += [-17, -15, 15, 17] # Bishop / Queen diagonal
                if p in [4, 5, 12, 13]: dirs += [-16, -1, 1, 16] # Rook / Queen orthogonal
                for d in dirs:
                    to = i + d
                    while not (to & 0x88):
                        target = self.b[to]
                        if not target:
                            moves.append((i, to))
                        elif (target > 8) != self.side:
                            moves.append((i, to))
                            break
                        else: # Friendly piece
                            break
                        to += d
        return moves

    def make_move(self, move):
        fr, to = move
        p = self.b[fr]
        captured = self.b[to]
        self.b[to] = p
        self.b[fr] = 0
        if p in [6, 14]:
            self.king_sq[0 if p == 6 else 1] = to
        
        old_side = self.side
        self.side = 1 - self.side
        return (captured, old_side)

    def unmake_move(self, move, record):
        fr, to = move
        captured, old_side = record
        p = self.b[to]
        self.b[fr] = p
        self.b[to] = captured
        if p in [6, 14]:
            self.king_sq[0 if p == 6 else 1] = fr
        self.side = old_side

    def perft(self, depth):
        if depth == 0: return 1
        nodes = 0
        for move in self.generate_moves():
            record = self.make_move(move)
            # Check if king is attacked by opponent (the side that just moved is now opponent)
            if not self.is_attacked(self.king_sq[1 - self.side], self.side):
                nodes += self.perft(depth - 1)
            self.unmake_move(move, record)
        return nodes
