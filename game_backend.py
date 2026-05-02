from hand import Hand
from player import Player
from table import Table
from positions import Positions
from gameStates import GameStateManager, StartState, DealState, HoleState, FlopState, TurnState, RiverState

class Game:
    def __init__(self,players):

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



    def setupPlayers(self,players_data):
        for playerDatum in players_data:
            player = Player(playerDatum[0], playerDatum[1],playerDatum[2])
            self.table.addPlayer(player)
            if player.keyPlayer:
                self.keyPlayer = player

        self.players = self.table.players

    def assignPositionsInHand(self):
        for i, player in enumerate(self.players):
            player.tablePosition = self.positions[i]

    def newHand(self):
        self.updateTable() #Check status of players at the table
        self.hand.newHand() #Reset the hand
        #Deal all cards to players/community in backend
        self.hand.dealHole()
        self.hand.dealFlop()
        self.hand.dealTurn()
        self.hand.dealRiver()



    def updateTable(self):
        numPlayers = len(self.table.players) #Number of players currently at the table
        self.table.players = [player for player in self.table.players if player.chips > 0] # Remove players with zero chips

        # Reset positions if players have been removed
        if len(self.table.players) != numPlayers:
            self.positions = Positions[len(self.table.players)] #Reset the positions at the table based on number of players
            self.assignPositionsInHand()

        else: #Only shift positions and button points if the number of players is the same
            self.positions.insert(0,self.positions.pop()) #Shift the positions at the table
            # self.buttonPoints.append(self.buttonPoints.pop(0)) #Shift where the dealer button will be drawn next hand
            self.assignPositionsInHand() #Sets the position for each player

    def run(self):
        pass
