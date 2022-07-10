import numpy as np
import cv2
from PIL import ImageGrab, Image
from pytesseract import pytesseract
from time import sleep
from CommonTools import *
from OneTouch21Data import *

def didWin(pt = result):
    color = getColor(pt)
    color_array = np.array(color)
    least_error = None
    least_index = None
    for i in range(len(colors)):
        err = sum((color_array - colors[i])**2)
        if least_error == None or err < least_error:
            least_error = err
            least_index = i
    return least_index - 1

def getMyPoint(BW=False):
    text = getText(my_up,my_down,tconfig, False, BW)
    is_soft = len(text) > 1 and text[1] == '/'
    print("You Got text:", text)
    if text == '10/2\n' and BW == False:
        return (20, True)
    x = re.findall("[0-9]+", text)
    lst = []
    for i in x:
        try:
            lst.append(int(i))
        except:
            continue

    if len(lst) == 2 and lst[len(x)-1] - lst[0] == 10 or len(x) == 1:
        return (lst.pop(),is_soft)
    
    return None

def getDealerPoint(BW=False):
    text = getText(deal_up,deal_down,tconfig, True, BW)
    print("Dealer Got text:", text)
    # special case for 1/11
    if text == '1/17\n':
        return 11
    x = re.findall("[0-9]+", text)
    lst = []
    for i in x:
        try:
            lst.append(int(i))
        except:
            continue

    if len(lst) == 2:
        diff = lst[len(x)-1] - lst[0]
        if diff>=10 and diff <= 16:
            return lst.pop()
    elif len(x) == 1:
        return lst[0]
    
    return None

def CanSplit():
    current_color = np.array(getColor(split))
    err  = sum((current_color - bcolor_array)**2)
    print(err)
    return err < 20

def CanDouble():
    current_color = np.array(getColor(double))
    err = sum((current_color - dcolor_array)**2)
    return err < 20


def Play(unit):
    round_finished = False
    first_round = True
    double_factor = 1
    # bet 
    click(double)
    sleep(0.05)
    print("About to bet:", unit, "confirm?")
    sleep(1)
    #input()
    click(chip1)
    for i in range(unit):
        click(slot1)
        sleep(0.17)
    sleep(0.45)
    click(deal)
    sleep(1.5)
    color = np.array(getColor(insure_no))
    if sum((color-no_red)**2) < 20:
        click(insure_no)
        click(insure_no)
    sleep(1.5)

    # get dealer value
    dealer_point1 = getDealerPoint()
    dealer_point2 = getDealerPoint(True)
    dealer_point = dealer_point1  if dealer_point1 != None and dealer_point1 <= 11 and dealer_point1 >= 2 else dealer_point2

    sleep(0.5)
    # Check dealer blackjack
    dealer_win = didWin(dealer_result)
    if dealer_win == 1:
        round_finished = True
        i_win = didWin()
        if i_win == 0:
            print("both blackjack, returning...")
        else:
            print("dealer blackjack!, returning...")
        return i_win * double_factor

    while round_finished == False:
        
        # remember to check blackjack
        if first_round:
            sleep(0.5)
        else:
            sleep(1)
        first_round = False
        win = didWin()
        print("Did I win?",win)
        if win == 1:
            print("I won!")
            break
        elif win == -1:
            print("I lost!")
            break
        
        my_point1 = getMyPoint()
        my_point2 = getMyPoint(True)
        my_point = my_point1[0] if (my_point1 != None) and (my_point1[0] <= 30) and (my_point1[0] >=2) else my_point2
        # my_point = None if my_point != None and my_point >= 30 else my_point
        print("your point:",my_point,"dealer:",dealer_point)
        if my_point == None or (type(my_point) == type((1,1)) and my_point[0] % 100 > 26):
            raise Exception("I am a dumb ass, I got an error")
        my_soft = my_point[1] if type(my_point) == type((1,1)) else my_point1[1]
        my_point = my_point[0] if type(my_point) == type((1,1)) else my_point
        my_point %= 100
        # hit if no split, no double
        if CanSplit() == False:
            button = None
            if CanDouble() and unit < 8 and my_point == 11:
                button = double
                double_factor *= 2
                print("about to doublw down, confirm?")
            elif CanDouble() and unit < 8 and (dealer_point != None and ((my_soft == True and (SoftDouble.get(my_point) != None and dealer_point in SoftDouble[my_point])))):
                button = double
                double_factor *= 2
                print("about to doublw down, confirm?")
            elif CanDouble() and unit < 8 and (dealer_point != None and HardDouble.get(my_point) != None and dealer_point in HardDouble[my_point]):
                button = double
                double_factor *= 2
                print("about to doublw down, confirm?")
            elif (my_point <= 11 and my_point >= 2) or (my_soft == True and my_point <= 17):
                button = hit
                print("about to hit, confirm?")
            elif dealer_point != None and ((my_point > 11 and my_point <= 16 and dealer_point >= 7) or (my_point == 12 and (dealer_point == 3 or dealer_point == 2))):
                button = hit
                print("about to hit, confirm?")
            elif (my_point >= 17 and my_point <= 21):
                button = stand
                print("about to stand, confirm?")
            elif dealer_point != None and ((my_point >= 12 and my_point < 17) and (dealer_point >= 2 and dealer_point <=6)):
                button = stand
                print("about to stand, confirm?")
            elif my_point >= 21:
                print("I busted...")
                if first_round == True:
                    raise Exception("Did i really busted?")
                break
            else:
                print("I am a dumb ass! returning")
                raise Exception("I am a dumb ass, I got an error")
        else: # If I can split
            if my_point >= 17 and my_point <= 21:
                print("about to stand, confirm?")
                button = stand
            elif my_point == 10:
                print("about to double, confirm?")
                button = double
            elif my_point < 16 and (dealer_point != None and (dealer_point > 6 or (my_point == 8 and dealer_point < 5))):
                print("about to hit, confirm?")
                button = hit
            elif my_point >= 21:
                print("I busted...")
                break
            else:
                print("I am a dumb ass, returning") 
                raise Exception("I can't handle split")
                break
        
        #answer = input()
        answer = 'y'
        sleep(1)
        if answer == 'y':
            click(button)
            print("sleeping....")
            sleep(1.5)
            # check if number was extracted correctly
            if sum((np.array(getColor(insure_no)) - no_red)**2) < 20:
                click(chip1)
                sleep(0.1)
                click(insure_no)
                sleep(0.1)
                click(stand)
                #raise Exception("something went wrong, was hitting on 17")
                sleep(1.5)
                break
            if button == stand or button == double:
                print("finish my round, breaking after sleep...")
                sleep(1)
                break

    sleep(2)        
    win = didWin()
    print("I won?:", win)
        
    #input("wait for you command")
    sleep(2)
    click(change_bet)
    sleep(0.1)
    click(change_bet)
    return win*double_factor


def OnGoing():
    rounds = 0
    total_win = 0
    lost = 0
    factor = 1
    unit = 1
    win = 0
    while True:
        rounds += 1
        try:
            true_bet = unit*pow(2,lost)*factor
            if true_bet >= 64:
                #winsound.Beep(1250,500)
                winsound.PlaySound("SystemQuestion",winsound.SND_ALIAS)
                answer = input("High stake warning, waiting for your input, proceed or play till win?")
                win = Play(true_bet) if answer == 'p' else 1
            else:
                win = Play(true_bet)
        except Exception as e:
            print(e.args[0])
            #winsound.Beep(1250,500)
            winsound.PlaySound("SystemQuestion",winsound.SND_ALIAS)
            win = int(input("wait for manual, did I win?:"))
        if win >0 or (win < -1 and lost >= 7):
            lost = 0
            factor = 1
        elif win < 0:
            lost += 1
            factor *= -win
        total_win += 1 if win > 0 else 0
        print("Current win rate:",total_win," out of:",rounds," rate:",total_win*1.0/rounds)
