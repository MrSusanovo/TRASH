from random import randrange

class BasicDeck:
    def __init__(self,dCount, DP = -1, quiet = True):
        self.deck_count = dCount
        self.deck = []
        self.drawn_stack = []
        self.init_deck()
        self.DPenetration = randrange(0,len(self.deck)) if DP == -1 else DP
        self.quiet = quiet
        #self.deck_size = 0
    
    def init_deck(self):
        self.deck.clear()
        self.drawn_stack.clear()
        #self.deck_size = self.deck_count*4*13
        for i in range(self.deck_count):
            for j in range(4):
                for k in range(13):
                    self.deck.append(k+1)
    
    def draw_card(self):
        deck_size = len(self.deck)
        index = randrange(0,deck_size)
        #index = randrange(0,self.deck_size)
        swap_slot = self.deck[index]
        self.deck[index] = self.deck[deck_size-1]
        #self.deck[index] = self.deck[self.deck_size-1]
        self.deck[deck_size-1] = swap_slot
        #self.deck[self.deck_size-1] = swap_slot
        self.drawn_stack.append(self.deck.pop())
        #self.deck_size -= 1
        # Shuffle if we reached our penetration.
        # if len(self.drawn_stack) >= self.DPenetration:
            # self.shuffle()
        return swap_slot if swap_slot <= 10 else 10
    
    def shuffle(self):
        if len(self.drawn_stack) >= self.DPenetration:
            if False == self.quiet:
                print("Shuffling")
            for card in self.drawn_stack:   
                self.deck.append(card)
            self.drawn_stack.clear()
    
    def get_hi_lo(self):
        count = 0
        for i in self.drawn_stack:
            if i >= 2 and i <= 6:
                count += 1
            elif (i >= 10 and i <= 13) or (i == 1):
                count -= 1
        return (count*4*13)/(len(self.deck))

class SpecialDeck(BasicDeck):
    def __init__(self, dCount, DP = -1, trueCount = 0, clear_card = -1, quiet = True):
        self.deck_count = dCount
        self.deck = []
        self.drawn_stack = []
        self.init_deck(trueCount, clear_card)
        self.DPenetration = randrange(0,len(self.deck)) if DP == -1 else DP
        self.quiet = quiet
    
    def init_deck(self, tCount, clear_card):
        self.deck.clear()
        self.drawn_stack.clear()
        self.true_count = tCount
        total = abs(tCount) * self.deck_count
        card_removed = False
        for i in range(self.deck_count):
            for j in range(4):
                for k in range(13):
                    if total > 0:
                        # skip for making a deck with true count
                        if (tCount > 0 and (k >= 1 and k <= 5)) or ( tCount < 0 and (k > 5 and k <= 12 or k == 1)):
                            total -= 1
                            continue
                    card = k+1
                    # skip for making a deck with 1 card removed
                    if card_removed == False and clear_card == card:
                        card_removed = True
                        continue
                    self.deck.append(card)
