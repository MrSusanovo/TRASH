from OLGInfiniteData import *
import cv2
import numpy as np
from PIL import Image, ImageGrab
from CommonTools import *
from math import ceil
import os
from time import sleep

greenTimerColorHSV = RGB2HSV(greenTimerColor)
yellowTimerColorHSV = RGB2HSV(yellowTimerColor)
CentralYellowHSV = RGB2HSV(CentralYellow)

class CardCounter:
    def __init__(self, onnx_file, deck):
        self.net = cv2.dnn.readNetFromONNX('last.onnx')
        self.deck = deck
        self.Reset()

        self.buffer_card = 0
        self.frame_count = 0
        self.is_gray = True
    
    def Reset(self):
        self.total_cards = deck * 52
        self.running_count = 9
        self.ClearBuffer()

    def GetBet(self, bankroll):
        true_count = self.running_count/self.total_cards
        if true_count < 1:
            return 1
        my_edge = (true_count - 1) * 0.005
        approx_payout = my_edge / 0.42
        return int(bankroll * my_edge / approx_payout)
    
    def Detect(self, frame):
        return None
    
    def GetTCount(self):
        return self.running_count/self.total_cards
    
    def Count(self, card):
        if card >= 10 and card <= 13 or (card == 1):
            self.running_count -= 1
        elif card <= 6 and card >= 2:
            self.running_count += 1
        self.total_cards -= 1
    
    def ClearBuffer(self):
        self.buffer_card = 0
        self.frame_count = 0
        self.is_gray = True
    
        
    

class AutoPlay:
    def __init__(self, balance):
        self.state = 0
        self.dimScreen = ImageGrab.grab()
        # convert coordinate from mouse to screen
        # cnn for card detection.
        self.net = cv2.dnn.readNet('last.onnx')
        self.cardCounter = None
        self.actions = []

        # Betting releated
        self.last_bet = 0
        self.bet_deviation = 0
        self.balance = balance

        # Cards related
        self.dealer_cards = []
        self.dealer_point = 0
        self.my_cards = []
        self.slot1 = []
        self.slot2 = []
        self.my_point = 0
        self.bj_checker = [0,0]

    # Init State machine actions
    def InitStateMachine(self):
        self.state = 0 
        self.actions = [self.State0, self.State1, self.State2, self.State3, self.State4, self.State5, self.State6, self.State7]
    # Color comparison
    def colorCompare(c1, c2, t, ERR):
        if t == 'rgb':
            return np.sqrt(sum((sample_color - color)**2)) < ERR
        else:
            return abs(c1[t]-c2[t]) < ERR
    
    # input color should be np array for rgb, normal tuple for hsv
    def pixelPollerWIN32(self, coord, color, t, ERR = 40):
        sample_color = np.array(getColorWIN32(coord)) if t == 'rgb' else RGB2HSV(getColorWIN32(coord))
        # different type of comparison
        return colorCompare(sample_color,color, t, ERR)
    
    def pixelPoller(self, coord, color, t, ERR=40, src = None):
        sample_color = np.array(getColor(coord,src)) if t == 'rgb' else RGB2HSV(getColor(coord))
        # different type of comparison
        return colorCompare(sample_color,color, t, ERR)
    
    def MakeBet(self, Amount):
        counter = Amount
        button = Bet1
        chip = 1
        while counter > 0:
            if counter >= 100:
                chip = 100
                button = Bet100
            elif counter >= 25:
                chip = 25
                button = Bet25
            elif counter >= 5:
                chip = 5
                button = Bet5
            else:
                chip = 1
                button = Bet1
            chip_count = int(counter/chip)
            for i in range(chip_count):
                click(button)
                sleep(0.015)
            counter -= chip_count * chip
        

    def State0(self):
        while True:
            # Copare color with win32 api, compare by hue, with error = 10 degree.
            if pixelPollerWIN32(greenTimerPos, greenTimerColorHSV, 0 ,5):
                self.state = 1
                break
    def State1(self):
        # Read in new balance.
        balance = int(getText(rectBalance.p1, rectBalance.p2,'-c tessedit_char_whitelist=0123456789 --psm 6')[:-1])
        # determine wether to update balance or not
        if abs(balance - self.balance) < self.bet_deviation:
            self.balance = balance
            self.bet_deviation = 0
        # Make bet
        self.last_bet = self.CardCounter.GetBet(self.balance)
        self.bet_deviation += self.last_bet
        self.MakeBet(self.last_bet)
        # Loop
        while True:
        # check for yellow card, if saw, reset card count, remake bet
            if pixelPollerWIN32(CentralPoint, CentralYellowHSV, 0, 5):
                self.CardCounter.Reset()
                self.bet_deviation -= self.last_bet
                self.last_bet = self.CardCounter.GetBet(self.balance)
                self.bet_deviation += self.last_bet
                self.MakeBet(self.last_bet)
            # check for yellow timer, if saw go to state 2
            if pixelPollerWIN32(yellowTimerPos, yellowTimerColorHSV, 0, 5):
                self.state = 2
                break

    def State2(self):
        # Count Cards and detect dealer card in a loop
        while True:
            # check if I got 2 cards and dealer got 1 card
            if len(self.my_cards) == 2 and len(self.dealer_cards == 1):
                # if I got blackjack, go to state 7 
                if self.my_point == 21:
                    self.state = 7
                    self.bet_deviation += 0.5 * self.last_bet
                    break
                # if dealer got ace but I didn't get blackjack, goto insurance state
                if self.dealer_point == 11:
                    self.state = 3
                    break
                # otherwise go to state 4
                self.state = 4
                break
            
            img = ImageGrab.grab()
            
            # Count card and calculate my point by yolo
            if len(self.my_cards) < 2:
                yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
                yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
                # yolo to get my card, returns none unless a card is confirmed, detect should count card
                new_card = self.CardCounter.Detect(yolo_frame)
                if new_card != None:
                    self.my_cards.append(new_card)
                    self.is_soft,self.my_point = CalculatePoints(self.my_cards)
                '''
                new_card = self.CardCounter.Detect(yolo_frame)
                if new_card == self.buff_card:
                    self.my_cards.append(new_card)
                    self.my_point = self.CalculatePoints(self.my_cards)
                    self.CardCounter.count(new_card)
                elif new_card == None:
                    self.buff_card = 0 if pixelPoller(CentralPoint, CentralWhite, 'rgb', 30, img) == False else self.buff_card
                elif self.buff_card == 0:
                    self.buff_card = 0 if new_card == None else new_card
                    '''
            
            # Get dealer's upcard
            if self.dealer_point == 0 and pixelPoller(dealerUpPos, dealerUpColor, 'rgb', 30, img):
                rect = screenToImgRect(rectDealerPoint.p1,rectDealerPoint.p2,img)
                text_img = img.crop(rect)
                text = getText(text_img,'-c tessedit_char_whitelist=0123456789 --psm 6')
                # manually correct the problem with dealer Ace
                new_point = int(text[:-1]) if len(text) > 0 else 0
                new_point = 11 if new_point = 0 or new_point == 1 else new_point
                self.dealer_point = new_point
                self.dealer_cards.append(new_point)
                # count dealer's card
                self.CardCounter.Count(new_point)


            # check if I got blackjack, state to 7
            # check if dealer got ace, or I got 2 cards but still can't get dealer's card check if insurance option provided, go to state 3 and break
            # if so change state 
            # else keep polling until we got 2 cards and dealer got 1, change state to 4
    def State3(self):
        # take insurance on TC 3+
        if self.cardCounter.getTCount() >= 3:
            click(Hit)
            self.bet_deviation += ceil(0.5 * self.last_bet)
        self.state = 4

    def State4(self):
        # need to get the memory from state 2
        while True:
            # make decision
            TC = self.CardCounter.getTCount()
            decision = Decide(self.my_cards, TC, self.my_point, self.dealer_point, self.is_soft)
            if decision == 's':
                # stand go to 5
                click(Stand)
                self.state = 5
                break
            elif decision == 'p':
                click(Split)
                self.bet_deviation += self.last_bet
                if self.my_cards[0] == 11 or self.my_cards[1] == 1:
                    self.state = 5
                    break
                self.slot1.append(self.my_cards[0])
                self.slot2.append(self.my_cards[1])
                self.my_cards.clear()
                self.state = 6
                break
            elif decision == 'd':
                click(Double)
                self.bet_deviation += self.last_bet
                self.state = 5
                break
            elif decision == 'b':
                # busted
                self.state = 5
                break
            else: # by default, hit
                # six card charlie
                if len(self.my_cards) == 6:
                    self.state = 7
                    break
                click(Hit)
                img = ImageGrab.grab()
                # Count card and calculate my point by yolo
                yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
                yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
                # yolo to get my card, returns none unless a card is confirmed, detect should count card
                new_card = self.CardCounter.Detect(yolo_frame)
                if new_card != None:
                    self.my_cards.append(new_card)
                    self.is_soft, self.my_point = CalculatePoints(self.my_cards)

        # split go to 6
        # count 
        # bust, double split on ace  go to 5
    def State5(self):
        while True:
            # keep count cards
            img = ImageGrab.grab()
            # Count card
            if len(self.my_cards) < 2:
                yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
                yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
                # yolo to get my card, returns none unless a card is confirmed, detect should count card
                self.CardCounter.Detect(yolo_frame)
            # pixel check if dealer flipped
            if False == pixelPoller(dealerHolePos,dealerHoleColor,'rgb', 30, img):
                # flipped go to 7
                self.CardCounter.ClearBuffer()
                self.state = 7
                break
        
    
    def State6(self):
        # need to get the memory from state 4
        # wait for my new card
        slot_index = 0
        slot = self.slot1
        while True:
            img = ImageGrab.grab()
            yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
            yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
            new_card = self.CardCounter.Detect(yolo_frame)
            if new_card != None:
                slot.append(new_card)
                if slot_index == 0:
                    slot = self.slot2
                    slot_index = 1
                    continue
                break
        
        slot_index = 0
        slot = self.slot1
        while True:
            is_soft, points = CalculatePoints(slot)
            TC = self.CardCounter.getTCount()
            # Can't split anymore
            decision = Decide(slot, TC, self.my_point, self.dealer_point,self.is_soft, False)
            if decision == 's':
                # stand go to 5
                click(Stand)
                # if finished with second slot, go to state 5
                if slot_index == 1:
                    self.state = 5
                    break
                slot_index = 1
                slot = self.slot2
            elif decision == 'b':
                # busted
                if slot_index == 1:
                    self.state = 5
                    break
                slot_index = 1
                slot = self.slot2
            else: # by default, hit, double and split are not allowed
                if len(slot) == 6:
                    if slot_index == 1:
                        self.state = 5
                        break
                    slot_index = 1
                    slot = self.slot2
                img = ImageGrab.grab()
                # Count card and calculate my point by yolo
                yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
                yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
                # yolo to get my card, returns none unless a card is confirmed, detect should count card
                new_card = self.CardCounter.Detect(yolo_frame)
                if new_card != None:
                    slot.append(new_card)

            
        # count cards
        # make dicision
        # 2 slots with any of stand, double, bust go to 5
    
    def State7(self):
        while True:
            img = ImageGrab.grab()
            # crop the text part 
            rect = screenToImgRect(rectDealerPoint.p1,rectDealerPoint.p2,img)
            text_img = img.crop(rect)
            # count dealer cards
            text = getText(text_img,'-c tessedit_char_whitelist=0123456789 --psm 6')
            new_point = int(text[:-1]) if len(text) > 0 else 0
            if new_point != self.dealer_point and new_point != 0 and new_point != 1:
                new_card = ((new_point - self.dealer_point) + 10) % 10
                self.dealer_cards.append(new_card)
                self.CardCounter.Count(new_card)
                self.dealer_point = new_point
            # pixel check yellow end of deck card
            if pixelPoller(CentralPoint, CentralYellowHSV, 0, 5, img):
                self.CardCounter.Reset()
            # pixel check green timer and go to state 1
            if pixelPoller(greenTimerPos, greenTimerColorHSV, 0, 5, img):
                self.state = 1
                self.dealer_point = 0
                self.dealer_cards.clear()
                self.my_cards.cleaer()
                self.slot1.clear()
                self.slot2.clear()
                self.my_point = 0
                self.is_soft = False
                break
    def Play(self):
        while True:
            self.actions[self.state]()