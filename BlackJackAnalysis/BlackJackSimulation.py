from Decks import *

def CalculatePoint(cards):
    hard_point = 0
    soft_point = 0
    has_ace = False
    is_soft = False
    for card in cards:
        hard_point += card
        soft_point += card
        if card == 1:
            if has_ace == False and soft_point <= 11:
                soft_point += 10
                is_soft = True
            has_ace = True
        if hard_point < soft_point and soft_point > 21 and hard_point <= 21:
            soft_point -= 10
            is_soft = False

    return (max(hard_point, soft_point), is_soft)

def DealerLogic(deck, cards, stand_s17 = False, point_stack = None, quiet = True):
    points = 0
    is_soft = False
    while True:
        points, is_soft = CalculatePoint(cards)
        if point_stack != None:
            is_split = False if len(cards) != 2 or cards[0] != cards[1] else True
            point_stack.append((points, is_soft, is_split))
        if False == quiet:
            print(points, is_soft)
        if points == 17:
            if is_soft == False or stand_s17 == True:
                break
        elif points > 17:
            break
        card = deck.draw_card()
        if False == quiet:
            print("Draw card:", card)
        cards.append(card)
    if False == quiet:
        print("All Cards:", cards)
    return points

def StopperLogic(deck, cards, stand_s17 = False, point_stack = None, quiet = True):
    points, is_soft = CalculatePoint(cards)
    is_split = False if len(cards) != 2 or cards[0] != cards[1] else True
    if point_stack != None:
        point_stack.append((points, is_soft, is_split))
    return points

class Dealer:
    def __init__(self,S17, deck, quiet = True):
        self.stand_s17 = S17 # Stand on soft 17
        self.deck = deck
        self.clear_card = 0
        self.hidden_card = 0
        self.points = 0
        self.blackjack = False
        self.hard = False
        self.quiet = True
        self.cards = []
    
    def draw_clear(self):
        self.clear_card = self.deck.draw_card()
        
    def draw_hidden(self):
        self.hidden_card = self.deck.draw_card()

        if self.clear_card + self.hidden_card == 11 and (self.clear_card == 1 or self.hidden_card == 1):
            self.blackjack = True

        if self.clear_card != 1 and self.hidden_card != 1:
            self.hard = True
    
    def decision(self):
        bonus = 0
        if False == self.quiet:
            print("Dealer base cards:", self.hidden_card, self.clear_card)
        self.cards = [self.hidden_card, self.clear_card] if self.hidden_card != 0 and self.clear_card != 0 else []
        '''
        points = 0
        is_soft = False
        while True:
            points, is_soft = CalculatePoint(self.cards)
            if False == self.quiet:
                print(points, is_soft)
            if points == 17:
                if is_soft == False or self.stand_s17 == True:
                    break
            elif points > 17:
                break
            card = self.deck.draw_card()
            if False == self.quiet:
                print("Dealer draw:", card)
            self.cards.append(card)
        if False == self.quiet:
            print("Dealer Cards:", self.cards)
        self.points = points
        '''
        self.points = DealerLogic(self.deck, self.cards, self.stand_s17)
    
    def clear(self):
        self.hidden_card = self.clear_card = 0
        self.blackjack = False
        self.cards.clear()
    
class Player:
    def __init__(self,deck, strategy_file = None):
        self.deck = deck
        self.bank_roll = 0
        self.strategy_file = strategy_file
        self.cards = []
        self.slot_info = []
        self.bets = []

    def clear_slots(self):
        self.cards.clear()
        self.slot_info.clear()
        self.bets.clear()

    def clear_slot(self, i):
        self.cards[i].clear()
        self.slot_info[i].clear()

    def bet(self, MAX, MIN):
        if self.strategy_file == None:
            player_bet = int(input("Place your bet:"))
            if player_bet <= self.bank_roll and player_bet <= MAX and player_bet >= MIN:
                self.bank_roll -= player_bet
                self.bets.append(player_bet)
                print("My bets:",self.bets)
                return player_bet
            else:
                return False

    # True for normal, number for blackjack
    def draw_two(self, dealer_blackjack = False):
        self.cards.append([])
        self.slot_info.append({"Doubled": False, "Splitted": False, "Hit": True})
        self.cards[0].append(self.deck.draw_card())
        self.cards[0].append(self.deck.draw_card())

        print("My Cards:",self.cards[0])
        print("My Points:",sum(self.cards[0]))

        # Check for blackjack
        if True == dealer_blackjack:
            print("Dealer Blackjack!")
        total_bet = sum(self.bets)
        if max(self.cards[0]) == 10 and sum(self.cards[0]) == 11:
            self.bank_roll += self.bets[0] if dealer_blackjack == True else 1.5 * self.bets[0]
            print("You got Blackjack! total bet:", total_bet)
            self.clear_slots()
            return total_bet
        if dealer_blackjack == True:
            self.clear_slots()
            return -total_bet
        
        return False
    
    #  True for success, false for bust
    def hit(self, i = 0):
        if self.slot_info[i]["Hit"] == True:
            self.cards[i].append(self.deck.draw_card())
            print("Hit Cards, roll",i,":", self.cards[i])

            if CalculatePoint(self.cards[i])[0] > 21:
                self.slot_info[i]["Hit"] = False
                return False
                #self.clear_slot(i)
                #return sum(self.bets)
        return True
    
    # Callee ensures split is valid, check for card and bet
    def split(self, i = 0):
        if self.bank_roll >= self.bets[i] and self.cards[i][0] == self.cards[i][1] and self.slot_info[i]["Splitted"] == False:
            self.slot_info.append({"Doubled": False, "Splitted": False, "Hit": True})
            self.cards.append([self.cards[i].pop()])
            self.bets.append(self.bets[i])
            self.bank_roll -= self.bets[i]
            self.slot_info[i]["Splitted"] = True

            # Hit Each Slot
            self.hit(i)
            self.hit(len(self.cards)-1)

            # for double ace, split and hit at once
            if self.cards[i] == 1:
                self.hit(i)
                self.slot_info[i]["Hit"] = False
                
                last_index = len(self.card) - 1
                self.hit(last_index)
                self.slot_info[last_index]["Hit"] = False

                self.slot_info[i]["Doubled"] = self.slot_info[last_index]["Doubled"] = self.slot_info[last_index]["Splitted"] = True

    
    def double(self, i = 0):
        if self.bank_roll >= self.bets[i] and self.slot_info[i]["Doubled"] == False:
            self.slot_info[i]["Doubled"] = True
            self.bank_roll -= self.bets[i]
            self.bets[i] *= 2

            self.hit(i)
    
    def Payoff(self, dealer_points):
        TotalLost = 0
        for i in range(len(self.cards)):
            has_ace = False
            Lost = -1
            point = 0
            soft = False
            for card in self.cards[i]:
                point, soft = CalculatePoint(self.cards[i])

            if point <= 21 and (dealer_points > 21 or point > dealer_points):
                print("roll:",i,",point:",point, ",dealer:",dealer_points)
                self.bank_roll += 2 * self.bets[i]
                Lost = 1
            elif point > 21:
                print("You bust!! roll:",i,",point:", point, ",dealer:",dealer_points)
            elif dealer_points == point:
                print("roll:",i,",point:", point, ",dealer:",dealer_points)
                self.bank_roll += self.bets[i]
                Lost = 0
            TotalLost += Lost
        total_bet = sum(self.bets)
        self.clear_slots()
        
        return (total_bet, TotalLost)
    
    def decide(self,dealer_clear):
        print("My Cards:",self.cards)
        print("dealer:",dealer_clear)

        i = 0
        while i < len(self.cards):
            looping = True
            while looping == True:
                cmd = input("Your Decision:")
                if cmd == "s":
                    break
                elif cmd == 'h':
                    if False == self.hit(i):
                        looping = False
                elif cmd == 'p':
                    self.split(i)
                elif cmd == "d":
                    self.double(i)
                    looping = False
            i += 1


class Game:
    def __init__(self, deck_count, bank_roll, MAX, MIN):
        # self.players = players
        self.deck = BasicDeck(deck_count)
        self.dealer = Dealer(False, self.deck, False)
        self.bank_roll = bank_roll
        self.max = MAX
        self.min = MIN
        self.dealer = Dealer(False, self.deck)
        self.game_started = False
        self.record = {}
        self.players = []
    
    def CreatePlayers(self, player_count, strategy_list):
        if len(strategy_list) == player_count:
            for i in range(player_count):
                player = Player(self.deck, strategy_list[i])
                player.bank_roll = self.bank_roll
                self.players.append(player)
                self.record[player] = {"Balance":[], "Win": [], "Bet":[]}

    def Clear(self):
        self.deck.shuffle()
        self.game_started = False
        self.record.clear()
        self.players.clear()

    def Run(self, total_rounds):
        self.game_started = True
        rounds = 0
        # Get player numbers
        player_count = int(input("Please input Player Count:"))
                
        # Get player strategies
        strategy_list = []
        for p in range(player_count):
            strategy = input("Please input Strategy File Name:")
            strategy_list.append(strategy if strategy != "" else None)

        # Create Players based on strategies
        self.CreatePlayers(player_count, strategy_list)
        
        while self.game_started == True and rounds < total_rounds:
            # Shuffle
            self.deck.shuffle()
            # Player Bet
            for player in self.players:
                player.bet(self.max, self.min)
            # Deal dealer
            self.dealer.draw_hidden()
            self.dealer.draw_clear()
            dealer_hard_point = self.dealer.clear_card + self.dealer.hidden_card
            dealer_blackjack = dealer_hard_point == 11 and max(self.dealer.clear_card, self.dealer.hidden_card) == 10
            # Deal each player
            bj_players = {}
            for player in self.players:
                result = player.draw_two(dealer_blackjack)
                # Check for blackjack
                if result != False:
                    bets = (result if result > 0 else -result, 0 if result > 0 and dealer_blackjack == True else result/abs(result))
                    #self.record[player]["Bet"].append(result if result > 0 else -result)
                    self.record[player]["Bet"].append(bets[0])
                    self.record[player]["Balance"].append(player.bank_roll)
                    #self.record[player]["Win"].append(0 if result > 0 and dealer_blackjack == True else result/abs(result))
                    self.record[player]["Win"].append([1])
                    bj_players[player] = True
                    print("Your Return:", bets)
                print("Draw2 Result != False:",result != False, ", result:", result)
                
            if dealer_blackjack == False:
                # Inform each player about the clear card and let them make decision
                print("Blackjack List:", bj_players)
                for player in self.players:
                    if bj_players.get(player) == None:
                        result = player.decide(self.dealer.clear_card)
            
                # Dealer's decision
                self.dealer.decision()
                dealer_points = self.dealer.points

                # Player's decision
                for player in self.players:
                    if bj_players.get(player) != None: continue
                    print("Dealer cards: ", self.dealer.hidden_card, self.dealer.clear_card, dealer_points)
                    print("Your cards:",player.cards)
                    bets = player.Payoff(dealer_points)
                    print("Your Return:", bets)
                    if bets != 0:
                        self.record[player]["Bet"].append(bets[0])
                        self.record[player]["Balance"].append(player.bank_roll)
                        self.record[player]["Win"].append(bets[1])
            
            rounds += 1
        
                
                
                    