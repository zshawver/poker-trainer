# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 15:03:44 2024

@author: zshawver
"""
from utils import calculate_points_from_start, draw_oval_points

class Table:
    def __init__(self):
        self.players = [] #An empty list to receive players at the table
    
    def addPlayer(self,Player):
        self.players.append(Player) #Add a player at the table
    
    def removePlayer(self,Player):
        self.players.remove(Player)
    
    def layout_players_oval(self, center_x, center_y, radius_x, radius_y, start_angle=0):
        num_players = len(self.players)
        return calculate_points_from_start(center_x, center_y, radius_x, radius_y, num_players, start_angle)

    def draw_player_positions(self, window, points):
        draw_oval_points(window, points)