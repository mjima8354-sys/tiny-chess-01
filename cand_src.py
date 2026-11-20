#tiny chess engine <4096B packed: alpha-beta, mvv-lva, pst, quiescence, iterative deepening, deterministic node budget
import sys, json, os, urllib.request, urllib.error

P,N,B,R,Q,K=1,2,3,4,5,6
WHITE,BLACK=0,1
KN=(-33,-31,-18,-14,14,18,31,33)
DIAG=(-17,-15,15,17)
ORTH=(-16,-1,1,16)
ALL8=DIAG+ORTH
PST_N=( -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50)
PST_B=( -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20)
PST_R=(  0,  0,  5, 10, 10,  5,  0,  0,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
         0,  0,  5, 10, 10,  5,  0,  0)
PST_Q=( -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -10,  5,  5,  5,  5,  5,  0,-10,
          0,  0,  5,  5,  5,  5,  0, -5,
         -5,  0,  5,  5,  5,  5,  0, -5,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20)
PST_K=(-30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -20,-30,-30,-40,-40,-30,-30,-20,
       -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20)
PST_P=(  0,  0,  0,  0,  0,  0,  0,  0,
         50, 50, 50, 50, 50, 50, 50, 50,
         10, 10, 20, 30, 30, 20, 10, 10,
          5,  5, 10, 25, 25, 10,  5,  5,
          0,  0,  0, 20, 20,  0,  0,  0,
          5, -5,-10,  0,  0,-10, -5,  5,
          5, 10, 10,-20,-20, 10, 10,  5,
          0,  0,  0,  0,  0,  0,  0,  0)
VAL=(0,100,320,330,500,900,20000)
PST=(0,PST_P,PST_N,PST_B,PST_R,PST_Q,PST_K)

class Board:
    def __init__(self):
        self.s=[0]*128
        self.side=WHITE
        self.castle=0
        self.ep=-1
        self.k=[0,0]
    def set_fen(self,fen):
        parts=fen.split()
        self.s=[0]*128
        r,c=7,0
        for ch in parts[0]:
            if ch=='/': r-=1; c=0
            elif ch.isdigit(): c+=int(ch)
            else:
                t={'p':P,'n':N,'b':B,'r':R,'q':Q,'k':K}[ch.lower()]
                if ch.isupper(): self.s[r*16+c]=t
                else: self.s[r*16+c]=t|8
                c+=1
        self.side=WHITE if parts[1]=='w' else BLACK
        self.castle=0
        if 'K' in parts[2]: self.castle|=1
        if 'Q' in parts[2]: self.castle|=2
        if 'k' in parts[2]: self.castle|=4
        if 'q' in parts[2]: self.castle|=8
        self.ep=-1 if parts[3]=='-' else (ord(parts[3][0])-97)+(int(parts[3][1])-1)*16
        self.k=[self.king_sq(WHITE),self.king_sq(BLACK)]
    def king_sq(self,color):
        target=K if color==WHITE else K|8
        for i in range(128):
            if not i&0x88 and self.s[i]==target: return i
        return -1
    def attacked(self,sq,by):
        s=self.s
        # pawns
        if by==WHITE:
            for d in (-15,-17):
                t=sq+d
                if not t&0x88 and s[t]==P: return True
        else:
            for d in (15,17):
                t=sq+d
                if not t&0x88 and s[t]==(P|8): return True
        for d in KN:
            t=sq+d
            if not t&0x88 and s[t]==(N|(8 if by else 0)): return True
        for d in DIAG:
            t=sq+d
            while not t&0x88:
                p=s[t]
                if p:
                    if (p&7) in (B,Q) and (p>>3)==by: return True
                    break
                t+=d
        for d in ORTH:
            t=sq+d
            while not t&0x88:
                p=s[t]
                if p:
                    if (p&7) in (R,Q) and (p>>3)==by: return True
                    break
                t+=d
        for d in ALL8:
            t=sq+d
            if not t&0x88 and s[t]==(K|(8 if by else 0)): return True
        return False
    def gen_pseudo(self):
        s=self.s; side=self.side; out=[]
        for i in range(128):
            if i&0x88: continue
            p=s[i]
            if not p or p>>3!=side: continue
            t=p&7
            if t==P:
                d=16 if side==WHITE else -16
                t1=i+d
                if not t1&0x88 and not s[t1]:
                    if (t1>>4)==(7 if side==WHITE else 0):
                        for pp in (Q,R,B,N): out.append((i,t1,0,t,pp))
                    else: out.append((i,t1,0,t,0))
                    if (i>>4)==(1 if side==WHITE else 6) and not s[i+2*d]:
                        out.append((i,i+2*d,0,t,0))
                for dd in (d-1,d+1):
                    t2=i+dd
                    if t2&0x88: continue
                    if s[t2] and s[t2]>>3!=side:
                        if (t2>>4)==(7 if side==WHITE else 0):
                            for pp in (Q,R,B,N): out.append((i,t2,s[t2],t,pp))
                        else: out.append((i,t2,s[t2],t,0))
                    elif t2==self.ep:
                        out.append((i,t2,0,t,0))
            elif t==N:
                for d in KN:
                    t1=i+d
                    if not t1&0x88 and (not s[t1] or s[t1]>>3!=side): out.append((i,t1,s[t1],t,0))
            elif t==K:
                for d in ALL8:
                    t1=i+d
                    if not t1&0x88 and (not s[t1] or s[t1]>>3!=side): out.append((i,t1,s[t1],t,0))
                if side==WHITE and i==4:
                    if self.castle&1 and not s[5] and not s[6] and not self.attacked(4,BLACK) and not self.attacked(5,BLACK) and not self.attacked(6,BLACK): out.append((4,6,0,t,0))
                    if self.castle&2 and not s[3] and not s[1] and not self.attacked(4,BLACK) and not self.attacked(3,BLACK) and not self.attacked(2,BLACK): out.append((4,2,0,t,0))
                elif side==BLACK and i==116:
                    if self.castle&4 and not s[117] and not s[118] and not self.attacked(116,WHITE) and not self.attacked(117,WHITE) and not self.attacked(118,WHITE): out.append((116,118,0,t,0))
                    if self.castle&8 and not s[115] and not s[114] and not s[113] and not self.attacked(116,WHITE) and not self.attacked(115,WHITE) and not self.attacked(114,WHITE): out.append((116,114,0,t,0))
            else:
                dirs=DIAG if t==B else ORTH if t==R else ALL8
                for d in dirs:
                    t1=i+d
                    while not t1&0x88:
                        if not s[t1]: out.append((i,t1,0,t,0))
                        else:
                            if s[t1]>>3!=side: out.append((i,t1,s[t1],t,0))
                            break
                        t1+=d
        return out
    def make(self,mv):
        i,t,cap,pt,promo=mv
        s=self.s; p=s[i]
        rec=(self.castle,self.ep,p)
        self.ep=-1
        s[t]=p if not promo else (promo if p>>3==0 else promo|8)
        s[i]=0
        pt2=p&7
        if pt2==K: self.k[p>>3]=t
        if pt2==P:
            if t==rec[1] and cap==0 and (t-i) in (15,17,-15,-17):
                # en passant capture
                capd=t-16 if p>>3==0 else t+16
                s[capd]=0
            if abs(t-i)==32: self.ep=(i+t)//2
        if pt2==K:
            if p>>3==0: self.castle&=~3
            else: self.castle&=~12
            if abs(t-i)==2:
                if t>i: s[t-1]=s[t+1]; s[t+1]=0
                else: s[t+1]=s[t-2]; s[t-2]=0
        if i==4 or t==4: self.castle&=~3
        if i==116 or t==116: self.castle&=~12
        if i==7 or t==7: self.castle&=~1
        if i==0 or t==0: self.castle&=~2
        if i==119 or t==119: self.castle&=~4
        if i==112 or t==112: self.castle&=~8
        self.side=1-self.side
        return rec
    def unmake(self,mv,rec):
        i,t,cap,pt,promo=mv
        s=self.s
        self.castle,self.ep,orig=rec
        s[i]=orig
        s[t]=0
        pt2=orig&7
        if pt2==P:
            if t==self.ep and cap==0 and (t-i) in (15,17,-15,-17):
                capd=t-16 if orig>>3==0 else t+16
                s[capd]=P|(8 if orig>>3==0 else 0)
        elif pt2==K and abs(t-i)==2:
            if t>i: s[t+1]=s[t-1]; s[t-1]=0
            else: s[t-2]=s[t+1]; s[t+1]=0
        if cap: s[t]=cap
        self.side=1-self.side
        if orig&7==K: self.k[orig>>3]=i
    def legal_moves(self):
        out=[]
        for mv in self.gen_pseudo():
            rec=self.make(mv)
            ks=self.k[1-self.side]
            if ks>=0 and not self.attacked(ks,self.side): out.append(mv)
            self.unmake(mv,rec)
        return out
    def eval(self):
        sc=0
        for i in range(128):
            if i&0x88: continue
            p=self.s[i]
            if not p: continue
            t=p&7
            idx=(((7-(i>>4))<<3)|(i&15)) if p>>3==0 else ((i>>4)<<3)|(i&15)
            v=VAL[t]+PST[t][idx]
            sc+= v if p>>3==0 else -v
        return sc if self.side==WHITE else -sc

nodes=0
node_cap=0
class Budget(Exception): pass

MVV_LVA=(0,10,9,9,5,4,2)
def qsearch(bd,alpha,beta,ply=0):
    global nodes
    nodes+=1
    if nodes>node_cap: raise Budget()
    if ply>18: return bd.eval()
    side=bd.side
    ownk=bd.k[side]
    inchk=ply<6 and ownk>=0 and bd.attacked(ownk,1-side)
    if not inchk:
        stand=bd.eval()
        if stand>=beta: return beta
        if stand>alpha: alpha=stand
        mvs=[m for m in bd.gen_pseudo() if m[2]]
    else:
        mvs=bd.gen_pseudo()
        if not mvs: return -30000
    for mv in mvs:
        rec=bd.make(mv)
        ks=bd.k[side]
        if ks>=0 and bd.attacked(ks,bd.side):
            bd.unmake(mv,rec); continue
        v=-qsearch(bd,-beta,-alpha,ply+1)
        bd.unmake(mv,rec)
        if v>=beta: return beta
        if v>alpha: alpha=v
    return alpha

def search(bd,depth,alpha,beta):
    global nodes
    nodes+=1
    if nodes>node_cap: raise Budget()
    side=bd.side
    legal=bd.legal_moves()
    if not legal:
        return -30000 if bd.attacked(bd.k[side],1-side) else 0
    inchk=bd.attacked(bd.k[side],1-side)
    if inchk: depth+=1
    if depth<=0:
        return qsearch(bd,alpha,beta)
    legal.sort(key=lambda m:(0 if m[2] else 1)*1000-(MVV_LVA[m[2]&7]-MVV_LVA[m[3]])*10-(m[4] and 500),)
    best=-10**9
    for mv in legal:
        rec=bd.make(mv)
        v=-search(bd,depth-1,-beta,-alpha)
        bd.unmake(mv,rec)
        if v>best: best=v
        if v>alpha: alpha=v
        if alpha>=beta: break
    return best

def best_move(bd,steps,node_budget):
    global nodes,node_cap
    nodes=0
    node_cap=nodes+node_budget
    best=None
    try:
        node_cap=node_budget
        for d in range(1,steps+1):
            legal=bd.legal_moves()
            legal.sort(key=lambda m:(0 if m[2] else 1)*1000-(MVV_LVA[m[2]&7]-MVV_LVA[m[3]])*10-(m[4] and 500))
            cur=None; alpha=-10**9; beta=10**9
            for mv in legal:
                rec=bd.make(mv)
                v=-search(bd,d-1,-beta,-alpha)
                bd.unmake(mv,rec)
                if v>alpha: alpha=v; cur=mv
            best=cur if cur else best
    except Budget:
        pass
    return best

def uci(mv):
    def sq(x): return chr(97+(x&15))+str(1+(x>>4))
    s=sq(mv[0])+sq(mv[1])
    if mv[4]: s+={Q:'q',R:'r',B:'b',N:'n'}[mv[4]]
    return s

def main():
    E=os.environ.get('MAKEFUN_ENV_URL')
    if not E: sys.exit('no MAKEFUN_ENV_URL')
    def POST(path,obj):
        req=urllib.request.Request(E+path,data=json.dumps(obj).encode(),headers={'content-type':'application/json'})
        try: return json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as e: sys.exit(path+':HTTP'+str(e.code))
    bd=Board()
    node_budget=120000
    while True:
        g=POST('/game',{})
        if g.get('status')=='done':
            print('done',g.get('wins'),g.get('draws'),g.get('losses'),file=sys.stderr)
            break
        while g.get('status')=='your_move':
            bd.set_fen(g['fen'])
            mv=best_move(bd,10,node_budget)
            if mv is None:
                g=POST('/resign',{'game':g['game']}); break
            g=POST('/move',{'game':g['game'],'move':uci(mv)})
if __name__=='__main__': main()