# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 12:14:36 2024

@author: zshawver
"""
from card import Card

class Deck:
    def __init__(self, x, y, image, scale, num_cards, offset):
        self.cards = []
        self.x = x
        self.y = y
        for i in range(num_cards):
            card_x = x + i * offset[0]
            card_y = y + i * offset[1]
            card = Card(card_x, card_y, image, scale)
            self.cards.append(card)
    
    def draw(self, surface):
        for card in self.cards:
            card.draw(surface)
    
    def setPos(self,x,y):
        self.x = x
        self.y = y
    
    def getWidth(self):
        if self.cards:
            return self.cards[0].getWidth()  # Assuming all cards in the deck have the same width after scaling
        return 0  # Handle case when there are no cards in the deck