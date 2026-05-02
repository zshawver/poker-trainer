# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 14:58:48 2024

@author: zshawver
"""

from card import Card

class Hole:
    def __init__(self, x, y, card1Img, card2Img, scale, space_px=10):
        # Use game.points from game.calculatePlayerLocations()
        self.x = x
        self.y = y

        # Create Cards from images
        self.leftCard = Card(self.x, self.y, card1Img, scale)
        self.rightCard = Card(self.x, self.y, card2Img, scale)

        # Establish the horizontal location of where the cards will be
        self.cardWidth = self.leftCard.getWidth()
        self.cardHeight = self.leftCard.getHeight()
        leftX = self.x - (self.leftCard.rect.width / 2) - (space_px / 2)
        rightX = self.x + (self.rightCard.rect.width / 2) + (space_px / 2)
        self.leftCard.setPos(leftX, self.y)
        self.rightCard.setPos(rightX, self.y)

        # Put the cards in a list
        self.cards = [self.leftCard, self.rightCard]
    
    def getRightEdgeX(self):
        # Calculate and return the X coordinate of the right-most edge of the right card
        right_center_x = self.rightCard.rect.centerx
        right_edge_x = right_center_x + (self.rightCard.rect.width / 2)
        return right_edge_x

    def draw(self, surface):
        for card in self.cards:
            card.draw(surface)
