from game import Game
import ctypes

user32 = ctypes.windll.user32

players = [
    [1000, 'Callan', True],
    [1000, 'Simon', False],
    [1000, 'Frankie',False],
    [1000, 'Byron',False],
    [1000, 'Wynn',False],
    [1000, 'Royal',False]
]

#~~#Set display variables#~~#
WIDTH, HEIGHT = user32.GetSystemMetrics(0)*.95, user32.GetSystemMetrics(1)*.95 #1000, 700 #Set the window size

if __name__ == "__main__":
    game = Game(players,WIDTH,HEIGHT)
    game.run()