from button import Button
from card import Card
from hole import Hole
from deck import Deck
from hand import Hand
from player import Player
from table import Table
from positions import Positions
from gameStates import GameStateManager, StartState, DealState, HoleState, FlopState, TurnState, RiverState

import pygame
from math import cos, pi, sin
import os

class Game:
    def __init__(self,players,WIDTH,HEIGHT):
        pygame.init()
        #~~#Window Variables#~~#
        flags = pygame.RESIZABLE
        self.window = pygame.display.set_mode((WIDTH,HEIGHT),flags) #Create the window
        self.centerX = WIDTH // 2
        self.centerY = HEIGHT // 2
        self.width = WIDTH
        self.height = HEIGHT
        self.bgColor = ('#247345') #BG color is green felt
        self.clock = pygame.time.Clock() #Pygame Timing

        #~~#Spacing Variables#~~#
        self.keyPlayerScale = .45
        self.playerScale = .3
        self.actionButtonScale = .7
        self.cardSpacing = 10 #How much space appears between cards
        self.deckScale = 0.35 #Scale size of Deck
        self.communityScale = .5 #Size of community cards
        self.deck_position = (0.07 * WIDTH,HEIGHT - 0.15 * HEIGHT) #7% in from the left, 10% up from the bottom

        #~~#Initialize Game Objects/Features#~~#
        #Gameplay variables
        self.table = Table() #Create the poker Table instance
        self.hand = None #Create an empty variable for a Hand at the Table
        self.players = []
        self.setupPlayers(players) #Add a list of players to that table
        self.setupGameObjects() #Create instances of game objects
        self.positions = Positions[len(self.players)] #Retrieve positions at the table based on number of players
        self.assignPositionsInHand() #Assign each player's starting location

        #On-screen location variables
        self.burn = None
        self.community = None

        #Game state variables
        self.gameStateManager = GameStateManager('start') #Load in the game state manager to begin the game in the 'start' state

        #Initialize the states
        self.startState = StartState(self.gameStateManager)
        self.dealState = DealState(self.gameStateManager)
        self.holeState = HoleState(self.gameStateManager)
        self.flopState = FlopState(self.gameStateManager)
        self.turnState = TurnState(self.gameStateManager)
        self.riverState = RiverState(self.gameStateManager)
        self.states = {
            'start':self.startState,
            'deal':self.dealState,
            'hole':self.holeState,
            'flop':self.flopState,
            'turn':self.turnState,
            'river':self.riverState
            }

    def setupGameObjects(self):
        '''
        Loads in & creates key objects used in game play.
        '''
        #~~#Table, Hand, & Players#~~#
        self.hand = Hand(self.table,self) #Create an instance of Hand at the Table
        self.backImage = pygame.image.load('cards\\back.png')  #Image for card back
        self.dealerButtonImage = pygame.image.load('dealerButton.png') #Image of circular Button that "D"
        self.dealerButtonPos = (0,0)
        self.dealerButton = Button(self.dealerButtonPos[0],self.dealerButtonPos[1],self.dealerButtonImage,.1)
        self.calculatePlayerLocations(-90) #Establish where players' cards will be drawn
        self.calculateDealerButtonLocations() #Establish where Dealer button will be drawn

        #~~#Image Files#~~#
        self.startButtonImage = pygame.image.load('startButton.png')  #Image of Button that says "Next Hand"
        self.nextButtonImage = pygame.image.load('nextHandButton.png')  #Image of Button that says "Next Hand"
        self.dealHandsButtonImage = pygame.image.load('dealHands.png') #Image of Button that says "Deal Hands"
        self.dealFlopButtonImage = pygame.image.load('dealFlop.png') #Image of Button that says "Deal Flop"
        self.dealTurnButtonImage = pygame.image.load('dealTurn.png') #Image of Button that says "Deal Turn"
        self.dealRiverButtonImage = pygame.image.load('dealRiver.png') #Image of Button that says "Deal River"
        self.raiseButtonImage = pygame.image.load('raiseButton.png') #Image of Button that says "Raise"
        self.callButtonImage = pygame.image.load('callButton.png') #Image of Button that says "Raise"
        self.foldButtonImage = pygame.image.load('foldButton.png') #Image of Button that says "Raise"

        #~~#Images Variables#~~#

        self.deckImage = Deck(self.deck_position[0],self.deck_position[1], self.backImage, self.deckScale, 7, (1, -1))  # Create appearance of deck with by drawing Cards atop each other, slightly offset
        self.burnXPosition = self.deckImage.x + self.deckImage.getWidth() + self.cardSpacing  # Calculate burn position based on deck

        self.getCommunityX() #Figure out where the left-most community card should be drawn

        self.getDeckButtonPos() #Set where the deck buttons will be drawn
        self.getActionButtonPos() #Set where the action buttons will be drawn

        #~~#Button Objects#~~#
        self.startButton = Button(self.centerX,self.centerY,self.startButtonImage,.4)
        self.nextHandButton = Button(self.deckButtonX,self.deckButtonY,self.nextButtonImage,.4)
        self.dealHandsButton = Button(self.deckButtonX,self.deckButtonY,self.dealHandsButtonImage,.4)
        self.dealFlopButton = Button(self.deckButtonX,self.deckButtonY,self.dealFlopButtonImage,.4)
        self.dealTurnButton = Button(self.deckButtonX,self.deckButtonY,self.dealTurnButtonImage,.4)
        self.dealRiverButton = Button(self.deckButtonX,self.deckButtonY,self.dealRiverButtonImage,.4)
        self.raiseButton = Button(self.actionButtonPos[0][0],self.actionButtonPos[0][1],self.raiseButtonImage, self.actionButtonScale)
        self.callButton = Button(self.actionButtonPos[1][0],self.actionButtonPos[1][1],self.callButtonImage, self.actionButtonScale)
        self.foldButton = Button(self.actionButtonPos[2][0],self.actionButtonPos[2][1],self.foldButtonImage, self.actionButtonScale)

    def setupPlayers(self,players_data):
        for playerDatum in players_data:
            player = Player(playerDatum[0], playerDatum[1],playerDatum[2])
            self.table.addPlayer(player)
            if player.keyPlayer:
                self.keyPlayer = player

        self.players = self.table.players

    def getCommunityX(self):
        tempCard = Card(0,0,self.backImage,self.communityScale)
        cardWidth = tempCard.getWidth()
        communityWidth = (cardWidth*5)+(self.cardSpacing*4)
        self.communitySpacing = cardWidth + (self.cardSpacing)
        self.communityX = self.centerX - (communityWidth // 2) + (cardWidth // 2)

    def getDeckButtonPos(self):
        tempCard = Card(0,0,self.backImage,self.deckScale)
        cardHeight = tempCard.getHeight()
        self.deckButtonY = self.deck_position[1] - cardHeight - self.cardSpacing //2
        self.deckButtonX = self.deckImage.x + (self.deckImage.getWidth()//2) + (self.cardSpacing//2)

    def getActionButtonPos(self):
        hole = Hole(self.keyPlayer.playerLocation[0],self.keyPlayer.playerLocation[1],self.backImage,self.backImage,self.keyPlayerScale)
        tempButton = Button(0,0,self.raiseButtonImage, self.actionButtonScale)
        rightEdge = hole.getRightEdgeX()
        self.actionButtonY = hole.rightCard.y #The y position of the key player's hole
        ySpace = tempButton.height   + (self.cardSpacing//2)
        actionButtonX = rightEdge + self.cardSpacing + (tempButton.width // 2)
        self.actionButtonPos = ((actionButtonX,hole.rightCard.y-ySpace),(actionButtonX,hole.rightCard.y),(actionButtonX,hole.rightCard.y+ySpace))

    def drawActionButtons(self,surface):
        self.raiseButton.drawOnce(surface)
        self.callButton.drawOnce(surface)

    def resetActionButtons(self):
        self.raiseButton.reset()
        self.callButton.reset()

    def resetDeckButtons(self):
        self.nextHandButton.clicked = None
        self.dealHandsButton.clicked = None
        self.dealFlopButton.clicked = None
        self.dealTurnButton.clicked = None
        self.dealRiverButton.clicked = None

    def calculatePlayerLocations(self, start_angle=0):
        '''
        Calculates positions of players around an ellipse.

        Parameters
        ----------
        start_angle : float, optional
            The starting angle in degrees for the first player. Default is 0 degrees.
        '''
        radiusX, radiusY = int(self.width* 0.4), int(self.height* 0.4)
        angle_step = 2 * pi / len(self.players)

        for i,player in enumerate(self.players):
            theta = start_angle - i * angle_step
            x = int(self.centerX + radiusX * cos(theta))
            y = int(self.centerY - radiusY * sin(theta))  # Reverse y-axis for pygame
            player.playerLocation = (x, y)

    def calculateDealerButtonLocations(self):

        for player in self.players:
            if player.keyPlayer:
                tempCard = Card(player.playerLocation[0],player.playerLocation[1],self.backImage,self.keyPlayerScale)
            else:
                tempCard = Card(player.playerLocation[0],player.playerLocation[1],self.backImage,self.playerScale)

            height = tempCard.getHeight()

            space = height//2 + self.cardSpacing//2 + self.dealerButton.height//2

            player.buttonLocation = (player.playerLocation[0],player.playerLocation[1]-space)

    def assignPositionsInHand(self):
        for i, player in enumerate(self.players):
            player.tablePosition = self.positions[i]

    def drawHoles(self):
        '''
        Draws hole cards for each player at their calculated positions on the screen.
        Key player is drawn with actual cards, others with back images.
        '''

        for i, player in enumerate(self.players):
            hole_position = player.playerLocation # Get the position for the current player

            if player.keyPlayer:
                # Draw actual hole cards for the key player
                fnLeft = "{}_{}".format(player.hand[0][0],player.hand[0][1])
                fnRight = "{}_{}".format(player.hand[1][0],player.hand[1][1])
                # print(player.hand[0],player.hand[1])
                leftCardImage = pygame.image.load(os.path.join('cards', fnLeft + '.png'))
                rightCardImage = pygame.image.load(os.path.join('cards', fnRight + '.png'))
                scale = self.keyPlayerScale
            else:
                # Draw back images for other players
                leftCardImage = self.backImage
                rightCardImage = self.backImage
                scale = self.playerScale

            hole = Hole(hole_position[0], hole_position[1], leftCardImage, rightCardImage, scale)
            hole.draw(self.window)  # Draw the hole cards or back images on the window

    def newHand(self):
        self.updateTable() #Check status of players at the table
        self.hand.newHand() #Reset the hand
        #Deal all cards to players/community in backend
        self.hand.dealHole()
        flop = self.hand.dealFlop()
        turnCard = self.hand.dealTurn()
        turn = flop + [turnCard]
        riverCard = self.hand.dealRiver()
        river = turn + [riverCard]

        #Prepare community card images
        self.flopImages = [pygame.image.load(os.path.join('cards',"{}_{}.png".format(card[0],card[1]))) for card in flop]
        self.turnImages = [pygame.image.load(os.path.join('cards',"{}_{}.png".format(card[0],card[1]))) for card in turn]
        self.riverImages = [pygame.image.load(os.path.join('cards',"{}_{}.png".format(card[0],card[1]))) for card in river]

        self.dealerButtonPos = next(player.buttonLocation for player in self.players if player.tablePosition.lower() == 'btn') #Set where the dealer button will be drawn the next hand
        self.dealerButton.updatePosition(self.dealerButtonPos[0], self.dealerButtonPos[1])  # Update dealer button position

    def updateTable(self):
        numPlayers = len(self.table.players) #Number of players currently at the table
        self.table.players = [player for player in self.table.players if player.chips > 0] # Remove players with zero chips

        # Reset positions if players have been removed
        if len(self.table.players) != numPlayers:
            self.points = [] #Reset player location points
            self.buttonPoints = [] #Reset dealer button points
            self.calculatePlayerLocations(start_angle=-45) #Recalculate where players' cards will be drawn
            self.calculateDealerButtonLocations() #Recalculate where the dealer button will be drawn
            self.positions = Positions[len(self.table.players)] #Reset the positions at the table based on number of players
            self.assignPositionsInHand()

        else: #Only shift positions and button points if the number of players is the same
            self.positions.insert(0,self.positions.pop()) #Shift the positions at the table
            # self.buttonPoints.append(self.buttonPoints.pop(0)) #Shift where the dealer button will be drawn next hand
            self.assignPositionsInHand() #Sets the position for each player

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.window.fill(self.bgColor)

            state = self.gameStateManager.getState()
            self.states[state].run(self)

            pygame.display.update()
        pygame.quit()
