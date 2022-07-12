class Rect():
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

rectMainSlotResult = Rect((680,654),(736,671))
rectMyMainPoint = Rect((698,679),(722,696))
rectDealerPoint = Rect((554,517),(574,534))
rectInsureBox = Rect((699,442),(726,455))
rectDealCard = Rect((744,554),(762,568))

rectCaptureRegion = Rect((530, 462),(796, 589))

dealerHolePos = (570,483)
dealerHoleColor = (152,152,150)

# Buttons
Double = (636,430)
DoubleColor = (255,93,32)
Split  = (896,452)
SplitColor = (23,111,212)
Stand = (822,421)
StandColor = (255,28,0)
Hit = rectInsureBox.p1
HitColor = (0,194,151)
DealCardWhite = (237,238,240)