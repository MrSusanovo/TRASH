from Decks import *

def Bucketize(f):
    floor = int(f) if f >= 0 else int(f) - 1
    return floor + 0.5 if (f-floor)>=0.5 else floor

def DPandTC(deck_count = 8, dp = 4, counting = 'hilo', rounds=10000):
    data = []
    deck = BasicDeck(deck_count,dp)
    for r in range(rounds):
        deck.init_deck()
        hand_counter = 0
        for draw in range(dp*13*4):
            deck.draw_card()
            #tc = Bucketize(deck.get_hi_lo())
            tc = deck.get_hi_lo()
            # true count, round number, the draw number, every 4 th draw is the player hand
            data.append((tc,r,draw))
    return data
