# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 19:00:08 2024

@author: zshawver
"""

import pygame

class Card:
    def __init__(self, x, y, image, scale):
        self.x = x
        self.y = y
        self.scale = scale
        # get image size
        self.width = image.get_width()
        self.height = image.get_height()
        # load image and rescale it
        self.image = pygame.transform.scale(image, (int(self.width * scale), int(self.height * scale)))
        # create a rectangle object for the image
        self.rect = self.image.get_rect()
        # give the coordinates for where to place the image/rectangle
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        # draw card on screen
        surface.blit(self.image, self.rect.topleft)

    def setPos(self, x, y):
        self.x = x
        self.y = y
        self.rect.center = (self.x, self.y)

    def getWidth(self):
        return int(self.width*self.scale)

    def getHeight(self):
        return int(self.height*self.scale)