# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 10:31:02 2024

@author: zshawver
"""

    # #identifies the type of hand the player was dealt
    # draw = [draw for draw in rangeHands for sublist in rangeHands[draw] if all(card in sublist for card in hole)][0]


    # #converts the card tuples into a list of card symbols for printing
    # holeSymbols = [deckSymbols[card] for card in hole]
    
    # print("Hole is {} {}, which is {}".format(holeSymbols[0],holeSymbols[1],draw))
    
    #next gives the first available item in an iterable that satisifes a condition
    #if the condition isn't satisfied, then you tell it what to give instead
    #here, it gives the best possible range or fold if the draw doesn't appear in any ranges
    # bestRange = next((name for name, r in ranges.items() if draw in r), 'fold')


    '''
    3) give feedback on range decision
    '''
    
    # # Create the plot and get the image buffer
    # rangePlot = create_plot(handsList)

    # # Load the image from the buffer
    # rangeImage = pygame.image.load(rangePlot)
    # rangePosition = rangeImage.get_rect(center=(windowSize[0] // 2, windowSize[1] // 2))

    # # Fill the background
    # window.fill(bgColor)

    # # Blit the plot image onto the background
    # window.blit(rangeImage, rangePosition)

    # # Update the display
    # pygame.display.flip()
