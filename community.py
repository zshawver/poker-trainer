# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 18:42:17 2024

@author: zshawver
"""

from card import Card

class Community:
    def __init__(self, x, y, images, scale, spacing):
        spaces = [x + i*spacing for i in range(len(images))]
        self.cards = [Card(spaces[i],y, image, scale) for i,image in enumerate(images)]

    def draw(self, surface):
        for card in self.cards:
            card.draw(surface)