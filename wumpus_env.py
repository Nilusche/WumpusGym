import pygame, sys, random, time
import numpy as np
import gym
from gym import spaces, error, utils
from gym.utils import seeding
from pygame import display


BLACK = pygame.Color(0,0,0)
WHITE = pygame.Color(255,255,255)
RED = pygame.Color(255,0,0)
GREEN = pygame.Color(0,255,0)
BLUE = pygame.Color(0,0,255)
pygame.font.init()
ROWS =4 
WIDTH = 400
SQ_SIZE = WIDTH // ROWS
IMAGES = {}

INITIAL_BOARD = np.array([
    ['_', '_', '_', 'P'],
    ['W', 'G', 'P', '_'],
    ['_', '_', '_', '_'],
    ['A_UP', '_', 'P', '_']
])

other_board =  np.array([
    ['_', '_', '_', 'P'],
    ['_', 'P', 'P', '_'],
    ['W', 'A_UP', '_', '_'],
    ['_', '_', 'P', '_']
])

#ACTION_SPACE = ["WALK", "TURNLEFT" , "TURNRIGHT", "SHOOT", "GRAB", "CLIMB"]

def load_images():
    pieces = ["W", "P", "G", "A_UP", "A_DOWN", "A_LEFT", "A_RIGHT"]
    for piece in pieces:
        IMAGES[piece] = pygame.transform.scale(pygame.image.load("images/"+piece+".png"),(SQ_SIZE, SQ_SIZE))

def draw_grid(win):
    for i in range(ROWS):
        pygame.draw.line(win, (0,0,0), (0,i*SQ_SIZE), (WIDTH, i*SQ_SIZE))
        for j in range(ROWS):
            pygame.draw.line(win, (0,0,0), (j*SQ_SIZE, 0), (j*SQ_SIZE, WIDTH))

def draw_board(win, board):
    for i in range(ROWS):
        for j in range(ROWS):
            if board[j][i] !="_":
                win.blit(IMAGES[board[j][i]], (i*SQ_SIZE, j*SQ_SIZE))

def draw_game(win, board):
    win.fill((255,255,255))
    draw_grid(win)
    draw_board(win, board)

class Wumpus(gym.Env):
    def __init__(self):
        self.observation_space = spaces.Discrete(11)
        self.action_space = spaces.Discrete(6)
        self.frame_size_x = WIDTH
        self.frame_size_y = WIDTH
        self.screen  = pygame.display.set_mode((self.frame_size_x, self.frame_size_y))
        self.reset()
        self.STEP_LIMIT = 1000
        


    def reset(self):
        self.screen.fill(WHITE)
        self.board = INITIAL_BOARD
        self.player_x = list(zip(*np.where(self.board == "A_UP")))[0][0]
        self.player_y = list(zip(*np.where(self.board == "A_UP")))[0][1]
        self.wumpus_x = 0
        self.wumpus_y = 1
        self.player_direction = "UP"
        self.player_alive = True
        self.player_arrows = 1
        self.gold = False
        self.scream = False
        self.stench = Wumpus.check_stench(self.board, self.player_x, self.player_y)
        self.breeze = Wumpus.check_breeze(self.board, self.player_x, self.player_y)
        self.glitter = Wumpus.check_glitter(self.board, self.player_x, self.player_y)
        self.bump = False
        self.steps = 0
        
        self.action = 0

    @staticmethod
    def check_stench(board, x, y):
        #Adjacent squares of the wumpus have a stench
        #Check adjacent squares of the player for a wumpus
        if y-1 >= 0:
            if board[y-1][x] == "W":
                return True
        if y+1 < ROWS:
            if board[y+1][x] == "W":
                return True
        if x-1 >= 0:
            if board[y][x-1] == "W":
                return True
        if x+1 < ROWS:
            if board[y][x+1] == "W":
                return True
            
        return False

    @staticmethod
    def check_breeze(board, x,y ):
        #Adjacent squares of the pit have a breeze
        #Check adjacent squares of the player for a breeze
        if y-1 >= 0:
            if board[y-1][x] == "P":
                return True
        if y+1 < ROWS:
            if board[y+1][x] == "P":
                return True
        if x-1 >= 0:
            if board[y][x-1] == "P":
                return True
        if x+1 < ROWS:
            if board[y][x+1] == "P":
                return True
            
        return False

    @staticmethod
    def check_glitter(board, x, y):
        #If the player is on the same square as the gold, the player can grab the gold
        if board[y][x] == "G":
            return True
        return False

    def render(self, mode="human"):
        if mode == "human": 
            load_images()
            draw_game(self.screen, INITIAL_BOARD)  
            pygame.display.flip()
        else:
            print(self.board)

    @staticmethod
    def change_direction(direction, action):    
        if action == 1:
            if direction == "UP":
                return "LEFT"
            elif direction == "DOWN":
                return "RIGHT"
            elif direction == "LEFT":
                return "DOWN"
            elif direction == "RIGHT":
                return "UP"
        elif action == 2:
            if direction == "UP":
                return "RIGHT"
            elif direction == "DOWN":
                return "LEFT"
            elif direction == "LEFT":
                return "UP"
            elif direction == "RIGHT":
                return "DOWN"
        return direction


    


        

    def step(self, action):
        if action == 1 or action == 2: # Turn left or right
            self.player_direction = self.change_direction(self.player_direction, action)
            ## change picture to direction
            self.board[self.player_y][self.player_x] = "A" + self.player_direction
        elif action == 0: # Walk forward
            if self.player_direction == "UP":
                self.player_y -= 1
            elif self.player_direction == "DOWN":
                self.player_y += 1
            elif self.player_direction == "LEFT":
                self.player_x -= 1
            elif self.player_direction == "RIGHT":
                self.player_x += 1
        elif action == 3: # Shoot an arrow
            pass
        elif action == 4: # Grab the gold   
            if self.board[self.player_y][self.player_x] == "G":
                self.gold = True
                self.board[self.player_y][self.player_x] = "_"
        elif action == 5: # Climb up the ladder
            #check if player is at start position:
            if self.player_x == 1 and self.player_y == 2:
                pass
        
        observation = self.get_observation()
        info = {"alive": self.player_alive, "gold": self.gold, "steps": self.steps}
        reward = self.reward_handler()

        reward, done = self.game_over(reward, self.board)
            
        return observation, reward, done, info

    def get_observation(self):
        observation = []
        observation.append(self.player_x)
        observation.append(self.player_y)
        observation.append(self.stench)
        observation.append(self.breeze)
        observation.append(self.glitter)
        observation.append(self.bump)
        observation.append(self.player_arrows)
        observation.append(self.player_direction)

        return observation
        
        

    def reward_handler(self):
        if self.player_arrows == 0 and self.scream == False:
            return -10
        if self.player_arrows == 0 and self.scream == True:
            return 100
        return -1
            

    def game_over(self, reward, board):
        # player is at the same position as the wumpus
        if board[self.player_y][self.player_x] == "W":
            self.player_alive = False
            reward = -1000
            return reward, True#
        # player fell in a pit
        if board[self.player_y][self.player_x] == "P":
            self.player_alive = False
            reward = -1000
            return reward, True
        
        # player has the gold and is at start_position
        if self.gold == True and self.player_x == 0 and self.player_y == 0:
            reward = 1000
            return reward, True
        
        # steps limit reached
        if self.steps == self.STEP_LIMIT:
            reward = 0
            return reward, True
        
        return reward, False

    def close(self):
        pygame.quit()
        



w = Wumpus()
w.render()
#print("x, y", w.player_x, w.player_y)
#print(other_board[w.player_y][w.player_x])
#print(w.stench)
#print(w.breeze)

        
    

