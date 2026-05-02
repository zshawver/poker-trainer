
from collections import Counter
from itertools import product
from random import shuffle
from poker_variables import deckSymbols

class Hand:
    def __init__(self, table):
        # Initialize broader game variables
        self.table = table  # set the table where the hand will be played
        self.players = self.table.players  # get all the players at the table

        # Initialize card variables
        self.deck = None  # variable to hold deck

        # Initialize hand states
        self.holeState = False  # hole has not been dealt
        self.flopState = False  # flop has not been dealt
        self.turnState = False  # turn has not been dealt
        self.riverState = False  # river has not been dealt

        # Initialize hand outcomes
        self.scores = None  # variable to hold scores
        self.winner = None  # variable to hold winner


    def newHand(self):
        # Reset players in hand
        self.players = self.table.players  # All players at table will play

        # Reset card variables
        # create a shuffled deck of 52 cards represented as numeric tuples
        self.deck = Hand.buildDeck()

        # Reset hand states
        self.holeState = False  # hole has not been dealt
        self.flopState = False  # flop has not been dealt
        self.turnState = False  # turn has not been dealt
        self.riverState = False  # river has not been dealt

        # Reset player variables
        for player in self.players:
            player.hand = []  # Give each player an empty hand
            player.score = None  # Give each player no score

        # Reset hand outcomes
        self.winner = None  # There's no winner before the hand starts
        print("start a new hand")
        print([deckSymbols[card] for card in self.deck][:5])

    def deal(self, card, player):
        player.hand.append(card)  # ...deal a card

    def dealHole(self):
        for _ in range(2):  # deal two cards
            for player in self.players:
                holeCard = self.deck.pop(0)  # Pull top card from deck
                self.deal(holeCard, player)  # Deal card to each player
        self.holeState = True  # hole has been dealt

    def dealFlop(self):
        if self.holeState:  # if hole has been dealt
            self.deck.pop(0)  # burn one card
            flop = self.deck[:3]  # Get next three cards for flop
            self.deck = self.deck[3:]  # reset deck to be all cards after flop
            for player in self.players:
                for card in flop:
                    self.deal(card, player)  # Deal each player the flop
            self.flopState = True  # flop has been dealt

        else:
            print("hole hasn't been dealt yet")

    def dealTurn(self):
        if self.flopState:  # if flop has been dealt
            self.deck.pop(0)  # burn one card
            turn = self.deck.pop(0)  # Get next card for turn
            for player in self.players:
                self.deal(turn, player)  # deal the turn to each player
            self.turnState = True

        else:
            print("flop hasn't been dealt yet")

    def dealRiver(self):
        if self.turnState:  # if turn has been dealt
            self.deck.pop(0)  # burn on card
            river = self.deck.pop(0)  # Get next card for river
            for player in self.players:
                self.deal(river, player)  # deal the river to each player
            self.riverState = True

        else:
            print("turn hasn't been dealt yet")

    def fold(self, player):
        self.players.remove(player)  # remove the player from the hand

    def scoreHands(self):
        for player in self.players:
            player.score = Hand.scoreHand(
                player.hand)  # get each player's score

    def getWinner(self):
        # collect players' scores
        self.scores = [player.score for player in self.players]
        # print(self.scores)
        maxScore = max(self.scores)  # get the highest score
        scoresCount = Counter(self.scores)  # get a count of the scores
        # print(scoresCount)
        if scoresCount[maxScore] == 1:
            winner = self.players[self.scores.index(maxScore)]
            # print(winner.name)
            self.winner = [winner]
            # return [winner]
        else:

            # Multiple players with the highest score
            bestHands = {player: Hand.getBestHand(
                player.score, player.hand) for player in self.players if player.score == maxScore}
            winner = Hand.settleTie(maxScore, bestHands)
            self.winner = winner
            # return winner

    def nameWinners(self):
        #Print the name of the winners

        if len(self.winner) > 1:
            print('split pot')

        for player in self.players:
            if player in self.winner:
                playerBestHand = Hand.getBestHand(player.score,player.hand)
                print("{} is a winner with {}".format(player.name,[deckSymbols[card] for card in playerBestHand]))

    @staticmethod
    def settleTie(score, bestHands):
        if score == 10:
            return Hand.royalFlushTie(bestHands)
        elif score == 9:
            return Hand.straightFlushTie(bestHands)
        elif score == 8:
            return Hand.fourOfAKindTie(bestHands)
        elif score == 7:
            return Hand.fullHouseTie(bestHands)
        elif score == 6:
            return Hand.flushTie(bestHands)
        elif score == 5:
            return Hand.straightTie(bestHands)
        elif score == 4:
            return Hand.threeOfAKindTie(bestHands)
        elif score == 3:
            return Hand.twoPairTie(bestHands)
        elif score == 2:
            return Hand.pairTie(bestHands)
        elif score == 1:
            return Hand.highCardTie(bestHands)
        else:
            raise ValueError("Invalid score")

    @staticmethod
    def royalFlushTie(bestHands):
        # Royal flush is the best hand, so all players are winners
        return list(bestHands.keys())

    @staticmethod
    def straightFlushTie(bestHands):
        # Compare the ranks of the cards in players' hands
        winners = Hand.compareNonPairHands(bestHands)
        return winners

    @staticmethod
    def fourOfAKindTie(bestHands):
        # Four of a kind: compare the ranks of the quads, then the kicker
        # Count the card ranks for all players' best hands
        playerCounts = {player: Counter(
            card[0] for card in hand) for player, hand in bestHands.items()}

        # Identify the quad rank for each player
        playerQuads = {player: next(card for card, count in counts.items(
        ) if count == 4) for player, counts in playerCounts.items()}

        # Find the maximum quad
        maxQuad = max(playerQuads.values())

        # Count how many players have the maximum set
        quadsCount = Counter(playerQuads.values())

        # If only one player has the highest quad, declare them the winner
        if quadsCount[maxQuad] == 1:
            winner = next(player for player,
                          Set in playerQuads.items() if Set == maxQuad)
            return [winner]
        else:
            # Players with the max quad
            maxQuadPlayers = [
                player for player in bestHands.keys() if playerQuads[player] == maxQuad]
            # Players and the rank of their kickers
            playerKickers = {player: [card[0] for card in hand if card[0] != maxQuad][0]
                             for player, hand in bestHands.items() if player in maxQuadPlayers}
            # Highest kicker rank
            maxKicker = max(playerKickers.values())
            # Count number of players with highest kicker rank
            kickersCount = Counter(playerKickers.values())

            # Among players with the highest quads, if there is one player with the highest kicker
            if kickersCount[maxKicker] == 1:
                winner = next(
                    player for player, kicker in playerKickers.items() if kicker == maxKicker)
                return [winner]
            else:
                # Multiple winners
                winners = [player for player,
                           kicker in playerKickers.items() if kicker == maxKicker]
                return winners

    @staticmethod
    def fullHouseTie(bestHands):
        # Full house: compare the ranks of the triples first, then the pairs

        # Count the card ranks for all players' best hands
        playerCounts = {player: Counter(
            card[0] for card in hand) for player, hand in bestHands.items()}

        # Identify the set rank for each player
        playerSets = {player: next(card for card, count in counts.items(
        ) if count == 3) for player, counts in playerCounts.items()}

        # Find the maximum set
        maxSet = max(playerSets.values())

        # Count how many players have the maximum set
        setsCount = Counter(playerSets.values())

        # If only one player has the highest set, declare them the winner
        if setsCount[maxSet] == 1:
            winner = next(player for player,
                          Set in playerSets.items() if Set == maxSet)
            return [winner]
        else:
            # Players with the max set
            maxSetPlayers = [
                player for player in bestHands.keys() if playerSets[player] == maxSet]
            # Players and the rank of their pairs
            playerPairs = {player: set(card[0] for card in hand if card[0] != maxSet).pop(
            ) for player, hand in bestHands.items() if player in maxSetPlayers}
            # Highest pair rank
            maxPair = max(playerPairs.values())
            # Count number of players with highest pair rank
            pairsCount = Counter(playerPairs.values())

            # Among players with the highest sets, if there is one player with the highest pair
            if pairsCount[maxPair] == 1:
                winner = next(player for player,
                              pair in playerPairs.items() if pair == maxPair)
                return [winner]
            else:
                # Multiple winners
                winners = [player for player,
                           pair in playerPairs.items() if pair == maxPair]
                return winners

    @staticmethod
    def flushTie(bestHands):
        # Flush: compare the highest cards by card rank
        winners = Hand.compareNonPairHands(bestHands)
        return winners

    @staticmethod
    def straightTie(bestHands):
        # Straight: compare the highest cards by card rank
        winners = Hand.compareNonPairHands(bestHands)
        return winners

    @staticmethod
    def threeOfAKindTie(bestHands):
        # Three of a kind: compare the ranks of the triplets first, then the kickers
        # Count the card ranks for all players' best hands
        playerCounts = {player: Counter(
            card[0] for card in hand) for player, hand in bestHands.items()}

        # Identify the set rank for each player
        playerSets = {player: next(card for card, count in counts.items(
        ) if count == 3) for player, counts in playerCounts.items()}

        # Find the maximum set
        maxSet = max(playerSets.values())

        # Count how many players have the maximum set
        setsCount = Counter(playerSets.values())

        # If only one player has the highest set, declare them the winner
        if setsCount[maxSet] == 1:
            winner = next(player for player,
                          Set in playerSets.items() if Set == maxSet)
            return [winner]
        else:
            # Players with the max set
            maxSetPlayers = [
                player for player in bestHands.keys() if playerSets[player] == maxSet]
            # Hands without the sets for those players
            nonSetHands = {player: [card for card in hand if card[0] != playerSets[player]]
                           for player, hand in bestHands.items() if player in maxSetPlayers}
            winners = Hand.compareNonPairHands(nonSetHands)
            return winners

    @staticmethod
    def twoPairTie(bestHands):
        # Two pair: compare the higher pairs, then the lower pairs, then the kicker
        def flatten(xss):
            '''
            Parameters
            ----------
            xss : List
                A list of lists of all pair ranks.

            Returns
            -------
            list
                A list of single elements.

            '''
            return [x for xs in xss for x in xs]

        def findSecondHighest(nums):
            '''

            Parameters
            ----------
            nums : List
                A list of numbers.

            Raises
            ------
            ValueError
                The list must have at least two numbers in it.

            Returns
            -------
            second : int
                Gives the second highest element from a list of numbers.

            '''
            if len(nums) < 2:
                raise ValueError("List must contain at least two elements.")

            first, second = None, None

            for num in nums:
                if first is None or num > first:
                    first, second = num, first
                elif num != first and (second is None or num > second):
                    second = num

            if second is None:
                raise ValueError(
                    "No second highest value found; the list may contain duplicates of the maximum value only.")

            return second

        # Pair: compare the rank of the pair first, then the kickers
        # Count the card ranks for all players' best hands
        playerCounts = {player: Counter(
            card[0] for card in hand) for player, hand in bestHands.items()}

        # Identify the pair ranks for each player
        playerPairs = {player: [rank for rank, c in count.items(
        ) if c == 2] for player, count in playerCounts.items()}

        # Find the maximum pair
        playerPairRanks = flatten(playerPairs.values())
        maxPair = max(playerPairRanks)

        #Get the players who hold the maximum pair
        playersWithMaxPair = [player for player, pairRanks in playerPairs.items() if maxPair in pairRanks]

        # If only one player has the highest pair, declare them the winner
        if len(playersWithMaxPair) == 1:
             winner = playersWithMaxPair[0]
             return [winner]
        else:
            #Get the second highest pair rank
            maxLowerPair = findSecondHighest(playerPairRanks)
            #Get the players' hands for everyone with max pair
            maxPairPlayerHands = {player:[card[0] for card in bestHands[player]] for player in playersWithMaxPair}
            #Get the players who have both max pair and max lower pair
            playersWithMaxLowerPair = [player for player,ranks in maxPairPlayerHands.items() if maxLowerPair in ranks]
            #If there's only one player with max lower pair
            if len(playersWithMaxLowerPair) == 1:
                #only one winner
                return playersWithMaxLowerPair
            else:
                #Evaluate kickers
                #Get the players' kicker cards
                playerKickers = {player:[num for num in hand if num != maxPair and num != maxLowerPair][0] for player,hand in maxPairPlayerHands.items()}
                #Find the highest kicker card
                maxKicker = max(playerKickers.values())
                #Get the players who have the highest kicker card
                playersWithMaxKickers = [player for player,kicker in playerKickers.items() if kicker == maxKicker]
                #If only one player has the highest kicker
                if len(playersWithMaxKickers) == 1:
                    #Only one winner
                    return playersWithMaxKickers
                else:
                    #split pot
                    return playersWithMaxKickers

    @staticmethod
    def pairTie(bestHands):
        # Pair: compare the rank of the pair first, then the kickers
        # Count the card ranks for all players' best hands
        playerCounts = {player: Counter(
            card[0] for card in hand) for player, hand in bestHands.items()}

        # Identify the pair rank for each player
        playerPairs = {player: next(card for card, count in counts.items(
        ) if count == 2) for player, counts in playerCounts.items()}

        # Find the maximum pair
        maxPair = max(playerPairs.values())

        # Count how many players have the maximum pair
        pairsCount = Counter(playerPairs.values())

        # If only one player has the highest pair, declare them the winner
        if pairsCount[maxPair] == 1:
            winner = next(player for player,
                          pair in playerPairs.items() if pair == maxPair)
            return [winner]
        else:
            # Players with the max pair
            maxPairPlayers = [
                player for player in bestHands.keys() if playerPairs[player] == maxPair]

            # Hands without the pairs for those players
            nonPairHands = {player: [card for card in hand if card[0] != playerPairs[player]]
                            for player, hand in bestHands.items() if player in maxPairPlayers}
            winners = Hand.compareNonPairHands(nonPairHands)
            return winners

    @staticmethod
    def highCardTie(bestHands):
        # High card: compare the highest cards
        winners = Hand.compareNonPairHands(bestHands)
        return winners

    @staticmethod
    def compareNonPairHands(bestHands):
        # Compare the remaining cards in each player's hand
        best_hand = None
        # Create an empty list to contain the winners
        winners = []

        # Across players' hands
        for player, hand in bestHands.items():
            # Just look at the ranks of the cards
            handRank = sorted([card[0] for card in hand], reverse=True)
            # If there's no best hand yet, or if the current best hand is better than a previous best hand
            if best_hand is None or handRank > best_hand:
                # The current best hand is the current hand being evaluated
                best_hand = handRank
                # That player is currently the winner
                winners = [player]
            # If the current hand being evaluated
            elif handRank == best_hand:
                # Add the player with the hand currently being evaluated to the winners list
                winners.append(player)

        return winners

    @staticmethod
    def buildDeck():
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
        # create list of card ranks
        ranks = list(range(1, 14))
        # create list of card suits
        suits = list(range(1, 5))

        # creates the 52 card combinations and shuffles the deck
        deck = list(product(ranks, suits))
        shuffle(deck)
        return deck

    # identifies and returns the flush suit
    @staticmethod
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
        # identify the flushed suit
        flushSuit = [suit for suit in suitsCount if suitsCount[suit] >= 5]
        # if there is a flush, return the flush suit, or else nothing
        return flushSuit[0] if flushSuit else None

    # finds and returns all cards in hand of the flush suit
    @staticmethod
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
        # keep only cards in flush suit
        return [card for card in hand if card[1] == flushSuit]

    @staticmethod
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

    @staticmethod
    def checkRoyalFlush(hand):
        '''
        Checks hand of 7 cards for a Royal Flush
        '''

        # count all the suits in the hand
        suitsCount = Counter([card[1] for card in hand])

        # if there are more than 5 of same suit counted
        if max(suitsCount.values()) >= 5:

            # get the flush suit
            flushSuit = Hand.getFlushSuit(suitsCount)

            # if there is a flushsuit
            if flushSuit:

                # keep only flush cards in hand
                flushHand = Hand.getFlushHand(hand, flushSuit)

                # if in the flush hand there is A-K-Q-J-T
                if all(rank in [card[0] for card in flushHand] for rank in [13, 12, 11, 10, 9]):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    @staticmethod
    def checkStraightFlush(hand):
        '''
        Checks hand of 7 cards for a Straight Flush
        '''

        # count all the suits in the hand
        suitsCount = Counter([card[1] for card in hand])

        # if there are more than 5 of same suit counted
        if max(suitsCount.values()) >= 5:

            # get the flush suit
            flushSuit = Hand.getFlushSuit(suitsCount)

            # if there is a flushsuit
            if flushSuit:

                # keep only flush cards in hand
                flushHand = Hand.getFlushHand(hand, flushSuit)
                # get and sort the card ranks without duplicates
                rankSet = Hand.getRankSet(flushHand)

                # for 5 or more cards
                if len(rankSet) <= 4:
                    return False
                # tests for an 5(4)-Ace(13) wheel straight
                if all(rank in rankSet for rank in [13, 4, 3, 2, 1]):
                    return True

                else:
                    # how many possible straights there are
                    checks = len(rankSet)-4

                    # check each possible straight
                    for i in range(checks):

                        # tests the difference between the high and low card
                        # A difference of 4 means that there are 5 sequential cards
                        if rankSet[i]-rankSet[i+4] == 4:
                            return True
                        else:
                            return False
        else:
            return False

    @staticmethod
    def checkFourKind(hand):
        '''
        Checks hand of 7 cards for a Four-Of-A-Kind
        '''

        # Get the number of times each rank appears in hand
        cardsCount = Counter(card[0] for card in hand)

        # checks if one card appears 4 times
        if 4 in cardsCount.values():
            return True
        else:
            return False

    @staticmethod
    def checkFullHouse(hand):
        '''
        Checks hand of 7 cards for a Full House
        '''

        # Get the number of times each rank appears in hand
        cardsCount = Counter(card[0] for card in hand)
        # summarizes the number of times cards appear
        countsCount = Counter(cardsCount.values())
        # checks if there are two sets or a set with at least one pair
        if countsCount[3] == 2 or (countsCount[3] == 1 and countsCount[2] >= 1):
            return True
        else:
            return False

    @staticmethod
    def checkFlush(hand):
        '''
        Checks hand of 7 cards for a Flush
        '''

        # count all the suits in the hand
        suitsCount = Counter([card[1] for card in hand])

        # if there are more than 5 of same suit counted
        if max(suitsCount.values()) >= 5:
            return True
        else:
            return False

    @staticmethod
    def checkStraight(hand):
        '''
        Checks hand of 7 cards for a Straight
        '''

        # get and sort the card ranks without duplicates
        rankSet = Hand.getRankSet(hand)

        # for 5 or more cards
        if len(rankSet) <= 4:
            return False
        # tests for an ace-low straight
        if all(rank in rankSet for rank in [4, 3, 2, 1, 13]):
            return True

        else:
            # how many possible straights there are
            checks = len(rankSet)-4

            # check each possible straight
            for i in range(checks):

                # tests the difference between the high and low card
                if rankSet[i]-rankSet[i+4] == 4:
                    return True
            return False

    @staticmethod
    def checkThreeKind(hand):
        '''
        Checks hand of 7 cards for a Three-Of-A-Kind
        '''

        # Get the number of times each rank appears in hand
        cardsCount = Counter(card[0] for card in hand)
        # checks if one card appears 3 times
        if 3 in cardsCount.values():
            return True
        else:
            return False

    @staticmethod
    def checkTwoPair(hand):
        '''
        Checks hand of 7 cards for a Two-Pair
        '''

        # Get the number of times each rank appears in hand
        cardsCount = Counter(card[0] for card in hand)
        # summarizes the number of times cards appear
        countsCount = Counter(cardsCount.values())
        # checks if two different cards appear twice with no set or quad
        if countsCount[2] >= 2:
            return True
        else:
            return False

    @staticmethod
    def checkPair(hand):
        '''
        Checks hand of 7 cards for a Pair
        '''

        # Get the number of times each rank appears in hand
        cardsCount = Counter(card[0] for card in hand)
        # summarizes the number of times cards appear
        countsCount = Counter(cardsCount.values())
        # checks if a pair appears just one time
        if countsCount[2] == 1:
            return True
        else:
            return False

    @staticmethod
    def checkHighCard(hand):
        '''
        Checks hand of 7 cards for a High Card
        '''

        # Get the number of times each rank appears in hand
        cardsCount = Counter(card[0] for card in hand)
        # counts the number of counts
        countsCount = Counter(cardsCount.values())
        # checks if there are 7 unique cards
        if countsCount[1] == 7:
            return True
        else:
            return False

    @staticmethod
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
            raise ValueError(
                "Invalid hand. Must contain 7 cards, each represented as a tuple (rank, suit).")

        if Hand.checkRoyalFlush(hand):
            return 10
        if Hand.checkStraightFlush(hand):
            return 9
        if Hand.checkFourKind(hand):
            return 8
        if Hand.checkFullHouse(hand):
            return 7
        if Hand.checkFlush(hand):
            return 6
        if Hand.checkStraight(hand):
            return 5
        if Hand.checkThreeKind(hand):
            return 4
        if Hand.checkTwoPair(hand):
            return 3
        if Hand.checkPair(hand):
            return 2
        if Hand.checkHighCard(hand):
            return 1
        else:
            # Should never reach here for a valid hand
            raise ValueError("Hand did not match any known poker hand type.")

    @staticmethod
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

        # count the suits in a hand
        suitsCount = Counter([card[1] for card in hand])
        # count the ranks in a hand
        cardsCount = Counter([card[0] for card in hand])

        # royal flush
        if score == 10:
            # get the flush suit
            flushSuit = Hand.getFlushSuit(suitsCount)

            if flushSuit:
                # get the flush hand
                flushHand = Hand.getFlushHand(hand, flushSuit)

                # choose the highest 5 cards with the flush suit
                bestHand = sorted(flushHand, reverse=True)[:5]
                return bestHand

        # straight flush
        if score == 9:
            # get the flush suit
            flushSuit = Hand.getFlushSuit(suitsCount)
            if flushSuit:
                # get the flush hand
                flushHand = Hand.getFlushHand(hand, flushSuit)

                # get the unique ranks for cards in the hand
                rankSet = sorted({card[0] for card in flushHand}, reverse=True)

                # check for ace-low straight first
                if all(rank in rankSet for rank in [4, 3, 2, 1, 13]):
                    bestHand = [card for rank in [4, 3, 2, 1, 13]
                                for card in flushHand if card[0] == rank]
                    return bestHand

                else:
                    checks = len(rankSet)-4

                    # check each possible straight
                    for i, check in enumerate(range(checks)):

                        # tests the difference between the high and low card
                        # if the difference between a high and low card is 4, then it is a straight
                        if rankSet[i]-rankSet[i+4] == 4:
                            # gets the ranks of the cards in the straight
                            straightRanks = rankSet[i:i+5]
                            # creates a shell to hold card ranks that have been used
                            usedRanks = set()
                            # keeps the best cards in the straight
                            bestHand = [card for card in flushHand if card[0] in straightRanks and not (
                                card[0] in usedRanks or usedRanks.add(card[0]))]
                            return bestHand

        # four of a kind
        if score == 8:
            # get the rank of the quad card
            quadRank = [
                rank for rank in cardsCount if cardsCount[rank] == 4][0]
            # get the cards in the quad
            quadCards = [card for card in hand if card[0] == quadRank]
            # get the highest card outside of the quad
            kicker = sorted([card for card in hand if card[0]
                            != quadRank], reverse=True)[0]
            # add the kicker to the best hand
            bestHand = quadCards + [kicker]
            return bestHand

        # full house
        if score == 7:
            # gets all set ranks in the hand
            maxSet = [rank for rank in cardsCount if cardsCount[rank] == 3]
            # finds highest ranking set
            maxSetRank = max(maxSet)
            # pulls the set cards
            setCards = [card for card in hand if card[0] == maxSetRank]
            # finds second highest set or any pairs
            maxFull = [rank for rank in cardsCount if cardsCount[rank]
                       >= 2 and rank != maxSetRank]
            # finds the highest ranking set or pair
            maxFullRank = max(maxFull)
            # pulls the full pair
            fullCards = [card for card in hand if card[0] == maxFullRank]
            # combines the set and full cards
            bestHand = setCards + fullCards
            return bestHand

        # flush
        if score == 6:
            # get the flush suit
            flushSuit = Hand.getFlushSuit(suitsCount)

            if flushSuit:
                # get the flush hand
                flushHand = Hand.getFlushHand(hand, flushSuit)

                # choose the highest 5 cards with the flush suit
                bestHand = sorted(flushHand, reverse=True)[:5]
                return bestHand

        # straight
        if score == 5:
            rankSet = sorted({card[0] for card in hand}, reverse=True)

            # check for ace-low straight first
            if all(rank in rankSet for rank in [4, 3, 2, 1, 13]):
                bestHand = [card for rank in [4, 3, 2, 1, 13]
                            for card in hand if card[0] == rank]
                return bestHand

            else:
                checks = len(rankSet)-4

                # check each possible straight
                for i in range(checks):

                    # tests the difference between the high and low card
                    # if the difference between a high and low card is 4, then it is a straight
                    if rankSet[i]-rankSet[i+4] == 4:
                        # gets the ranks of the cards in the straight
                        straightRanks = rankSet[i:i+5]
                        # creates a shell to hold card ranks that have been used
                        usedRanks = set()
                        # keeps the best cards in the straight
                        bestHand = [card for card in hand if card[0] in straightRanks and not (
                            card[0] in usedRanks or usedRanks.add(card[0]))]
                        return bestHand

        # three of a kind
        if score == 4:
            # finds the rank of cards in set
            setRank = [rank for rank in cardsCount if cardsCount[rank] == 3][0]
            # pulls the set cards
            setCards = [card for card in hand if card[0] == setRank]
            # pulls highest remaining cards
            kickers = sorted([card for card in hand if card[0]
                             != setRank], reverse=True)[:2]
            # combines the set and kickers
            bestHand = setCards + kickers
            return bestHand

        # two pair
        if score == 3:
            # gets all sets in the hand
            maxPairs = sorted(
                [rank for rank in cardsCount if cardsCount[rank] == 2], reverse=True)[:2]
            # pulls the two highest ranking pairs
            pairs = [card for pair in maxPairs for card in hand if card[0] == pair]
            # finds the kicker
            kicker = sorted(
                [card for card in hand if card not in pairs], reverse=True)[0]
            # adds the kicker to the pairs
            bestHand = pairs + [kicker]
            return bestHand

        # pair
        if score == 2:
            # finds the rank of cards in set
            pairRank = [
                rank for rank in cardsCount if cardsCount[rank] == 2][0]
            # pulls the set cards
            pairCards = [card for card in hand if card[0] == pairRank]
            # pulls highest remaining cards
            kickers = sorted([card for card in hand if card[0]
                             != pairRank], reverse=True)[:3]
            # combines the set and kickers
            bestHand = pairCards + kickers
            return bestHand

        # high card
        if score == 1:
            bestHand = sorted([card for card in hand], reverse=True)[:5]
            return bestHand
        else:
            # Should never reach here for a valid hand
            raise ValueError("Hand did not match any known poker hand type.")
