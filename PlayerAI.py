from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.MapOutOfBoundsException import *

import time
from copy import deepcopy
from Queue import Queue

SAFE, UNSAFE = 1, 0

def timeit(method):
    def timed(*args, **kw):
        ts = int(round(time.time() * 1000))
        result = method(*args, **kw)
        te = int(round(time.time() * 1000))

        print('%r ran in %.0f ms'%(method.__name__, te-ts))
        return result
    return timed

class Node:
    def __init__(self, x, y, direction, time, can_rotate):
        self.x = x
        self.y = y
        self.direction = direction
        self.time = time
        self.can_rotate = can_rotate

def change_direction(x, y, direction, total_height, total_width):
    if direction == Direction.LEFT:
        dx, dy = -1, 0
    elif direction == Direction.RIGHT:
        dx, dy = 1, 0
    elif direction == Direction.DOWN:
        dx, dy = 0, 1
    else: #UP
        dx, dy = 0, -1

    return (x+dx) % total_height, (x+dy) % total_width

class PlayerAI:
    def __init__(self):
        pass

    def get_n_futures(self, n):
        return

    def target_closest_point(self, player, gameboard):
        n_futures = self.get_n_futures(10)

        q = Queue()
        q.put(Node(player.x, player.y, player.direction, 0, True))

        while not q.empty():
            cur_node = q.get()

            if gameboard.power_up_at_tile[cur_node.x][cur_node.y]: # generalize it to any point
                return cur_node.x, cur_node.y # fix!

            new_x, new_y = change_direction(cur_node.x, cur_node.y, cur_node.position, gameboard.height, gameboard.width)

            if n_futures[cur_node.time][new_x][new_y] == SAFE:
                q.put(Node(new_x, new_y, cur_node.position, cur_node.time+1, True))

            if cur_node.can_rotate:
                for dirr in [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]:
                    if dirr != cur_node.direction:
                        q.put(Node(cur_node.x, cur_node.y, dirr, cur_node.time+1, False))

        return -1, -1


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
                bull.x, bull.y = change_direction(bull.x, bull.y, bull.direction, gameboard.width, gameboard.height)
                safe_spots[bull.x][bull.y] = UNSAFE


            #pop dead bullets
            temp = []
            for c in range(len(bulls)):
                if c not in to_pop:
                    temp.append(bulls[c])
            bulls = temp

            n_futures.append(safe_spots)

        return Move.NONE