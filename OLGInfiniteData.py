import numpy as np
class Rect():
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

rectMainSlotResult = Rect((680,654),(736,671))
rectMyMainPoint = Rect((698,679),(722,696))
rectDealerPoint = Rect((554,517),(574,534))
rectInsureBox = Rect((699,442),(726,455))
rectDealCard = Rect((744,554),(762,568))
rectSplitPoint1 = Rect((770,678),(795,697))
rectSplitPoint2 = Rect((619,678),(645,697))
rectBalance = Rect((250,742),(295,757))
rectCaptureRegion = Rect((537, 468),(831, 595))
rectValidBoxRegion = Rect((257,105),(285,140))

# Sampling points
dealerHolePos = (570,483)
dealerUpPos = (551,494)
dealerHoleColor = np.array((152,152,150))
dealerUpColor = np.array((242,242,240))
greenTimerPos = (766,306)
greenTimerColor = np.array((0,210,129))
yellowTimerPos = (762,295)
yellowTimerColor = np.array((161,172,14))
CentralPoint = (752,565)
CentralGray = np.array((75,80,86))
CentralWhite = np.array((236,233,232))
CentralYellow = np.array((235,209,40))

# Buttons
Double = (636,430)
DoubleColor = (255,93,32)
Split  = (896,452)
SplitColor = np.array((23,111,212))
Stand = (822,421)
StandColor = (255,28,0)
Hit = rectInsureBox.p1
HitColor = np.array((0,194,151))
ButtonDict = {'d':Double, 's': Stand, 'p': Split, 'h': Hit}
ColorDict = {'d':DoubleColor, 's':StandColor, 'p':SplitColor, 'h':HitColor}
DealCardWhite = np.array((237,238,240))
Bet100 = (792,434)
Bet25 = (730,434)
Bet5 = (695,426)
Bet1 = (670,438)
ChipSlot = (761,678)
BetUndo = (627,435)

# Window Names
OLG_WINDOW = "OLG Live Casino"
