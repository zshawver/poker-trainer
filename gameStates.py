# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 10:21:24 2024

@author: zshawver
"""
from deck import Deck
from community import Community

class GameStateManager:
    def __init__(self, currentState):
        self.currentState = currentState
    def getState(self):
        return self.currentState
    def setState(self,state):
        self.currentState = state

class StartState:
    def __init__(self, gameStateManager):
        self.gameStateManager = gameStateManager
    def run(self, game):
        if game.startButton.draw(game.window):
            self.gameStateManager.setState('deal')

class DealState:
    def __init__(self,gameStateManager):
        self.gameStateManager = gameStateManager
    def run(self, game):
        game.deckImage.draw(game.window)
        if game.dealHandsButton.draw(game.window):
            game.newHand()
            self.gameStateManager.setState('hole')
            game.resetActionButtons()

class HoleState:
    def __init__(self,gameStateManager):
        self.gameStateManager = gameStateManager
    def run(self, game):
        game.deckImage.draw(game.window) #Draw a deck
        game.drawHoles()
        game.dealerButton.drawStatic(game.window)
        game.drawActionButtons(game.window)
        if game.foldButton.draw(game.window):
            self.gameStateManager.setState('deal')
            game.resetDeckButtons()
        if game.dealFlopButton.draw(game.window):
            self.gameStateManager.setState('flop')
            game.resetActionButtons()

class FlopState:
    def __init__(self,gameStateManager):
        self.gameStateManager = gameStateManager
    def run(self, game):
        game.deckImage.draw(game.window) #Draw a deck
        game.drawHoles() #Draw dealt cards to each player
        game.burn = Deck(game.burnXPosition,game.deck_position[1], game.backImage, game.deckScale, 1, (1, -1)) #Create image of burn cards
        game.burn.draw(game.window) #Draw burnt Cards
        game.community = Community(game.communityX,game.centerY,game.flopImages,game.communityScale,game.communitySpacing)
        game.community.draw(game.window)
        game.dealerButton.drawStatic(game.window)
        game.drawActionButtons(game.window)
        if game.foldButton.draw(game.window):
            self.gameStateManager.setState('deal')
            game.resetDeckButtons()
        if game.dealTurnButton.draw(game.window):
            self.gameStateManager.setState('turn')
            game.resetActionButtons()

class TurnState:
    def __init__(self,gameStateManager):
        self.gameStateManager = gameStateManager
    def run(self, game):
        game.deckImage.draw(game.window) #Draw a deck
        game.drawHoles()
        game.burn = Deck(game.burnXPosition,game.deck_position[1], game.backImage, game.deckScale, 2, (1, -1)) #Create image of burn cards
        game.burn.draw(game.window) #Draw burnt Cards
        game.community = Community(game.communityX,game.centerY,game.turnImages,game.communityScale,game.communitySpacing)
        game.community.draw(game.window)
        game.dealerButton.drawStatic(game.window)
        game.drawActionButtons(game.window)
        if game.foldButton.draw(game.window):
            self.gameStateManager.setState('deal')
            game.resetDeckButtons()
        if game.dealRiverButton.draw(game.window):
            self.gameStateManager.setState('river')
            game.resetActionButtons()
        
class RiverState:
    def __init__(self,gameStateManager):
        self.gameStateManager = gameStateManager
    def run(self, game):
        game.deckImage.draw(game.window) #Draw a deck
        game.drawHoles()
        game.burn = Deck(game.burnXPosition,game.deck_position[1], game.backImage, game.deckScale, 3, (1, -1)) #Create image of burn cards
        game.burn.draw(game.window) #Draw burnt Cards
        game.community = Community(game.communityX,game.centerY,game.riverImages,game.communityScale,game.communitySpacing)
        game.community.draw(game.window)
        game.dealerButton.drawStatic(game.window)
        game.drawActionButtons(game.window)
        if game.foldButton.draw(game.window):
            self.gameStateManager.setState('deal')
            game.resetDeckButtons()
        if game.nextHandButton.draw(game.window):
            self.gameStateManager.setState('deal')
            game.resetActionButtons()