import numpy as np
my_up = (761,649)
my_down = (787,662)
c1up = (742,571)
c1down = (751, 585)
c2up = (731, 577)
c2down = (741, 591)
deal_up = (763, 296)
deal_down = (783,310)

# color constants
red = (227,35,0)
no_red = np.array((243,0,0))
yes_green = (0,169,21)
yellow = (233,166,53)
green = (34, 154, 16)
button_color = (0,53,79)
dcolor_array = np.array((0,58,87))
bcolor_array = np.array(button_color)
colors = [np.array(red),np.array(yellow),np.array(green)]

# buttons
dealer_result = (769,298)
result = (770,651)
second_dec = (769, 693)
chip1 = (618,741)
slot1 = (763,528)
rebet = hit = deal = (1317,714)
rebet2 = split = (1310,618)
clear_bet = change_bet = stand = (1216, 712)
dealer_point = (770,342)
double = (1120,714)
insure_no = (730,536)
insure_yes = (781,534)

# Rules
HardDouble = {9: range(3,7), 10: range(2,10), 11:range(2,12)}
SoftDouble = {13: range(5,7), 14: range(5,7), 15:range(4,7), 16:range(4,7),17:range(3,7),18:range(2,7),19:range(6,7)}