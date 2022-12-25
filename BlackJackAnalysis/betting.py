from random import randrange

def GetPoker():
    num = randrange(0,27)
    num = int(num/2) + 1
    return num

def GenSeq(n):
    a = []
    for i in range(n):
        num = GetPoker()
        while i == 0 and num == 14:
            num = GetPoker()
        a.append(num)
    return a

def Judge(a,b):
    if b == 14:
        return 'J'
    elif a > b:
        return 'S'
    elif a < b:
        return 'L'
    else:
        return 'T'

def JudgeSeq(s):
    res = []
    if len(s) > 0:
        head = s[0]
        for i in range(1,len(s)):
            res.append(Judge(head,s[i]))
            if s[i] != 14:
                head = s[i]
    return res

class Player:
    def __init__(self, Strategy, cash):
        self.Strategy = Strategy
        # Tier index of the strategy
        self.Tier = 0
        self.ConseqWin = 0
        self.cash = cash
    
    def payFee(self, fee):
        self.cash -= fee
    
    
    def Decide(self, a):
        if a == 7:
            return 'L' if randrange(0,2) == 0 else 'S'
        elif a < 7:
            return 'L'
        else:
            return 'S'
    def ResetState(self):
        self.Tier = 0
        self.ConseqWin = 0

    def DidIWin(self, res):
        if res == 'W':
            self.ConseqWin += 1
            if self.ConseqWin >= self.Strategy[self.Tier] and self.Tier < len(self.Strategy) - 1:
                self.Tier += 1
        elif res == 'L':
            self.ResetState()

    def MakeBet(self, a):
        dec = self.Decide(a)
        difference = abs(a-7)

        if self.Strategy[self.Tier] == -1 :
            return dec
        
        if self.Tier >= difference:
            self.ResetState()
            return 'Q'
        else:
            return dec

class Game:
    def __init__(self, rounds, players):
        self.rounds = rounds
        self.seq = GenSeq(rounds)
        self.judgeSeq = JudgeSeq(self.seq)
        self.players = players
        self.playerStates = {}
        self.record = {}
        self.playerMoney = {}
        
        for p in self.players:
            self.record[p] = []
            self.playerStates[p] = 'Q'
            self.playerMoney[p] = 0

    def play(self):
        card = self.seq[0]
        for index in range(len(self.judgeSeq)):
            judge = self.judgeSeq[index]
            for p in self.players:
                res = 'T'
                if self.playerStates[p] == 'Q':
                    p.payFee(10)
                    self.playerStates[p] = 'P'
                    self.playerMoney[p] = 10
                dec = p.MakeBet(card)
                if dec == judge:
                    self.playerMoney[p] *= 2
                    res = 'W'
                elif judge == 'J':
                    self.playerMoney[p] += 100
                    res = 'J'
                elif dec == 'Q':
                    p.payFee(-1 * self.playerMoney[p])
                    self.playerMoney[p] = 0
                    self.playerStates[p] = 'Q'
                    res = 'W'
                elif judge == 'T':
                    res = 'T'
                elif dec != judge:
                    self.playerMoney[p] = 0
                    self.playerStates[p] = 'Q'
                    res = 'L'
                
                p.DidIWin(res)
                self.record[p].append((p.cash, p.ConseqWin,self.playerMoney[p],card, dec, res))

            if judge !='J':
                card = self.seq[index+1]
