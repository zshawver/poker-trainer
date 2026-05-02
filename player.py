# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 15:03:07 2024

@author: zshawver
"""

class Player:
    def __init__(self,buyIn,name,keyPlayer = False):
        self.name = name #Give the player a name
        self.chips = buyIn #Give the player some chips
        self.hand = [] #An empty list to receive cards
        self.bestHand = [] #An empty list to receive best hand for score
        self.score = None #Score at beginning of each hand
        self.keyPlayer = keyPlayer
        self.tablePosition = None
        self.playerLocation = None
        self.buttonLocation = None