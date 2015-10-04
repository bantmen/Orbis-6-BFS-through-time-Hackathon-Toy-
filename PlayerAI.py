from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.MapOutOfBoundsException import *

import time
from copy import deepcopy

SAFE, UNSAFE = 1, 0

def timeit(method):

    def timed(*args, **kw):
        ts = int(round(time.time() * 1000))
        result = method(*args, **kw)
        te = int(round(time.time() * 1000))

        print('%r ran in %.0f ms'%(method.__name__, te-ts))
        return result

    return timed

class PlayerAI:
    def __init__(self):
        pass

    @timeit
    def get_move(self, gameboard, player, opponent):
        curr_turn = gameboard.current_turn

        safeboard = [[SAFE for i in range(gameboard.height)] for j in range(gameboard.width)]
        #fill walls
        walls = gameboard.walls
        for wall in walls:
            safeboard[wall.x][wall.y] = UNSAFE
        #fill turrets
        turs = gameboard.turrets
        for tur in turs:
            safeboard[tur.x][tur.y] = UNSAFE

        base_matrix = deepcopy(safeboard)
        n_futures = []
        bulls = gameboard.bullets

        #generate time series
        for t in range(n):
            safe_spots = deepcopy(base_matrix)
            
            #update bullets
            to_pop = []
            for i in range(len(bulls)):
                if bulls[i].direction == Direction.LEFT:
                    dx, dy = -1, 0
                elif bulls[i].direction == Direction.RIGHT:
                    dx, dy = 1, 0
                elif bulls[i].direction == Direction.DOWN:
                    dx, dy = 0, 1
                else: #UP
                    dx, dy = 0, -1

                if safe_spots[(bull.x+dx)%gameboard.height][(bull.y+dy)%gameboard.width] == UNSAFE:
                    to_pop.append(i)

            this_turn = curr_turn + t
            #laser
            for tur in turs:
                if this_turn%(tur.fire_time + tur.cooldown_time) < tur.fire_time:
                    #CHECK IF IT'S ALIVE
                    
                    #go up
                    x = tur.x
                    y = (tur.y + 1)%gameboard.height
                    while (not gameboard.is_wall_at_tile(x, y)) and (not gameboard.is_turret_at_tile(x, y)):
                        safe_spots[x][y] = UNSAFE
                        y = (y + 1) % gameboard.height

                    #go down
                    x = tur.x
                    y = (tur.y - 1)%gameboard.height
                    while (not gameboard.is_wall_at_tile(x, y)) and (not gameboard.is_turret_at_tile(x, y)):
                        safe_spots[x][y] = UNSAFE
                        y = (y - 1) % gameboard.height

                    #go left
                    y = tur.y
                    x = (tur.x + 1)%gameboard.width
                    while (not gameboard.is_wall_at_tile(x, y)) and (not gameboard.is_turret_at_tile(x, y)):
                        safe_spots[x][y] = UNSAFE
                        x = (x + 1) % gameboard.width

                    #go right
                    y = tur.y
                    x = (tur.x - 1)%gameboard.width
                    while (not gameboard.is_wall_at_tile(x, y)) and (not gameboard.is_turret_at_tile(x, y)):
                        safe_spots[x][y] = UNSAFE
                        x = (x - 1) % gameboard.width

            #fill bullets
            for bull in bulls:
                if bull.direction == Direction.LEFT:
                    dx, dy = -1, 0
                elif bull.direction == Direction.RIGHT:
                    dx, dy = 1, 0
                elif bull.direction == Direction.DOWN:
                    dx, dy = 0, 1
                else: #UP
                    dx, dy = 0, -1
                bull.x = (bull.x+dx)%gameboard.height
                bull.y = (bull.y+dy)%gameboard.width
                safe_spots[bull.x][bull.y] = UNSAFE


            #pop dead bullets
            temp = []
            for c in range(len(bulls)):
                if c not in to_pop:
                    temp.append(bulls[c])
            bulls = temp

            n_futures.append(safe_spots)

        return Move.NONE

