from PythonClientAPI.libs.Game.Enums import *
from PythonClientAPI.libs.Game.MapOutOfBoundsException import *

import time
from copy import deepcopy
from queue import Queue

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
    def __init__(self, x, y, direction, time, can_rotate, traveled, initial_d, next_moves = 0):
        self.x = x
        self.y = y
        self.direction = direction
        self.time = time
        self.can_rotate = can_rotate
        self.traveled = {} 
        self.initial_d = initial_d
        self.next_moves = next_moves

def change_direction(x, y, direction, total_height, total_width):
    if direction == Direction.LEFT:
        dx, dy = -1, 0
    elif direction == Direction.RIGHT:
        dx, dy = 1, 0
    elif direction == Direction.DOWN:
        dx, dy = 0, 1
    else: #UP
        dx, dy = 0, -1

    return (x+dx) % total_width, (y+dy) % total_height

@timeit
def in_turret_contact(node, gameboard):
    #results = []

    #go up
    x = node.x
    y = (node.y + 1)%gameboard.height
    while (not gameboard.is_wall_at_tile(x, y)):
        if gameboard.is_turret_at_tile(x, y):
            return Direction.UP
        y = (y + 1) % gameboard.height

    #go down
    x = node.x
    y = (node.y - 1)%gameboard.height
    while (not gameboard.is_wall_at_tile(x, y)):
        if gameboard.is_turret_at_tile(x, y):
            return Direction.DOWN
        y = (y - 1) % gameboard.height

    #go left
    y = node.y
    x = (node.x + 1)%gameboard.width
    while (not gameboard.is_wall_at_tile(x, y)):
        if gameboard.is_turret_at_tile(x, y):
            return Direction.LEFT
        x = (x + 1) % gameboard.width

    #go right
    y = node.y
    x = (node.x - 1)%gameboard.width
    while (not gameboard.is_wall_at_tile(x, y)):
        if gameboard.is_turret_at_tile(x, y):
            return Direction.RIGHT
        x = (x - 1) % gameboard.width

    return None


class PlayerAI:
    def __init__(self):
        self.hardcoded = [Move.FORWARD, Move.FACE_DOWN, Move.FORWARD, Move.FORWARD, Move.FACE_RIGHT, Move.FORWARD, Move.FORWARD, Move.FACE_UP, Move.FORWARD, Move.FORWARD, Move.FACE_RIGHT, Move.FORWARD]
        self.hardcoded_i = -1

    @timeit
    def target_closest_point(self, player, gameboard, n, n_futures):
        q = Queue()
        q.put(Node(player.x, player.y, player.direction, 0, True, dict(), None))

        while not q.empty():
            cur_node = q.get()
            #print(cur_node.x, cur_node.y)

            if cur_node.time >= n-1:
                continue

            if gameboard.power_up_at_tile[cur_node.x][cur_node.y]: # generalize it to any point
                # return cur_node.x, cur_node.y # fix!
                return cur_node.initial_d

            turret_dirr = in_turret_contact(cur_node, gameboard)
            if turret_dirr:
                if turret_dirr != cur_node.direction: # need 2 turns
                    if cur_node.time == 0:
                        initial_d = turret_dirr
                    else:
                        initial_d = cur_node.initial_d
                    q.put(Node(cur_node.x, cur_node.y, turret_dirr, cur_node.time+1, True, temp, initial_d))

            new_x, new_y = change_direction(cur_node.x, cur_node.y, cur_node.direction, gameboard.height, gameboard.width)
            #print("new {}, {}, {}, {}, {}, {}, {}".format(n_futures[cur_node.time+1][new_y][new_x], len(n_futures), len(n_futures[0]), len(n_futures[0][0]), cur_node.time+1, new_x, new_y))

            if (cur_node.time+1 <= n-1) and (n_futures[cur_node.time+1][new_x][new_y] == SAFE) and (not ((new_x, new_y) in cur_node.traveled)):
                temp = cur_node.traveled
                temp[(new_x, new_y)] = 1
                if cur_node.time == 0:
                    initial_d = cur_node.direction
                else:
                    initial_d = cur_node.initial_d
                q.put(Node(new_x, new_y, cur_node.direction, cur_node.time+1, True, temp, initial_d))

            if cur_node.can_rotate and (n_futures[cur_node.time+1][cur_node.x][cur_node.y] == SAFE):
                for dirr in [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]:
                    if dirr != cur_node.direction:
                        if cur_node.time == 0:
                            initial_d = dirr
                        else:
                            initial_d = cur_node.initial_d
                        q.put(Node(cur_node.x, cur_node.y, dirr, cur_node.time+1, False, cur_node.traveled, initial_d))

        return None

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
        n = 23
        for t in range(n):
            safe_spots = deepcopy(base_matrix)
            if not player.shield_active:
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
                    if (this_turn-1)%(tur.fire_time + tur.cooldown_time) < tur.fire_time:
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
                    bull.x, bull.y = change_direction(bull.x, bull.y, bull.direction, gameboard.height, gameboard.width)
                    safe_spots[bull.x][bull.y] = UNSAFE


                #pop dead bullets
                temp = []
                for c in range(len(bulls)):
                    if c not in to_pop:
                        temp.append(bulls[c])
                bulls = temp

            n_futures.append(safe_spots)

        # print(n_futures[0])
        # print(n_futures[1])

        new_dirr = self.target_closest_point(player, gameboard, n, n_futures)
        p_dirr = player.direction
        #print(new_dirr)

        new_x, new_y = player.x, player.y

        if new_dirr == None:
            play =  Move.NONE
        elif new_dirr == p_dirr:
            play = Move.FORWARD
            new_x, new_y = change_direction(player.x, player.y, player.direction, gameboard.height, gameboard.width)
        elif new_dirr == Direction.UP:
            play = Move.FACE_UP
        elif new_dirr == Direction.DOWN:
            play = Move.FACE_DOWN
        elif new_dirr == Direction.LEFT:
            play = Move.FACE_LEFT
        else:
            play = Move.FACE_RIGHT

        if player.shield_count > 0:
            if (player.shield_count > 1):
                play = Move.SHIELD

        #If you see a Turret, if you're safe, shoot it
        curr_x = player.x
        curr_y = player.y
        if player.direction == Direction.LEFT:
            dx, dy = -1, 0
        elif player.direction == Direction.RIGHT:
            dx, dy = 1, 0
        elif player.direction == Direction.DOWN:
            dx, dy = 0, 1
        else: #UP
            dx, dy = 0, -1

        i_x = (player.x + dx) % gameboard.width
        i_y = (player.y + dy) % gameboard.height

        while (not gameboard.is_turret_at_tile(i_x, i_y)) and (not gameboard.is_wall_at_tile(i_x, i_y)) and not (curr_x == i_x and curr_y == i_y):
            i_x = (i_x + dx) % gameboard.width
            i_y = (i_y + dy) % gameboard.height
        if gameboard.is_turret_at_tile(i_x, i_y):
            play = Move.SHOOT
            new_x, new_y = player.x, player.y


        if player.shield_count > 0:
            if (n_futures[0][new_x][new_y] == UNSAFE):
                play = Move.SHIELD


        return play

        # self.hardcoded_i += 1
        # return self.hardcoded[self.hardcoded_i%len(self.hardcoded)]