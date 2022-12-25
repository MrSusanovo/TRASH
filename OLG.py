from OLGInfiniteData import *
import cv2
import numpy as np
from PIL import Image, ImageGrab
from CommonTools import *
from math import ceil
import os
from time import sleep
from Predict import post_process_mask, inference, net

greenTimerColorHSV = RGB2HSV(greenTimerColor)
yellowTimerColorHSV = RGB2HSV(yellowTimerColor)
CentralYellowHSV = RGB2HSV(CentralYellow)
HiLo = 0
AO2 = 2

class CardCounter:
    def __init__(self, onnx_file, deck, strategy = HiLo):
        #self.net = cv2.dnn.readNetFromONNX(onnx_file)
        self.deck = deck
        self.strategy = strategy
        self.Reset()

        self.buffer_card = 0
        self.frame_count = 0
        self.is_gray = True
    
    def Reset(self):
        self.total_cards = self.deck * 52
        self.running_count = 0
        self.Ace = self.deck * 4
        self.ClearBuffer()

    def GetBet(self, bankroll):
        # Bet no more than 4 TC
        true_count = min(4,self.GetBetCount())
        if true_count < 1:
            return 1
        my_edge = (true_count - 1) * 0.005 + 0.5
        approx_payout = my_edge / 0.42
        return max(1, int(bankroll * (0.42 - 0.5 / approx_payout)))
    
    # A card is confirmed and returned when it appears more than once and finally disappeared.
    def Detect(self, frame):
        # check if it's gray
        sample_color = np.array(getColorWIN32(CentralPoint))
        self.is_gray = colorCompare(sample_color,CentralGray, 'rgb', 40)
        
        # If gray, clear existing cards and return that to upper level.
        if self.is_gray:
            if self.buffer_card != 0 and self.frame_count > 1:
                print("Buff card:",self.buffer_card,"frame count:",self.frame_count)
                confirmed = self.buffer_card
                self.Count(confirmed)
                self.ClearBuffer()
                #print("confirmed:", confirmed)
                return confirmed
            self.buffer_card = self.frame_count = 0
            return None
        
        print("Card counter Detect: is gray:", self.is_gray)

        # If it's not gray, do yolo detection.
        #print('Detect:', frame.shape)
        boxes,classes = post_process_mask(frame.copy(),inference(frame, net))
        index = 0
        for box in boxes:
            x0 = box[0]
            y0 = box[1]
            x1 = box[0] + box[2]
            y1 = box[1] + box[3]
            # if box is in the region, record the card and count it.
            if x0 >= rectValidBoxRegion.p1[0] and x1 <= rectValidBoxRegion.p2[0] and y0 >= rectValidBoxRegion.p1[1] and y1 <= rectValidBoxRegion.p2[1]:
                card = int(classes[index])
                print("Card counter Detect: got card:", card, "Buffer:",self.buffer_card,"frame_count:",self.frame_count)
                card = 10 if card > 10 else card
                if self.buffer_card == 0:
                    self.buffer_card = card
                    self.frame_count = 1
                elif self.buffer_card == card:
                    self.frame_count += 1
                else:
                    if self.frame_count > 1 and self.buffer_card > 0:
                        confirmed = self.buffer_card
                        self.buffer_card = card
                        self.frame_count = 1
                        self.Count(confirmed)
                        return confirmed
                return None
            index += 1
        # if no card detected but cards recorded on file, count and return that
        print("No Card Detected: buffer_card:", self.buffer_card,"frame_count:",self.frame_count)
        if self.buffer_card != 0 and self.frame_count > 1:
            confirmed = self.buffer_card
            self.ClearBuffer()
            self.Count(confirmed)
            return confirmed

        self.ClearBuffer()
        return None
    
    def GetTCount(self):
        return self.running_count/(self.total_cards/52)
    
    def GetBetCount(self):
        if self.strategy == AO2:
            ace_surplus = self.Ace - 4*self.total_cards/52
            ace_surplus = ace_surplus if self.strategy == HiLo else 2*ace_surplus
            bet_running_count = self.running_count + ace_surplus
            return bet_running_count/(self.total_cards/52)
        else:
            return GetTCount()
    
    def Count(self, card):
        if self.strategy == HiLo:
            if card >= 10 and card <= 13 or (card == 1):
                self.running_count -= 1
            elif card <= 6 and card >= 2:
                self.running_count += 1
        elif self.strategy == AO2:
            if card >= 4 and card <= 6:
                self.running_count += 2
            elif card == 2 or card == 3 or card == 7:
                self.running_count += 1
            elif card == 9:
                self.running_count -= 1
            elif card >= 10 and card <= 13:
                self.running_count -= 2
            elif card == 1:
                self.Ace -= 1
        self.total_cards -= 1 if card != None else 0
        print("Count card:", card, "Running Count:", self.running_count, "Cards Left:", self.total_cards)
    
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
        self.cardCounter = CardCounter('best_4000.onnx',8)
        self.actions = []

        # Betting releated
        self.last_bet = 0
        self.bet_deviation = 0
        self.balance = balance
        self.BettingPortion = balance

        # Cards related
        self.dealer_cards = []
        self.dealer_point = 0
        self.my_cards = []
        self.slot1 = []
        self.slot2 = []
        self.my_point = 0
        self.bj_checker = [0,0]

        # Init Windows
        self.window = win32gui.GetForegroundWindow()
        # Init the game
        self.InitStateMachine()

    # Init State machine actions
    def InitStateMachine(self):
        self.state = 0 
        self.actions = [self.State0, self.State1, self.State2, self.State3, self.State4, self.State5, self.State6, self.State7]
    
    
    # input color should be np array for rgb, normal tuple for hsv
    def pixelPollerWIN32(self, coord, color, t, ERR = 40):
        sample_color = np.array(getColorWIN32(coord)) if t == 'rgb' else RGB2HSV(getColorWIN32(coord))
        # different type of comparison
        return colorCompare(sample_color,color, t, ERR)
    
    def pixelPoller(self, coord, color, t, ERR=40, src = None):
        sample_color = np.array(getColor(coord,src)) if t == 'rgb' else RGB2HSV(getColor(coord))
        # different type of comparison
        return colorCompare(sample_color,color, t, ERR)
    
    def ResetBet(self,clicks):
        for i in range(clicks):
            click(BetUndo)
            sleep(0.015)


    def MakeBet(self, Amount):
        counter = Amount
        button = Bet1
        chip = 1
        print("MakeBet:", Amount)
        clicks = 0
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
                click(ChipSlot)
                clicks+=1
            counter -= chip_count * chip
        sleep(0.01)
        win32gui.SetForegroundWindow(self.window)
        return clicks
        

    def State0(self):
        while True:
            # Compare color using win32 api, compare by hue, with error = 10 degree.
            if self.pixelPollerWIN32(greenTimerPos, greenTimerColorHSV, 0 ,5):
                print("Saw Green, switch state to 1")
                self.state = 1
                break
    def State1(self):
        # Read in new balance.
        balance_text = getText(rectBalance.p1, rectBalance.p2,'-c tessedit_char_whitelist=0123456789., --psm 6')[:-1].replace(',','')
        balance = float(balance_text)
        print("Got Balance:", balance)
        # determine wether to update balance or not
        if abs(balance - self.balance) < self.bet_deviation:
            self.balance = balance
            self.bet_deviation = 0
        # Make bet
        self.last_bet = self.cardCounter.GetBet(self.BettingPortion)
        self.bet_deviation += self.last_bet
        clicks = self.MakeBet(self.last_bet)

        # State Changer
        State2Ready = False

        # Flag for Yellow Card
        YellowDetected = False
        # Loop
        while True:
        # check for yellow card, if saw, reset card count, remake bet
            if YellowDetected == False and self.pixelPollerWIN32(CentralPoint, CentralYellowHSV, 0, 3) and self.pixelPollerWIN32(CentralPoint, CentralYellow, 'rgb', 20):
                self.cardCounter.Reset()
                self.bet_deviation -= self.last_bet
                self.last_bet = self.cardCounter.GetBet(self.BettingPortion)
                self.bet_deviation += self.last_bet
                # Reset Bet
                self.ResetBet(clicks)
                self.MakeBet(self.last_bet)
                # mark the flag as true so that it doesn't repeatedly reseting bet
                YellowDetected = True
            # check for yellow timer, if saw go to state 2
            if self.pixelPollerWIN32(yellowTimerPos, yellowTimerColorHSV, 0, 5):
                State2Ready = True
            else:
                if State2Ready:
                    self.state = 2
                    break
    def ReadMyPoint(self,text_img):
        my_text = getTextNoCrop(text_img,tconfig)
        print("READ MY PONIT:",my_text)
        my_text = my_text[:-1] if len(my_text) > 0 else "0"
        new_point = 0
        is_soft = False
        if '/' in my_text:
            new_point = int(my_text[:my_text.find('/')])
        else:
            new_point = int(my_text)
        return new_point
        
    def State2(self):
        TimeStamp = 0
        # Count Cards and detect dealer card in a loop
        while True:
            # check if I got 2 cards and dealer got 1 card
            if len(self.my_cards) == 2 and len(self.dealer_cards) == 1:
                # if dealer got ace but I didn't get blackjack, goto insurance state
                if self.dealer_point == 11 or self.dealer_point == 1:
                    print("State 2: Dealer got Ace. Got to state 3.")
                    self.state = 3
                    break
                # if I got blackjack, go to state 7 
                if self.my_point == 21:
                    print("State 2: I got black jack! Go to state 7.")
                    self.state = 7
                    self.bet_deviation += 0.5 * self.last_bet
                    break
                # otherwise go to state 4
                print("State 2: go to state 4")
                self.state = 4
                break
            
            img = ImageGrab.grab()
            rect = screenToImgRect(rectMyMainPoint.p1,rectMyMainPoint.p2,img)
            text_img = img.crop(rect)
            # check if I missed cards
            if self.pixelPoller(Hit,HitColor,'rgb',20,img):
                if TimeStamp == 0:
                    TimeStamp = time.time()
                elif time.time() - TimeStamp > 2:
                    print("MISSED CARD!")
                    text_point = self.ReadMyPoint(text_img)
                    # trouble shoot to get my other card
                    if len(self.my_cards) == 1 and new_point > self.my_cards[0]:
                        self.my_cards.append(new_point-self.my_cards[0])
                        print("RECOVER: my_card:", self.my_cards)

                    

            # Count card and calculate my point by yolo
            if len(self.my_cards) < 2:
                yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
                yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
                # yolo to get my card, returns none unless a card is confirmed, detect should count card
                new_card = None
                try:
                    new_card = self.cardCounter.Detect(yolo_frame)
                except Exception as e:
                    cv2.imwrite('bugpic.png',yolo_frame)
                    raise e
                if new_card != None:
                    print("State 2: Got card:", new_card)
                    self.my_cards.append(new_card)
                    self.is_soft,self.my_point = CalculatePoints(self.my_cards)
                    text_point = self.ReadMyPoint(text_img)
                    if text_point != self.my_point:
                        print("ERROR: my_point:",self.my_point,", text_point:",text_point)
                '''
                new_card = self.cardCounter.Detect(yolo_frame)
                if new_card == self.buff_card:
                    self.my_cards.append(new_card)
                    self.my_point = self.CalculatePoints(self.my_cards)
                    self.cardCounter.Count(new_card)
                elif new_card == None:
                    self.buff_card = 0 if pixelPoller(CentralPoint, CentralWhite, 'rgb', 30, img) == False else self.buff_card
                elif self.buff_card == 0:
                    self.buff_card = 0 if new_card == None else new_card
                    '''
            
            # Get dealer's upcard
            if self.dealer_point == 0 and self.pixelPoller(dealerUpPos, dealerUpColor, 'rgb', 30, img):
                rect = screenToImgRect(rectDealerPoint.p1,rectDealerPoint.p2,img)
                text_img = img.crop(rect)
                text = getTextNoCrop(text_img,'-c tessedit_char_whitelist=0123456789 --psm 6')
                # manually correct the problem with dealer Ace
                new_point = int(text[:-1]) if len(text) > 0 else 0
                new_point = 11 if new_point == 0 or new_point == 1 else new_point
                print("State 2: got dealer upcard:", text)
                self.dealer_point = new_point
                self.dealer_cards.append(new_point)
                # count dealer's card
                self.cardCounter.Count(new_point)


            # check if I got blackjack, state to 7
            # check if dealer got ace, or I got 2 cards but still can't get dealer's card check if insurance option provided, go to state 3 and break
            # if so change state 
            # else keep polling until we got 2 cards and dealer got 1, change state to 4
    def State3(self):
        # take insurance on TC 3+
        tc = self.cardCounter.GetTCount()
        if tc >= 3:
            print("State 3: tc:", tc,", take insurance")
            self.ClickButton('h')
            self.bet_deviation += ceil(0.5 * self.last_bet)
        else:
            print("State 3: tc:", tc,", don't take insurance")
            self.ClickButton('s')
        print("State 3: go to state 4")
        self.state = 4

    def State4(self):
        # need to get the memory from state 2
        button = None
        while True:
            # make decision
            TC = self.cardCounter.GetTCount()
            decision = Decide(self.my_cards, TC, self.my_point, self.dealer_point, self.is_soft)
            print("State 4: Decision:",decision)
            if decision == 's':
                # stand go to 5
                self.state = 5
                if self.my_point == 21:
                    break
            elif decision == 'p':
                self.bet_deviation += self.last_bet
                if self.my_cards[0] == 11 or self.my_cards[1] == 1:
                    self.ClickButton(decision)
                    self.state = 5
                    break
                self.slot1.append(self.my_cards[0])
                self.slot2.append(self.my_cards[1])
                self.my_cards.clear()
                self.state = 6
            elif decision == 'd':
                self.bet_deviation += self.last_bet
                self.state = 5
            elif decision == 'b':
                # busted
                self.state = 5
                break
            else: # by default, hit
                # six card charlie
                if len(self.my_cards) == 6:
                    self.state = 7
                    break
                
            self.ClickButton(decision)
            if decision != 'h':
                break
            # Only hit will hit this part.
            while decision == 'h':
                img = ImageGrab.grab()
                # Count card and calculate my point by yolo
                yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
                yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
                # yolo to get my card, returns none unless a card is confirmed, detect should count card
                new_card = None
                try:
                    new_card = self.cardCounter.Detect(yolo_frame)
                except Exception as e:
                    cv2.imwrite('bugpic.png',yolo_frame)
                    raise e
                #new_card = self.cardCounter.Detect(yolo_frame)
                if new_card != None:
                    self.my_cards.append(new_card)
                    print("State 4: yolo got card:", new_card, "My cards:", self.my_cards) 
                    self.is_soft, self.my_point = CalculatePoints(self.my_cards)
                    break
        print("State 4: go to state:", self.state)
        # split go to 6
        # count 
        # bust, double split on ace  go to 5
    def State5(self):
        Init = False
        while True:
            # keep count cards
            img = ImageGrab.grab()
            
            yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
            yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
            # yolo to get my card, returns none unless a card is confirmed, detect should count card
            
            try:
                new_card = self.cardCounter.Detect(yolo_frame)
            except Exception as e:
                cv2.imwrite('bugpic.png',yolo_frame)
                raise e
            #self.cardCounter.Detect(yolo_frame)

            if False == self.pixelPollerWIN32(dealerHolePos,dealerHoleColor,'rgb', 30) and Init == True:
                print(getColorWIN32(dealerHolePos), dealerHoleColor)
                # flipped go to 7
                print("State 5: dealer flipped card, goto state 7")
                self.cardCounter.ClearBuffer()
                self.state = 7
                break
            elif Init == False and True == self.pixelPollerWIN32(dealerHolePos, dealerHoleColor, 'rgb', 30):
                Init = True
            
            '''
            # Count card
            if len(self.my_cards) < 2:
                yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
                yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
                # yolo to get my card, returns none unless a card is confirmed, detect should count card
                self.cardCounter.Detect(yolo_frame)
            # pixel check if dealer flipped
            if False ==self.pixelPoller(dealerHolePos,dealerHoleColor,'rgb', 30, img):
                # flipped go to 7
                self.cardCounter.ClearBuffer()
                self.state = 7
                break
                '''
        
    
    def State6(self):
        # need to get the memory from state 4
        # wait for my new card
        slot_index = 0
        slot = self.slot1
        while True:
            img = ImageGrab.grab()
            yolo_rect = screenToImgRect(rectCaptureRegion.p1, rectCaptureRegion.p2, img)
            yolo_frame = cv2.cvtColor(np.array(img.crop(yolo_rect)),cv2.COLOR_BGR2RGB)
            try:
                new_card = self.cardCounter.Detect(yolo_frame)
            except Exception as e:
                cv2.imwrite('bugpic.png',yolo_frame)
                raise e
            #new_card = self.cardCounter.Detect(yolo_frame)
            if new_card != None:
                slot.append(new_card)
                # make decision
                is_soft, points = CalculatePoints(slot)
                TC = self.cardCounter.GetTCount()
                decision = Decide(slot, TC, pints, self.dealer_point, is_soft, False)
                # Click the button
                self.ClickButton(decision)
                # For non-hit and six card charlie, switch slot or change state.
                if decision != 'h' or (decision == 'h' and len(slot) == 6) or (poitns == 21):
                    if slot_index == 1:
                        self.state = 5
                        break
                    slot_index = 1
                    slot = self.slot2
            
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
            text = getTextNoCrop(text_img,'-c tessedit_char_whitelist=0123456789 --psm 6')
            new_point = int(text[:-1]) if len(text) > 0 else 0
            if new_point != self.dealer_point and new_point != 0 and new_point != 1:
                new_card = ((new_point - self.dealer_point) + 10) % 10
                new_card += 10 if new_card == 0 else 0
                print("State 7: dealer got card:", new_card)
                self.dealer_cards.append(new_card)
                self.cardCounter.Count(new_card)
                self.dealer_point = new_point
            # pixel check yellow end of deck card
            if self.pixelPoller(CentralPoint, CentralYellowHSV, 0, 3, img) and self.pixelPoller(CentralPoint, CentralYellow, 'rgb', 20, img):
                print("State 7: saw yellow card, reset card counter")
                self.cardCounter.Reset()
            # pixel check green timer and go to state 1
            if self.pixelPoller(greenTimerPos, greenTimerColorHSV, 0, 5, img):
                print("State 7: saw green timer, goto state 1")
                self.state = 1
                self.dealer_point = 0
                self.dealer_cards.clear()
                self.my_cards.clear()
                self.slot1.clear()
                self.slot2.clear()
                self.my_point = 0
                self.is_soft = False
                break
    def ClickButton(self,decision):
        # Skipt for busted
        if decision == 'b':
            return False
        # Poll until the button appears
        while self.pixelPollerWIN32(ButtonDict[decision], ColorDict[decision], 'rgb' , 20) == False:
            continue
        print("Click:", decision)
        click(ButtonDict[decision])
        sleep(0.01)
        win32gui.SetForegroundWindow(self.window)
        while self.pixelPollerWIN32(ButtonDict[decision], ColorDict[decision], 'rgb', 20) == True:
            continue

        
    def Play(self):
        while True:
            self.actions[self.state]()