# specific to olg, hilo strategy. no double after split
def Decide(cards, true_count, points, dealer_up, is_soft, can_split = True):
    if points > 21:
        return 'b'
    # check for split and double first
    if can_split and len(cards) == 2:
        # split
        if cards[0] == cards[1]:
            card = cards[0]
            if (card == 2 or card ==3) and ((dealer_up <= 7 and dealer_up >= 4 )or (dealer_up == 1)):
                return 'p'
            if card == 4 and true_count >= 2:
                return 'd'
            if card == 5 and ((dealer_up >= 2 and dealer_up <= 9) or true_count >= 4):
                return 'd'
            if card == 6:
                if dealer_up >= 3 and dealer_up <=6:
                    return 'p'
                if dealer_up == 2 and true_count >= 3:
                    return 's'
            if card == 7 and dealer_up <= 7 and dealer_up >= 2:
                return 'p'
            if card == 8 or card == 1 or card == 11:
                return 'p'
            if card == 9 and ((dealer_up >= 2 and dealer_up <= 6) or (dealer_up >=8 and dealer_up <= 9)):
                return 'p'
            if card == 10 and (dealer_up >= 4 and dealer_up <= 6):
                if true_count >= 6:
                    return 'p'
                if true_count >= 5 and dealer_up >= 5:
                    return 'p'
                if true_count == 4 and dealer_up == 6:
                    return 'p'
            if card == 1 or card == 11:
                return 'p'
        else:
            if points == 8 and true_count >= 2:
                return 'd'
            if points == 9:
                if dealer_up >= 2 and dealer_up <= 7:
                    if true_count >= 3:
                        return 'd'
                    if true_count >= 1 and dealer_up <= 6:
                        return 'd'
                    if dealer_up >= 3 and dealer_up <= 6:
                        return 'd'
            if points == 10:
                if true_count >= 4:
                    return 'd'
                if dealer_up >= 2 and dealer_up <= 9:
                    return 'd'
            if points == 11:
                if true_count >= 1:
                    return 'd'
                if dealer_up >= 2 and dealer_up <= 10:
                    return 'd'
            if is_soft:
                if dealer_up == 5 or dealer_up == 6:
                    if true_count >= 1 and points <= 20:
                        return 'd'
                    if points <= 17:
                        return 'd'
                if dealer_up == 4 and points >= 15 and points <= 19:
                    if true_count >= 3:
                        return 'd'
                    if points <= 18:
                        return 'd'
                if dealer_up >= 2 and dealer_up <= 3 and points >= 17 and points <= 18:
                    if true_count >= 1:
                        return 'd'
                    if points != 17 or dealer_up != 2:
                        return 'd'
                        '''
                if points >= 19:
                    return 's'
                if points == 18 and dealer_up == 7 or dealer_up == 8:
                    return 's'
                    '''
    # rest we only handle stand, default is hit
    if is_soft:
        if points >= 19 or (points >= 18 and dealer_up >= 2 and dealer_up <=8) :
            return 's'
    else:
        if points >= 17:
            return 's'
        if points >= 12 and dealer_up >= 2 and dealer_up <= 6:
            if not (points == 12 and ((dealer_up == 4 and true_count < 0) or (dealer_up == 3 and true_count < 2) or (dealer_up == 2 and true_count < 3))) and not (points == 13 and true_count < -1 and dealer_up == 2):
                return 's'
        if points == 16:
            if true_count >= 4 and dealer_up == 9:
                return 's'
            if true_count > 0 and dealer_up == 10:
                return 's'
        if points == 15 and dealer_up == 10 and true_count >= 4:
            return 's'
    return 'h'
