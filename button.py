# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 08:29:22 2024

@author: zshawver
"""
import pygame

class Button():
    def __init__(self,x,y,image,scale):
        
        #get image size
        width = image.get_width()
        height = image.get_height()
        #load image and rescale it
        self.image = pygame.transform.scale(image,(int(width*scale),int(height*scale)))
        self.width = int(width*scale)
        self.height = int(height*scale)
        #create a rectangle object for the image
        self.rect = self.image.get_rect()
        #give the coordinates for where to place the image/rectangle
        self.rect.center = (x,y)
        #Creates a state to receive clicks
        self.clicked = None
        
    def draw(self,surface):
        #creates a variable that registers whether an action has been taken
        action = False
        
        #get mouse position
        pos = pygame.mouse.get_pos()
        
        #check if mouse is overtop the button
        if self.rect.collidepoint(pos):
            #check if button is clicked
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked==False:
                #Registers a sigle click
                self.clicked = True
                #The action is whether the button has been clicked
                action = True
        
        #After a click, returns the button to unclicked state
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False
        
        #draw button on screen
        surface.blit(self.image, (self.rect.x, self.rect.y))
        
        return action
    def drawOnce(self, surface):
        if not self.clicked:
            if self.draw(surface):
                self.clicked = True

    def reset(self):
        self.clicked = False
    
    def drawStatic(self,surface):
        #draw button on screen
        surface.blit(self.image, (self.rect.x, self.rect.y))
        
    def updatePosition(self, x, y):
        self.rect.center = (x, y)