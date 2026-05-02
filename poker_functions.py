# -*- coding: utf-8 -*-
"""
Functions used in Poker Training Program

Created on Mon Jun  3 13:58:05 2024

@author: zshawver

"""
from itertools import product, combinations
from random import shuffle 
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import io




def buildDeck(ranks,suits):
    '''
    Creates a deck of 52 cards
    Combines 13 card ranks with 4 card suits

    Parameters
    ----------
    ranks : list
        This is a list from 1-13.
        The values signify the 13 ranks of cards in a deck.
        1:Deuce(2) -- 13:Ace(A)
    suits : list
        This is a list from 1-4.
        The values signify the 4 suits of cards in a deck.
        1:Club, 2: Hearts, 3: Diamonds, 4: Spades

    Returns
    -------
    deck : list
        The list is 52 tuples.
        Each tuple represents a card.
        The rank is the first element.
        The suit is the second element.
        card = (rank,tuple)
        The final deck of cards is shuffled.

    '''
    #creates the 52 card combinations and shuffles the deck
    deck = list(product(ranks, suits))
    shuffle(deck)
    return deck

#identifies and returns the flush suit
def getFlushSuit(suitsCount):
    '''
    Gets the flush suit of a hand of 7 cards
    Checks whether there are at least 5 cards of same suit

    Parameters
    ----------
    suitsCount : Counter
        A counter {item:count} of card suits in hand.
        Need to create the counter on the hand suits before hand.
        suitsCount = Counter(card[1] for card in hand)

    Returns
    -------
    int
        The suit for which there are at least 5 cards.
        If there is no flush, the return is empty.

    '''
    #identify the flushed suit
    flushSuit = [suit for suit in suitsCount if suitsCount[suit] >= 5]
    #if there is a flush, return the flush suit, or else nothing
    return flushSuit[0] if flushSuit else None

#finds and returns all cards in hand of the flush suit
def getFlushHand(hand, flushSuit):
    '''
    Gives the hand composed of only flush suited cards.

    Parameters
    ----------
    hand : list
        A list of 7 cards.
        Each card is a tuple composed of (rank,suit)
    flushSuit : int
        The value of suit for which there is a flush.

    Returns
    -------
    list
        A hand of at least 5 cards, all of same suit.

    '''
    #keep only cards in flush suit
    return [card for card in hand if card[1] == flushSuit]

def getRankSet(hand):
    '''
    Gives just the ranks of cards in hands without duplicates.

    Parameters
    ----------
    hand : hand : list
        A list of 7 cards.
        Each card is a tuple composed of (rank,suit).

    Returns
    -------
    set
        A set of card ranks, sorted from highest to lowest.

    '''
    return sorted({card[0] for card in hand}, reverse=True)

def checkRoyalFlush(hand):
    '''
    Checks hand of 7 cards for a Royal Flush
    '''
    
    #count all the suits in the hand
    suitsCount = Counter([card[1] for card in hand])
    
    #if there are more than 5 of same suit counted 
    if max(suitsCount.values()) >= 5:
        
        #get the flush suit
        flushSuit = getFlushSuit(suitsCount)
    
        #if there is a flushsuit
        if flushSuit:
            
            #keep only flush cards in hand
            flushHand = getFlushHand(hand, flushSuit)
            
            #if in the flush hand there is A-K-Q-J-T
            if all(rank in [card[0] for card in flushHand] for rank in [13,12,11,10,9]):
                return True
            else:
                return False
        else:
            return False
    else:
        return False

def checkStraightFlush(hand):
    '''
    Checks hand of 7 cards for a Straight Flush
    '''
    
    #count all the suits in the hand
    suitsCount = Counter([card[1] for card in hand])
    
    #if there are more than 5 of same suit counted 
    if max(suitsCount.values()) >= 5:
        
        #get the flush suit
        flushSuit = getFlushSuit(suitsCount)
    
        #if there is a flushsuit
        if flushSuit:
            
            #keep only flush cards in hand
            flushHand = getFlushHand(hand, flushSuit)
            #get and sort the card ranks without duplicates
            rankSet = getRankSet(flushHand)
            
            #for 5 or more cards
            if len(rankSet)<=4:
                return False
            #tests for an 5(4)-Ace(13) wheel straight
            if all(rank in rankSet for rank in [13,4,3,2,1]):
                return True
                
            else:
                #how many possible straights there are
                checks = len(rankSet)-4
                
                #check each possible straight
                for i in range(checks):
                    
                    #tests the difference between the high and low card
                    #A difference of 4 means that there are 5 sequential cards
                    if rankSet[i]-rankSet[i+4] == 4:
                        return True
                    else:
                        return False
    else:
        return False

def checkFourKind(hand):
    '''
    Checks hand of 7 cards for a Four-Of-A-Kind
    '''
    
    #Get the number of times each rank appears in hand
    cardsCount = Counter(card[0] for card in hand)
    
    #checks if one card appears 4 times
    if 4 in cardsCount.values():
        return True
    else:
        return False

def checkFullHouse(hand):
    '''
    Checks hand of 7 cards for a Full House
    '''
    
    #Get the number of times each rank appears in hand
    cardsCount = Counter(card[0] for card in hand)
    #summarizes the number of times cards appear
    countsCount = Counter(cardsCount.values())
    #checks if there are two sets or a set with at least one pair
    if countsCount[3]== 2 or (countsCount[3] == 1 and countsCount[2] >= 1):
        return True
    else:
        return False

def checkFlush(hand):
    '''
    Checks hand of 7 cards for a Flush
    '''
    
    #count all the suits in the hand
    suitsCount = Counter([card[1] for card in hand])
    
    #if there are more than 5 of same suit counted 
    if max(suitsCount.values()) >= 5: 
        return True
    else:
        return False

def checkStraight(hand):
    '''
    Checks hand of 7 cards for a Straight
    '''
    
    #get and sort the card ranks without duplicates
    rankSet = getRankSet(hand)
    
    #for 5 or more cards
    if len(rankSet)<=4:
        return False
    #tests for an ace-low straight
    if all(rank in rankSet for rank in [4,3,2,1,13]):
        return True
        
    else:
        #how many possible straights there are
        checks = len(rankSet)-4
        
        #check each possible straight
        for i in range(checks):
            
            #tests the difference between the high and low card
            if rankSet[i]-rankSet[i+4] == 4:
                return True
        return False

def checkThreeKind(hand):
    '''
    Checks hand of 7 cards for a Three-Of-A-Kind
    '''
    
    #Get the number of times each rank appears in hand
    cardsCount = Counter(card[0] for card in hand)
    #checks if one card appears 3 times
    if 3 in cardsCount.values():
        return True
    else:
        return False

def checkTwoPair(hand):
    '''
    Checks hand of 7 cards for a Two-Pair
    '''
    
    #Get the number of times each rank appears in hand
    cardsCount = Counter(card[0] for card in hand)
    #summarizes the number of times cards appear
    countsCount = Counter(cardsCount.values())
    #checks if two different cards appear twice with no set or quad
    if countsCount[2]>=2:
        return True
    else:
        return False

def checkPair(hand):
    '''
    Checks hand of 7 cards for a Pair
    '''
    
    #Get the number of times each rank appears in hand
    cardsCount = Counter(card[0] for card in hand)
    #summarizes the number of times cards appear
    countsCount = Counter(cardsCount.values())
    #checks if a pair appears just one time
    if countsCount[2] == 1:
        return True
    else:
        return False

def checkHighCard(hand):
    '''
    Checks hand of 7 cards for a High Card
    '''
    
    #Get the number of times each rank appears in hand
    cardsCount = Counter(card[0] for card in hand)
    #counts the number of counts
    countsCount = Counter(cardsCount.values())
    #checks if there are 7 unique cards
    if countsCount[1] == 7:
        return True
    else:
        return False

def scoreHand(hand):
    '''
    Function to Score Poker Hand
    
    Runs through a list of checking functions.
    The functions are in order from strongest to weakest.
    Each function returns either True or False.
    If a function returns True, then a score gets assigned based on the strength of the hand.
    The score gets returned.

    Parameters
    ----------
    hand : list
        The seven cards (2 in hole + 5 community) in a poker hand.
        Each card in poker hand is a tuple: (rank,suit).
        Ranks range 1-13 and correspond to deuce(2)-Ace(A).
        Pairing of card ranks and values is in rankValues.
        Suits range from 1-4 and correspond to Clubs, Hearts, Diamonds, Spades.
        Pairing of card suits and symbols is in suitSymbols.

    Returns
    -------
    int
        The score for the best poker hand available.
        The scores are based on the standard strongest hands ranked.

    '''
    
    # Ensure the hand has the correct number of cards
    if len(hand) != 7 or not all(isinstance(card, tuple) and len(card) == 2 for card in hand):
        raise ValueError("Invalid hand. Must contain 7 cards, each represented as a tuple (rank, suit).")

    if checkRoyalFlush(hand):
        return 10
    if checkStraightFlush(hand):
        return 9
    if checkFourKind(hand):
        return 8
    if checkFullHouse(hand):
        return 7
    if checkFlush(hand):
        return 6
    if checkStraight(hand):
        return 5
    if checkThreeKind(hand):
        return 4
    if checkTwoPair(hand):
        return 3
    if checkPair(hand):
        return 2
    if checkHighCard(hand):
        return 1
    else:
        #Should never reach here for a valid hand
        raise ValueError("Hand did not match any known poker hand type.")

def getBestHand(score, hand):
    '''
    Function to Get the Best 5-card Poker Hand from seven cards
    
    Takes the score of a poker hand and the dealt hand to produce the five
    cards that were used to score the poker hand.
    
    Parameters
    ----------
    score : int
        The highest score of a poker hand from the scoreHand() function.
    hand : list
        The seven cards (2 in hole + 5 community) in a poker hand.
        Each card in poker hand is a tuple: (rank,suit).
        Ranks range 1-13 and correspond to deuce(2)-Ace(A).
        Pairing of card ranks and values is in rankValues.
        Suits range from 1-4 and correspond to Clubs, Hearts, Diamonds, Spades.
        Pairing of card suits and symbols is in suitSymbols.

    Returns
    -------
    list
        The best five cards from the seven card hand.
        These cards are the ones used to achieve the high-scoring hand.

    '''

    #count the suits in a hand
    suitsCount = Counter([card[1] for card in hand])
    #count the ranks in a hand
    cardsCount = Counter([card[0] for card in hand])

    #royal flush
    if score == 10:
        #get the flush suit
        flushSuit = getFlushSuit(suitsCount)
        
        if flushSuit:
            #get the flush hand
            flushHand = getFlushHand(hand, flushSuit)
            
            #choose the highest 5 cards with the flush suit
            bestHand = sorted(flushHand,reverse = True)[:5]
            return bestHand
        
    #straight flush
    if score == 9:
        #get the flush suit
        flushSuit = getFlushSuit(suitsCount)
        if flushSuit:
            #get the flush hand
            flushHand = getFlushHand(hand, flushSuit)
            
            #get the unique ranks for cards in the hand
            rankSet = sorted({card[0] for card in flushHand},reverse=True)
            
            #check for ace-low straight first
            if all(rank in rankSet for rank in [4,3,2,1,13]):
                bestHand = [card for rank in [4,3,2,1,13] for card in flushHand if card[0] == rank]
                return bestHand
            
            else:
                checks = len(rankSet)-4
                
                #check each possible straight
                for i,check in enumerate(range(checks)):
                    
                    #tests the difference between the high and low card
                    #if the difference between a high and low card is 4, then it is a straight
                    if rankSet[i]-rankSet[i+4] == 4:
                        #gets the ranks of the cards in the straight
                        straightRanks = rankSet[i:i+5]
                        #creates a shell to hold card ranks that have been used
                        usedRanks = set()
                        #keeps the best cards in the straight
                        bestHand = [card for card in flushHand if card[0] in straightRanks and not (card[0] in usedRanks or usedRanks.add(card[0]))]
                        return bestHand
    
    #four of a kind
    if score == 8:
        #get the rank of the quad card
        quadRank = [rank for rank in cardsCount if cardsCount[rank] == 4][0]
        #get the cards in the quad
        quadCards = [card for card in hand if card[0] == quadRank]
        #get the highest card outside of the quad
        kicker = sorted([card for card in hand if card[0] != quadRank], reverse = True)[0]
        #add the kicker to the best hand
        bestHand = quadCards + [kicker]
        return bestHand

    
    #full house
    if score == 7:
        #gets all set ranks in the hand
        maxSet = [rank for rank in cardsCount if cardsCount[rank] == 3]
        #finds highest ranking set
        maxSetRank = max(maxSet)
        #pulls the set cards
        setCards = [card for card in hand if card[0] == maxSetRank]
        #finds second highest set or any pairs
        maxFull = [rank for rank in cardsCount if cardsCount[rank] >= 2 and rank != maxSetRank]
        #finds the highest ranking set or pair
        maxFullRank = max(maxFull)
        #pulls the full pair
        fullCards = [card for card in hand if card[0] == maxFullRank]
        #combines the set and full cards
        bestHand = setCards + fullCards
        return bestHand
    
    #flush
    if score == 6:
        #get the flush suit
        flushSuit = getFlushSuit(suitsCount)
        
        if flushSuit:
            #get the flush hand
            flushHand = getFlushHand(hand, flushSuit)
            
            #choose the highest 5 cards with the flush suit
            bestHand = sorted(flushHand, reverse = True)[:5]
            return bestHand
    
    #straight
    if score == 5:
        rankSet = sorted({card[0] for card in hand},reverse=True)
        
        #check for ace-low straight first
        if all(rank in rankSet for rank in [4,3,2,1,13]):
            bestHand = [card for rank in [4,3,2,1,13] for card in hand if card[0] == rank]
            return bestHand
        
        else:
            checks = len(rankSet)-4
            
            #check each possible straight
            for i in range(checks):
                
                #tests the difference between the high and low card
                #if the difference between a high and low card is 4, then it is a straight
                if rankSet[i]-rankSet[i+4] == 4:
                    #gets the ranks of the cards in the straight
                    straightRanks = rankSet[i:i+5]
                    #creates a shell to hold card ranks that have been used
                    usedRanks = set()
                    #keeps the best cards in the straight
                    bestHand = [card for card in hand if card[0] in straightRanks and not (card[0] in usedRanks or usedRanks.add(card[0]))]
                    return bestHand
    
    #three of a kind
    if score == 4:
        #finds the rank of cards in set
        setRank = [rank for rank in cardsCount if cardsCount[rank] == 3][0]
        #pulls the set cards
        setCards = [card for card in hand if card[0] == setRank]
        #pulls highest remaining cards
        kickers = sorted([card for card in hand if card[0] != setRank], reverse = True)[:2]
        #combines the set and kickers
        bestHand = setCards + kickers
        return bestHand
    
    #two pair
    if score == 3:
        #gets all sets in the hand
        maxPairs = sorted([rank for rank in cardsCount if cardsCount[rank] == 2], reverse = True)[:2]
        #pulls the two highest ranking pairs
        pairs = [card for pair in maxPairs for card in hand if card[0] == pair]
        #finds the kicker
        kicker = sorted([card for card in hand if card not in pairs],reverse = True)[0]
        #adds the kicker to the pairs
        bestHand = pairs + [kicker]
        return bestHand
    
    #pair
    if score == 2:
        #finds the rank of cards in set
        pairRank = [rank for rank in cardsCount if cardsCount[rank] == 2][0]
        #pulls the set cards
        pairCards = [card for card in hand if card[0] == pairRank]
        #pulls highest remaining cards
        kickers = sorted([card for card in hand if card[0] != pairRank], reverse = True)[:3]
        #combines the set and kickers
        bestHand = pairCards + kickers
        return bestHand
    
    
    #high card
    if score == 1:
        bestHand = sorted([card for card in hand], reverse = True)[:5]
        return bestHand
    else:
        #Should never reach here for a valid hand
        raise ValueError("Hand did not match any known poker hand type.")

def getRangeHands(deck, handsList, rankValues):
    # creates a list of all 2-card draw combinations
    allDraws = list(combinations(deck, 2))
    
    # prepares an empty dictionary to hold the card draws
    rangeHands = {}
    
    # loop through all possible 2-card hands
    for hand in handsList:
        # check if hand is a pair
        if len(hand) == 2:
            # get the numeric rank of the pair
            getVal = hand[0]
            
            # get the card rank value
            cardVal = list(rankValues.keys())[list(rankValues.values()).index(getVal)]
            
            # make list of all pairs for a particular value
            draws = [[draw[0], draw[1]] for draw in allDraws if draw[0][0] == cardVal and draw[1][0] == cardVal]
            
            # append hand with all combination draws to dictionary
            rangeHands.update({hand: draws})
    
        # check if hand is suited 
        elif hand[-1] == 's':
            # get the numeric rank of each card in hand
            getVal0 = hand[0]
            getVal1 = hand[1]
            
            # get the cards' rank values
            cardVal0 = list(rankValues.keys())[list(rankValues.values()).index(getVal0)]
            cardVal1 = list(rankValues.keys())[list(rankValues.values()).index(getVal1)]
            
            # make list of all suited hands
            draws = [[draw[0], draw[1]] for draw in allDraws if draw[0][1] == draw[1][1] and ((draw[0][0] == cardVal0 or draw[0][0] == cardVal1) and (draw[1][0] == cardVal0 or draw[1][0] == cardVal1))]
            
            # append hand with all combination draws to dictionary
            rangeHands.update({hand: draws})
        
        # check if hand is off-suited        
        elif hand[-1] == 'o':
            # get the numeric rank of each card in hand
            getVal0 = hand[0]
            getVal1 = hand[1]
            
            # get the cards' rank values
            cardVal0 = list(rankValues.keys())[list(rankValues.values()).index(getVal0)]
            cardVal1 = list(rankValues.keys())[list(rankValues.values()).index(getVal1)]
            
            # make list of all off-suited hands
            draws = [[draw[0], draw[1]] for draw in allDraws if draw[0][1] != draw[1][1] and draw[0][0] != draw[1][0] and ((draw[0][0] == cardVal0 or draw[0][0] == cardVal1) and (draw[1][0] == cardVal0 or draw[1][0] == cardVal1))]
            
            # append hand with all combination draws to dictionary
            rangeHands.update({hand: draws})
    
    return rangeHands

# Function to brighten a hex color
def brighten_color(hex_color, factor=1.2):
    #Converts a hexcolor to RGB
    rgb = mcolors.hex2color(hex_color)
    #brightens RGB color by whatever scaling factor
    bright_rgb = [min(1, c * factor) for c in rgb]
    return mcolors.to_hex(bright_rgb)

def create_plot(handsList,ranges,draw,bestRange):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    fig.patch.set_facecolor('#247345') #Change the plot color to match pygame bg color

    ax.set_xlim(0, 13)
    ax.set_ylim(0, 13)
    ax.set_aspect('equal')

    ax.grid(True, color='white')
    ax.set_xticks(range(14))
    ax.set_yticks(range(14))
    ax.tick_params(axis='both', which='both', length=0)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    

    ax.invert_yaxis()

    
    #Colors from Moonrise Kingdom from R package wespalette
    wesPalette = [
        "#F3DF6C", "#CEAB07", "#D5D5D3", "#24281A",
        "#798E87", "#C27D38", "#CCC591", "#29211F",
        "#85D4E3", "#F4B5BD", "#9C964A", "#CDC08C", "#FAD77B"]

      
    handsListFormatting = {}
    for hand in handsList:
        if len(hand) == 2:
            handsListFormatting.update({hand:wesPalette[8]})
        elif hand[-1] == 's':
            handsListFormatting.update({hand:wesPalette[0]})
        elif hand[-1] == 'o':
            handsListFormatting.update({hand:wesPalette[9]})

    for i, hand in enumerate(handsList):
        row = i // 13
        col = i % 13

        color = handsListFormatting[hand]

        if hand == draw:
            alpha = 1
            fontsize = 13
            weight = 'bold'
            color = brighten_color(color)

            ax.add_patch(plt.Rectangle((col, row), 1, 1, fill=False, edgecolor='black', linewidth=5))
        else:
            alpha = 0.2
            fontsize = 10
            weight = 'normal'

        if bestRange != 'fold':
            if hand in ranges[bestRange]:
                alpha = 0.6

        ax.text(col + 0.5, row + 0.5, hand, ha='center', va='center', fontsize=fontsize, color='black', weight=weight)
        ax.add_patch(plt.Rectangle((col, row), 1, 1, color=color, alpha=alpha))

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf
