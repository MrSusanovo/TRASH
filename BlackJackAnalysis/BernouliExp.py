from random import randrange, random
from math import sqrt
from matplotlib import pyplot as plt

def WinLose(p = 0.42, draw = 0.08):
    r = randrange(100)
    if r < 100*p:
        return 1
    else:
        return 0 if r < 100*(p+draw) else -1

def SampleDev(sample_avg, sample_count, p):
    sig = sqrt(p*(1-p))
    unit = sig/sqrt(sample_count)
    return (sample_avg-p)/unit*1.0

def GenSeq(rounds):
    seq = []
    for i in range(rounds):
        seq.append(WinLose())
    return seq

def Game(seq, factor = 2, base = 4, dev_unit = 1, bank_roll = 10000, bar = 20):
    rounds = len(seq)
    balance = bank_roll
    winrate_list = []
    devlist = []
    bet_list = []
    wins = 0
    total = 0
    blist = []
    #avgdev_list = []
    avgwin_list = []
    avgwin_large = []
    current_unit = base
    previous_sign = 0
    for i in range(rounds):
        total += 1
        win = seq[i]
        bet_list.append(current_unit)
        #wins += 1 if win > 0 else 0
        wins = sum(map(lambda x: x if x > 0 else 0, seq[i-bar:i]))*1.0/bar
        winrate_list.append(wins)
        avg_win = sum(winrate_list[max(0,i-bar):i])*1.0/bar
        avg_large = sum(winrate_list[max(0,i-5*bar):i])*1.0/(5*bar)

        balance += win * current_unit
        #dev = SampleDev(wins/total, total, 0.42)
        #dev = SampleDev(wins/total, total, 0.42) if i <= bar else SampleDev(sum(map(lambda x: x if x > 0 else 0, seq[i-bar:i]))*1.0/bar, bar, 0.42)
        #devlist.append(dev)
        #winrate_list.append(wins/total)
        blist.append(balance)
        #avg_dev = sum(devlist[max(0,i-bar):i])/bar
        #avgdev_list.append(avg_dev)
        avgwin_list.append(avg_win)
        avgwin_large.append(avg_large)
        if total >= bar:
            #current_unit = base * factor**int(dev/dev_unit)
            #new_unit = base * factor ** int(dev/dev_unit)
            sign = 0
            if wins < avg_win:
                sign = -1
            elif avg_win > avg_large:
                sign = 1        
            if sign != previous_sign:
                #current_unit = base*factor**int(sign * abs(dev/dev_unit))
                current_unit = base*factor**int(sign * 3)
                previous_sign = sign

        
    #return (winrate_list,blist,devlist,bet_list,avgdev_list)
    return (avgwin_list,blist,bet_list,avgwin_large,winrate_list)

def Draw(res, index,i,j):
    fig,left = plt.subplots()
    right = left.twinx()
    left.plot(res[i][:index], color="black")
    right.plot(res[j][:index], color="red")
    plt.show()

def Draw1(res,i,j = None):
    fig,left = plt.subplots()
    #right = left.twinx()
    left.plot(res[i], color="black")
    if j != None:
        left.plot(res[j], color="red")
    plt.show()

def GenerateHiLoDeck(count):
    positive = 5*4*count
    neutral = 3*4*count
    negative = 5*4*count
    lst = []
    for i in range(positive):
        lst.append(1)
    for i in range(neutral):
        lst.append(0)
    for i in range(negative):
        lst.append(-1)
    return (lst,positive,neutral,negative)

class DeckCounter:
    def __init__(self,count, dp_percent):
        self.dp_percent = dp_percent
        self.count = count
        self.setup(count)

    def setup(self,count):
        tup = GenerateHiLoDeck(count)
        self.deck = tup[0]
        self.positive = tup[1]
        self.neutral = tup[2]
        self.total = count * 4 * 13
        self.dp = int(self.total * self.dp_percent)
        self.rc = 0

    def draw(self):
        idx = randrange(0,len(self.deck))
        if idx < self.positive:
            self.positive -= 1
            self.deck = self.deck[1:]
            self.rc += 1
            return 1
        if idx < self.positive + self.neutral and self.neutral > 0:
            self.deck[self.positive+self.neutral-1] = -1
            self.neutral -= 1
            self.deck.pop()
            return 0
        card = self.deck.pop()
        self.rc += card
        return card

    def GetTc(self):
        return self.rc / (len(self.deck)/52)
    
    def GetWinRate(self):
        return 0.495 + self.GetTc()*0.005
    
    def shuffle(self):
        if len(self.deck) <= self.dp:
            self.setup(self.count)

def game(rounds, dp = 0.5, balance = 5000, unit = 20, ucut = 3, minbet = 1):
    dc = DeckCounter(8,dp)
    winrates = []
    wins = []
    B1 = []
    B2 = []
    R1 = []
    R2 = []
    b1 = b2 = balance
    for round in range(rounds):
        edge = dc.GetWinRate() - 0.5
        bet = minbet if (edge <= 0 or (edge/0.005) * unit <= minbet) else (edge/0.005) * unit
        bet = int(bet)
        bet2 = bet if bet <= ucut * unit else ucut * unit
        B1.append(bet)
        B2.append(bet2)
        # Assuming 4 cards for each round
        for i in range(4):
            dc.draw()
        winrate = dc.GetWinRate()
        winrates.append(winrate)
        chance = random()
        win = 1 if chance < winrate else -1
        wins.append(win)
        b1 += win * bet
        b2 += win * bet2
        R1.append(b1)
        R2.append(b2)
        dc.shuffle()
    return (winrates,wins,B1,B2,R1,R2)

def game1(rounds, dp = 0.5, balance = 5000, unit = 20, ucut = 3, minbet = 1):
    dc = DeckCounter(8,dp)
    winrates = []
    wins = []
    B1 = []
    R1 = []
    b1 = balance
    for round in range(rounds):
        edge = dc.GetWinRate() - 0.5
        bet = minbet if (edge <= 0 or (edge/0.005) * unit <= minbet) else (edge/0.005) * unit
        bet = int(bet)
        if b1 < bet:
            break
        B1.append(bet)
        # Assuming 4 cards for each round
        for i in range(4):
            dc.draw()
        winrate = dc.GetWinRate()
        winrates.append(winrate)
        chance = random()
        win = 1 if chance < winrate else -1
        wins.append(win)
        b1 += win * bet
        R1.append(b1)
        dc.shuffle()
    return (winrates,wins,B1,R1)

def game2(rounds, dp = 0.5, balance = 5000, unit = 20, ucut = 3, minbet = 1):
    dc = DeckCounter(8,dp)
    winrates = []
    wins = []
    B2 = []
    R2 = []
    b2 = balance
    for round in range(rounds):
        edge = dc.GetWinRate() - 0.5
        bet = minbet if (edge <= 0 or (edge/0.005) * unit <= minbet) else (edge/0.005) * unit
        bet = int(bet)
        bet2 = bet if bet <= ucut * unit else ucut * unit
        if b2 < bet2:
            break
        B2.append(bet2)
        # Assuming 4 cards for each round
        for i in range(4):
            dc.draw()
        winrate = dc.GetWinRate()
        winrates.append(winrate)
        chance = random()
        win = 1 if chance < winrate else -1
        wins.append(win)
        b2 += win * bet2
        R2.append(b2)
        dc.shuffle()
    return (winrates,wins,B2,R2)

def RoR(GAME, sim = 10000, rounds = 10000, dp=0.5, balance=5000, unit = 20, ucut = 3, minbet = 1):
    lose_rounds = []
    win_rounds = []
    fuck_up_rounds = []
    max_draws = []
    bets = []
    weights = []
    for s in range(sim):
        res=GAME(rounds,dp,balance,unit,ucut,minbet)
        if len(res[-1]) < rounds:
            fuck_up_rounds.append(len(res[-1]))
        elif res[-1][-1] < balance:
            lose_rounds.append(res[-1][-1])
            max_draws.append(min(res[-1]))
        else:
            win_rounds.append(res[-1][-1])
            max_draws.append(min(res[-1]))
        weights.append(len(res[-2])/rounds)
        bets.append(sum(res[-2])/len(res[-2]))
    return(lose_rounds,win_rounds,fuck_up_rounds,max_draws,bets,weights)

    


        