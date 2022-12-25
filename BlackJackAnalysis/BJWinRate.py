from Decks import SpecialDeck
from BlackJackSimulation import Dealer, CalculatePoint

def BustRate(deck_count, rounds=10000, true_count = 0, dp = 0):
    result = {"rounds": rounds}
    for i in range(1,11):
        deck = SpecialDeck(deck_count, dp, true_count, i)
        dealer = Dealer(False, deck)
        dealer.clear_card = i
        result[i] = {}
        temp = {}
        for r in range(rounds):
            dealer.draw_hidden()
            dealer.decision()
            k = dealer.points if dealer.points <= 21 else 22
            temp[k] = temp.get(k,0) + 1
            deck.shuffle()
            dealer.clear()
        result[i] = {k: v for k, v in sorted(temp.items(), key=lambda x: x[0])}
    return result

def BustRateRange(deck_count, rounds=10000, R = range(-4,5), dp=0, devide = True):
    rates = {}
    f_rounds = float(rounds)
    for true_count in R:
        rates[true_count] = {}
        rate = BustRate(deck_count, rounds, true_count, dp)
        for clear_card in range(1,11):
            r = {a:b/f_rounds for a, b in rate[clear_card].items()}
            rates[true_count][clear_card] = r
    return rates

def PlayerWinRate(deck_count, play_logic_func , rounds=10000, true_count = 0, dp = 0):
    hresult = {"rounds": rounds}
    sresult = {"rounds": rounds}
    presult = {"rounds": rounds}
    for i in range(1, 11):
        # setup deck
        deck = SpecialDeck(deck_count, dp, true_count, i)
        
        # setup dealer
        dealer = Dealer(False, deck)
        dealer.clear_card = i

        # setup player
        player_cards = []        

        hresult[i] = {}
        sresult[i] = {}
        presult[i] = {}

        htemp = {}
        stemp = {}
        ptemp = {}
        for r in range(rounds):
            # clear all 
            deck.shuffle()
            dealer.cards.clear()
            dealer.blackjack = False
            player_cards.clear()
            score_stack = []

            # player draw two cards
            player_cards.append(deck.draw_card())
            player_cards.append(deck.draw_card())

            # check if player blackjacked
            player_blackjack = sum(player_cards) == 11 and max(player_cards) == 10

            # dealer draw hidden card
            dealer.draw_hidden()
            dealer_blackjack = dealer.blackjack

            # First check blackjack
            if player_blackjack == True:
                new_tup = stemp.get(23,[0,0,0])
                if dealer_blackjack == False:
                    new_tup[0] += 1
                else:
                    new_tup[2] += 1
                
                stemp[23] = new_tup
                continue

            # If dealer blackjack
            is_split = player_cards[0] == player_cards[1]
            k, is_soft = CalculatePoint(player_cards)
            temp = ptemp if is_split else htemp
            if dealer_blackjack == True:
                #rint("Dealer Blackjack")
                new_tup = stemp.get(k,[0,0,0]) if is_soft == True else temp.get(k,[0,0,0])
                new_tup[1] += 1
                if is_soft == False:
                    temp[k] = new_tup
                else:
                    stemp[k] = new_tup
                continue

            # Play the game
            player_point = play_logic_func(deck, player_cards, True, score_stack)
            dealer.decision()
            index = 0 # 0 is win, 1 is lose
            if player_point > 21 or (dealer.points <= 21 and dealer.points > player_point):
                index = 1
            elif player_point == dealer.points:
                index = 2
            #print("len?:",len(score_stack))
            for tup in score_stack:
                temp = stemp if tup[1] == True else htemp
                temp = ptemp if tup[2] == True else temp
                new_tup = temp.get(tup[0],[0,0,0])
                new_tup[index] += 1
                temp[tup[0] if tup[0] <= 21 else 22] = new_tup
        
        hresult[i] = {k: v for k, v in sorted(htemp.items(), key=lambda x: x[0])}
        sresult[i] = {k: v for k, v in sorted(stemp.items(), key=lambda x: x[0])}
        presult[i] = {k: v for k, v in sorted(ptemp.items(), key=lambda x: x[0])}
    
    return (hresult,sresult,presult)

            

            



