# -*- coding: utf-8 -*-
"""
Created on Mon Jun 17 10:56:29 2024

@author: zshawver
"""

from hole import Hole

import pygame

# Initialize Pygame
pygame.init()

# Set up display
screen = pygame.display.set_mode((1500, 700))

# Load card images
card1Img = pygame.image.load('cards//13_2.png')
card2Img = pygame.image.load('cards//13_4.png')

# Create a Hole object
hole = Hole(x=400, y=300, card1Img=card1Img, card2Img=card2Img, scale=.5)



# Main game loop
running = True
while running:# and iteration_count < max_iterations:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Clear the screen
    screen.fill((0, 0, 0))
    
    # Draw the hole cards
    hole.draw(screen)
    
    # Update the display
    pygame.display.flip()


# Quit Pygame
pygame.quit()

'''

import pygame
from button import Button



# Initialize Pygame
pygame.init()

# Set up the display
windowSize = (800, 600)
window = pygame.display.set_mode(windowSize)
pygame.display.set_caption('Pygame Tutorial')

# Load the image
image = pygame.image.load('13_4.png')


#Initialize Button
buttonImage = pygame.image.load('button.png')
nextButton = Button(windowSize[0]//2,5*windowSize[1]//6,buttonImage,.4)




#Resize the image

scale = 3 #Amount to resize the image
imageSize = (image.get_width()//scale,image.get_height()//scale) #Specify new image size
image = pygame.transform.scale(image, imageSize) #Resize the image

# Calculate the center positions for the left and right images

#Left image placed at 1/3 of the window width, centered vertically
imageLeftPosition = image.get_rect(center=(windowSize[0]//3,windowSize[1]//2))
#Right image placed at 2/3 of the window width, centered vertically
imageRightPosition = image.get_rect(center=(2*windowSize[0]//3,windowSize[1]//2))


# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Fill the window with a color
    window.fill('#247345')  
    if nextButton.draw():
        print('click')

    # Blit the images to the window
    window.blit(image, imageLeftPosition)
    # window.blit(image,imageRightPosition)

    # Update the display
    pygame.display.flip()

# Quit Pygame
pygame.quit()


# import sys
# import pygame as pg

# BG_COLOR = pg.Color(80, 60, 70)
# PLAYER_COLOR = pg.Color(90, 140, 190)

# def main():
#     screen = pg.display.set_mode((640, 480))
#     clock = pg.time.Clock()

#     player_img = pg.Surface((40, 60))
#     player_img.fill(PLAYER_COLOR)
#     # Create a rect with the size of the image/pygame.Surface
#     # and immediately set it's topleft coords to (100, 300).
#     player_rect = player_img.get_rect(topleft=(100, 300))

#     done = False

#     while not done:
#         for event in pg.event.get():
#             if event.type == pg.QUIT:
#                 done = True
#             if event.type == pg.KEYDOWN:
#                 if event.key == pg.K_d:
#                     # Set the center to these new coords.
#                     player_rect.center = (400, 200)
#                 if event.key == pg.K_a:
#                     # Set the x coord to 300.
#                     player_rect.x = 300

#         screen.fill(BG_COLOR)
#         screen.blit(player_img, player_rect)
#         pg.display.flip()
#         clock.tick(30)


# if __name__ == '__main__':
#     pg.init()
#     main()
#     pg.quit()
#     sys.exit()
'''