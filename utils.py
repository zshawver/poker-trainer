# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 11:02:15 2024

@author: zshawver
"""
import pygame
import math

def calculate_points_from_start(center_x, center_y, radius_x, radius_y, num_players, start_angle=0):
    points = []
    angle_step = 2 * math.pi / num_players
    
    for i in range(num_players):
        theta = start_angle + i * angle_step
        x = center_x + radius_x * math.cos(theta)
        y = center_y + radius_y * math.sin(theta)
        points.append((x, y))
    
    return points
def draw_oval_points(window, points):
    for i, point in enumerate(points):
        color = (0, 0, 255) if i == 0 else (255, 0, 0)  # Make the first point blue
        pygame.draw.circle(window, color, (int(point[0]), int(point[1])), 10)