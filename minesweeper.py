"""
-----------------------------------------------------------------------------
  Minesweeper
-----------------------------------------------------------------------------
  Version:  1.2
  Authors:  Asa Maker, Zach Sevart, Ebraheem Alaamer
  Created:  2025-09-10
  Modified: 2025-09-15
-----------------------------------------------------------------------------
  Inputs:   - Mouse clicks (left-click to reveal, right-click to flag)
            - Console input for the number of mines at startup.
  Outputs:  - A graphical Minesweeper game window.
            - Game status updates displayed on the screen.
-----------------------------------------------------------------------------
  Description:
  This script implements a complete, playable Minesweeper game with a modern
  graphical user interface using the Pygame library. It adheres to the
  specifications for the EECS 581 Project 1, featuring a 10x10 grid with
  row/column labels, user-defined mine count (10-20), and core gameplay logic.
-----------------------------------------------------------------------------
  Attribution:
  This code was developed in full by Asa Maker and Zach Sevart for the
  EECS 581 Project 1 assignment. A special thanks to Kevin Likani (spell his name right Asa) for
  assistance with this project.
-----------------------------------------------------------------------------
"""

import pygame
import random
import sys

# =============================================================================
# 1. Game Constants and Configuration
# =============================================================================
# This section defines the core parameters for the game window, grid, and colors.

#grid and Cell Dimensions
GRID_SIZE = 10  #how many cells per side (square grid)
CELL_SIZE = 50  #set CELL SIZE; used for layout or sizing
LABEL_AREA_SIZE = 40 # set LABEL AREA SIZE; used for layout or sizing
GRID_WIDTH = GRID_SIZE * CELL_SIZE #width and height set to grid size * cell size  # set GRID WIDTH; used for layout or sizing.
GRID_HEIGHT = GRID_SIZE * CELL_SIZE #set GRID HEIGHT; used for layout or sizing
HEADER_HEIGHT = 150 # set HEADER HEIGHT; used for layout or sizing

# Window Dimensions
SCREEN_WIDTH = GRID_WIDTH + LABEL_AREA_SIZE # set SCREEN WIDTH; used for layout or sizing
SCREEN_HEIGHT = GRID_HEIGHT + HEADER_HEIGHT + LABEL_AREA_SIZE # set SCREEN HEIGHT; used for layout or sizing

#Colors - A modern, clean color palette
COLOR_BG = (28, 28, 30) # RGB color for COLOR BG
COLOR_HEADER_BG = (45, 45, 48) # RGB color for COLOR HEADER BG
COLOR_GRID_LINES = (62, 62, 66) # RGB color for COLOR GRID LINES
COLOR_CELL_COVERED = (62, 62, 66) # RGB color for COLOR CELL COVERED
COLOR_CELL_UNCOVERED = (45, 45, 48) # RGB color for COLOR CELL UNCOVERED
COLOR_FLAG = (240, 81, 47) # RGB color for COLOR FLAG
COLOR_MINE = (200, 70, 70) # RGB color for COLOR MINE
COLOR_TEXT = (220, 220, 220) # RGB color for COLOR TEXT
COLOR_TEXT_HEADER = (255, 255, 255) # RGB color for COLOR TEXT HEADER
COLOR_RESTART_BUTTON = (86, 156, 214) # RGB color for COLOR RESTART BUTTON
COLOR_NUMBERS = { # set COLOR NUMBERS; used for layout or sizing
    1: (86, 156, 214), 2: (78, 201, 176), 3: (206, 145, 120),
    4: (189, 99, 197), 5: (215, 186, 125), 6: (75, 180, 184),
    7: (174, 174, 174), 8: (120, 120, 120)
}
#potentially using images from original game for UI (
CELL_IMG = pygame.image.load('images/cell_0_0.png') #og cell image
CELL_IMG = pygame.transform.scale(CELL_IMG, (CELL_SIZE, CELL_SIZE)) #scales to fit cell
FLAG_IMG = pygame.image.load('images/cell_0_2.png')  #og flag image
FLAG_IMG = pygame.transform.scale(FLAG_IMG, (CELL_SIZE, CELL_SIZE)) #scales to fit cell
MINE_IMG = pygame.image.load('images/cell_0_6.png') #og mine image
MINE_IMG = pygame.transform.scale(MINE_IMG, (CELL_SIZE, CELL_SIZE)) #scales to fit cell
CLICKED_IMG = pygame.image.load('images/cell_0_1.png') #og clicked/revealed image
CLICKED_IMG = pygame.transform.scale(CLICKED_IMG, (CELL_SIZE, CELL_SIZE)) #scales to fit cell
NUMBER_IMGS = { #maps images for adjacent mines to cells
    1: pygame.image.load('images/cell_1_0.png'),  # load images/cell_1_0.png into memory
    2: pygame.image.load('images/cell_1_1.png'),  # load images/cell_1_1.png into memory
    3: pygame.image.load('images/cell_1_2.png'),  # load images/cell_1_2.png into memory
    4: pygame.image.load('images/cell_1_3.png'),  # load images/cell_1_3.png into memory
    5: pygame.image.load('images/cell_1_4.png'),  # load images/cell_1_4.png into memory
    6: pygame.image.load('images/cell_1_5.png'),  # load images/cell_1_5.png into memory
    7: pygame.image.load('images/cell_1_6.png'),  # load images/cell_1_6.png into memory
    8: pygame.image.load('images/cell_1_7.png')  # load images/cell_1_7.png into memory
}
for num in NUMBER_IMGS: # loop through items
    NUMBER_IMGS[num] = pygame.transform.scale(NUMBER_IMGS[num], (CELL_SIZE, CELL_SIZE)) #scales all number images to cell size.


DIGIT_SIZE = (20, 30)
DIGIT_IMGS = {
    0: pygame.image.load('images/cell9.png'),
    1: pygame.image.load('images/cell0.png'),
    2: pygame.image.load('images/cell1.png'),
    3: pygame.image.load('images/cell2.png'),
    4: pygame.image.load('images/cell3.png'),
    5: pygame.image.load('images/cell4.png'),
    6: pygame.image.load('images/cell5.png'),
    7: pygame.image.load('images/cell6.png'),
    8: pygame.image.load('images/cell7.png'),
    9: pygame.image.load('images/cell8.png'),
    '-': pygame.image.load('images/cell10.png'),
    'empty': pygame.image.load('images/cell11.png')
}
for key in DIGIT_IMGS:
    DIGIT_IMGS[key] = pygame.transform.scale(DIGIT_IMGS[key], DIGIT_SIZE)

# =============================================================================
# 2. Cell Class
# =============================================================================
class Cell:
    """Represents a single cell in the Minesweeper grid."""

    def __init__(self, row, col):# function __init__: does this specific task for the game
        self.row = row  # set row; used for layout or sizing
        self.col = col  # set col; used for layout or sizing
        # Adjust x, y coordinates to account for the label area  
        self.x = col * CELL_SIZE + LABEL_AREA_SIZE  # set x; used for layout or sizing
        self.y = row * CELL_SIZE + HEADER_HEIGHT + LABEL_AREA_SIZE  # set y; used for layout or sizing
        self.is_mine = False #cells aren't initialized as a mine  # track is mine as part of the game state
        self.is_revealed = False #cells aren't revealed until game starts  # track is revealed as part of the game state
        self.is_flagged = False #cells don't start off flagged  # track is flagged as part of the game state
        self.adjacent_mines = 0 #cells don't have adjacent mines until start  # set adjacent mines; used for layout or sizing


    def draw(self, screen, font):  # function draw: does this specific task for the game
        """Renders the cell on the screen based on its current state."""  # quick docstring/header note
        rect = pygame.Rect(self.x, self.y, CELL_SIZE, CELL_SIZE)  # set rect; used for layout or sizing
        if self.is_revealed:  # if this condition holds, do the next bit
            screen.blit(CLICKED_IMG, (self.x, self.y))  # draw that image/text onto the screen
            if self.is_mine:  # if this condition holds, do the next bit
                self.draw_mine(screen, rect)  # call a function/method here
            elif self.adjacent_mines > 0:  # otherwise, try this condition
                screen.blit(NUMBER_IMGS[self.adjacent_mines], (self.x, self.y))  # draw that image/text onto the screen
        else:  # fallback when none of the above matched
            screen.blit(CELL_IMG, (self.x, self.y))  # draw that image/text onto the screen
            if self.is_flagged:  # if this condition holds, do the next bit
                self.draw_flag(screen, rect)  # call a function/method here
        pygame.draw.rect(screen, COLOR_GRID_LINES, rect, 1)  # draw a rectangle (used for UI panels/buttons)

    def draw_flag(self, screen, rect):  # function draw_flag: does this specific task for the game
        """Draws a flag icon in the center of the cell's rectangle."""  # quick docstring/header note
        screen.blit(FLAG_IMG, (self.x, self.y))  # draw that image/text onto the screen

    def draw_mine(self, screen, rect):  # function draw_mine: does this specific task for the game
        """Draws a mine icon in the center of the cell's rectangle."""  # quick docstring/header note
        screen.blit(MINE_IMG, (self.x, self.y))  # draw that image/text onto the screen

# =============================================================================
# 3. Board Class
# =============================================================================
class Board:  # defining class Board to group related behavior
    """Manages the grid of cells and core game logic."""  # quick docstring/header note

    def __init__(self, num_mines):  # function __init__: does this specific task for the game
        self.grid = [[Cell(row, col) for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]  # set grid; used for layout or sizing
        self.num_mines = num_mines  # set num mines; used for layout or sizing

    def place_mines(self, first_click_row, first_click_col):  # function place_mines: does this specific task for the game
        """Randomly places mines, ensuring the first clicked cell is safe."""  # quick docstring/header note
        safe_zone = set()  # set safe zone; used for layout or sizing
        for r_offset in range(-1, 2):  # loop through items
            for c_offset in range(-1, 2):  # loop through items
                r, c = first_click_row + r_offset, first_click_col + c_offset  # set up a value I need later
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:  # if this condition holds, do the next bit
                    safe_zone.add((r, c))  # call a function/method here

        possible_mine_locations = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if
                                   (r, c) not in safe_zone]  # set up a value I need later
        mine_locations = random.sample(possible_mine_locations, self.num_mines)  # call a function/method here

        for r, c in mine_locations:  # loop through items
            self.grid[r][c].is_mine = True  # track is mine as part of the game state
        self.calculate_all_adjacent_mines()  # call a function/method here
      
    def calculate_all_adjacent_mines(self):  # function calculate_all_adjacent_mines: does this specific task for the game
        """Calculates adjacent mines for each non-mine cell."""  # quick docstring/header note
        for r in range(GRID_SIZE):  # loop through items
            for c in range(GRID_SIZE):  # loop through items
                if not self.grid[r][c].is_mine:  # if this condition holds, do the next bit
                    self.grid[r][c].adjacent_mines = self.count_adjacent_mines(r, c)  # set adjacent mines; used for layout or sizing

    def count_adjacent_mines(self, row, col):  # function count_adjacent_mines: does this specific task for the game
        """Counts mines adjacent to a given cell."""  # quick docstring/header note
        count = 0  # set count; used for layout or sizing
        for r_offset in range(-1, 2):  # loop through items
            for c_offset in range(-1, 2):  # loop through items
                if r_offset == 0 and c_offset == 0: continue  # if this condition holds, do the next bit
                r, c = row + r_offset, col + c_offset  # set up a value I need later
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and self.grid[r][c].is_mine:  # if this condition holds, do the next bit
                    count += 1  # set up a value I need later
        return count  # hand back a value / finish here

    def reveal_cell(self, row, col):  # function reveal_cell: does this specific task for the game
        """Recursively reveals cells."""  # quick docstring/header note
        cell = self.grid[row][col]  # set cell; used for layout or sizing
        if cell.is_revealed or cell.is_flagged: return  # if this condition holds, do the next bit
        cell.is_revealed = True  # track is revealed as part of the game state
        if cell.adjacent_mines == 0 and not cell.is_mine:  # if this condition holds, do the next bit
            for r_offset in range(-1, 2):  # loop through items
                for c_offset in range(-1, 2):  # loop through items
                    if r_offset == 0 and c_offset == 0: continue  # if this condition holds, do the next bit
                    r, c = row + r_offset, col + c_offset  # set up a value I need later
                    if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:  # if this condition holds, do the next bit
                        self.reveal_cell(r, c)  # call a function/method here

    def reveal_all_mines(self):  # function reveal_all_mines: does this specific task for the game
        """Reveals all mines at the end of a game."""  # quick docstring/header note
        for row in self.grid:  # loop through items
            for cell in row:  # loop through items
                if cell.is_mine:  # if this condition holds, do the next bit
                    cell.is_revealed = True  # track is revealed as part of the game state


# =============================================================================
# 4. Game Class
# =============================================================================
class Game:
    """Main class to manage the game loop, state, and rendering."""

    def __init__(self, num_mines):  # function __init__: does this specific task for the game
        pygame.init()  # boot up pygame (and fonts)
        pygame.font.init()  # boot up pygame (and fonts)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # open the game window with this width/height
        pygame.display.set_caption("EECS 581 Minesweeper")  # call a function/method here

        # Fonts  # (note I left for myself)
        self.header_font = pygame.font.Font(None, 50)  # pick a font and size for text rendering
        self.cell_font = pygame.font.Font(None, 32)  # pick a font and size for text rendering
        self.status_font = pygame.font.Font(None, 30)  # pick a font and size for text rendering
        self.label_font = pygame.font.Font(None, 24)  # pick a font and size for text rendering

        # Pre-rendered static text  # (note I left for myself)
        self.title_text_surface = self.header_font.render("MINESWEEPER", True, COLOR_TEXT_HEADER)  # call a function/method here
        self.title_text_rect = self.title_text_surface.get_rect(center=(SCREEN_WIDTH / 2, 40))  # center this text/image where I want it

        # Restart button  # (note I left for myself)
        self.restart_text_surface = self.status_font.render("Restart", True, COLOR_TEXT_HEADER)  # call a function/method here
        self.restart_button_rect = pygame.Rect(SCREEN_WIDTH - 120, 30, 100, 40)  # set restart button rect; used for layout or sizing
        self.restart_text_rect = self.restart_text_surface.get_rect(center=self.restart_button_rect.center)  # center this text/image where I want it

        self.num_mines = num_mines  # set num mines; used for layout or sizing
        self.last_game_status = None  # To track the result of the previous game  # track last game status as part of the game state
        self.reset_game()  # call a function/method here
  


    def reset_game(self):  # function reset_game: does this specific task for the game
        """Resets the game to its initial state, recording the previous game's result."""  # quick docstring/header note
        # Before resetting, check if a game was just completed and record its status.  # (note I left for myself)
        # The hasattr check ensures this doesn't run on the very first initialization.  # (note I left for myself)
        if hasattr(self, 'game_over') and self.game_over:  # if this condition holds, do the next bit
            self.last_game_status = "Victory!" if self.win else "Loss"  # set last game status; used for layout or sizing

        self.board = Board(self.num_mines)  # set board; used for layout or sizing
        self.game_over = False  # track game over as part of the game state
        self.win = False  # track win as part of the game state
        self.first_click = True  # track first click as part of the game state
        self.running = True  # track running as part of the game state
        self.flags_placed = 0  # set flags placed; used for layout or sizing
      

    def run(self):  # function run: does this specific task for the game
        """The main game loop."""  # quick docstring/header note
        while self.running:  # repeat while this stays true
            self.handle_events()  # call a function/method here
            self.update()  # call a function/method here
            self.draw()  # call a function/method here
        pygame.quit()  # call a function/method here
        sys.exit()  # call a function/method here

    def handle_events(self):  # function handle_events: does this specific task for the game
        """Processes all user inputs."""  # quick docstring/header note
        for event in pygame.event.get():  # read all input events (mouse/quit/etc.)
            if event.type == pygame.QUIT:  # user closed the window — time to exit
                self.running = False  # track running as part of the game state
            if event.type == pygame.MOUSEBUTTONDOWN:  # mouse click happened
                if self.restart_button_rect.collidepoint(event.pos):  # check if the click landed on the restart button
                    self.reset_game()  # call a function/method here
                    return  # hand back a value / finish here

                if not self.game_over:  # if this condition holds, do the next bit
                    x, y = event.pos  # set up a value I need later
                    # Adjust click coordinates for the label area offset  # (note I left for myself)
                    if x > LABEL_AREA_SIZE and y > HEADER_HEIGHT + LABEL_AREA_SIZE:  # if this condition holds, do the next bit
                        col = (x - LABEL_AREA_SIZE) // CELL_SIZE  # set col; used for layout or sizing
                        row = (y - HEADER_HEIGHT - LABEL_AREA_SIZE) // CELL_SIZE  # set row; used for layout or sizing

                        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:  # if this condition holds, do the next bit
                            cell = self.board.grid[row][col]  # set cell; used for layout or sizing
                            if event.button == 1 and not cell.is_flagged:  # left click
                                if self.first_click:  # if this condition holds, do the next bit
                                    self.board.place_mines(row, col)  # call a function/method here
                                    self.first_click = False  # track first click as part of the game state
                                self.board.reveal_cell(row, col)  # call a function/method here
                                if cell.is_mine:  # if this condition holds, do the next bit
                                    self.game_over = True  # track game over as part of the game state
                                    self.win = False  # track win as part of the game state
                                    self.board.reveal_all_mines()  # call a function/method here
                            elif event.button == 3 and not cell.is_revealed:  # right click (flag/unflag)
                                if not cell.is_flagged and self.flags_placed < self.num_mines:  # if this condition holds, do the next bit
                                    cell.is_flagged = True  # track is flagged as part of the game state
                                    self.flags_placed += 1  # set up a value I need later
                                elif cell.is_flagged:  # otherwise, try this condition
                                    cell.is_flagged = False  # track is flagged as part of the game state
                                    self.flags_placed -= 1  # set up a value I need later
                                  
    def update(self):  # keep the game state fresh each frame
        """Updates the game state, such as checking for a win."""
        if not self.game_over and not self.first_click:
            self.check_win_condition() # see if all safe cells are revealed yet
            # if that check decided the game is over (win or loss)
            if self.game_over: # lock in the final elapsed time (so it doesn’t keep ticking after game ends)
                self.elapsed_time = (pygame.time.get_ticks() - self.start_time) // 1000 #save time to display for last round

    def check_win_condition(self):  # function check_win_condition: does this specific task for the game
        """Checks if all non-mine cells have been revealed."""  # quick docstring/header note
        revealed_count = sum(1 for r in self.board.grid for c in r if c.is_revealed and not c.is_mine)  # set revealed count; used for layout or sizing
        if revealed_count == (GRID_SIZE * GRID_SIZE) - self.num_mines:  # if this condition holds, do the next bit
            self.game_over = True  # track game over as part of the game state
            self.win = True  # track win as part of the game state

    def draw(self):  # function draw: does this specific task for the game
        """Renders all game elements to the screen."""  # quick docstring/header note
        self.screen.fill(COLOR_BG)  # call a function/method here
        self.draw_header()  # call a function/method here
        self.draw_labels()  # call a function/method here
        for row in self.board.grid:  # loop through items
            for cell in row:  # loop through items
                cell.draw(self.screen, self.cell_font)  # call a function/method here
        pygame.display.flip()  # push the new frame to the screen

    def draw_header(self): # top strip with title, flags counter, and timer
        """Draws the top header panel.""" # quick reminder of what this does
        pygame.draw.rect(self.screen, COLOR_HEADER_BG, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))  # paint the header bar
        self.screen.blit(self.title_text_surface, self.title_text_rect) # drop the “MINESWEEPER” title in its spot
        flags_remaining = self.num_mines - self.flags_placed  # how many mines still unflagged
        flag_text = self.status_font.render(f"Mines: ", True, COLOR_TEXT) # render the label text “Mines: ”
        self.screen.blit(flag_text, (50, 125)) # put that label near the left side
        timer_text = self.status_font.render(f"Timer: ", True, COLOR_TEXT) # render the label text “Timer: ”
        self.screen.blit(timer_text, ((SCREEN_WIDTH // 2) + 20, 125)) # place the timer label around the middle-right
        flags_str = f"{flags_remaining:03d}"
        digits = [int(d) for d in flags_str] # split into separate numbers so we can draw each digit image
        flags_x = 120 # starting x for the first flag digit (tuned by eye)
        for i, digit in enumerate(digits): # walk through each digit (hundreds, tens, ones)
            self.screen.blit(DIGIT_IMGS[digit], (flags_x + i * DIGIT_SIZE[0], 115)) # place digits side-by-side


        if self.start_time is not None and not self.game_over:
            self.elapsed_time = min((pygame.time.get_ticks() - self.start_time) // 1000, 999)  # Cap at 999
        if self.start_time is None:
            digits = ['-', '-', '-']  # Show dashes before first click
        else:
            # Convert elapsed time to three digits (e.g., 7 -> "007", 123 -> "123")
            time_str = f"{self.elapsed_time:03d}" if self.elapsed_time <= 999 else "999"
            digits = [int(d) for d in time_str]

        # Blit three digit images
        timer_x = SCREEN_WIDTH - 180  # Position timer to fit three 20x30 digits
        for i, digit in enumerate(digits):
            self.screen.blit(DIGIT_IMGS[digit], (timer_x + i * DIGIT_SIZE[0], 115))

        # Display last game status if available  # (note I left for myself)
        if self.last_game_status:  # if this condition holds, do the next bit
            last_game_text = self.status_font.render(f"Last Game: {self.last_game_status}", True, COLOR_TEXT)  # call a function/method here
            self.screen.blit(last_game_text, (20, 65))  # draw that image/text onto the screen


        pygame.draw.rect(self.screen, COLOR_RESTART_BUTTON, self.restart_button_rect, border_radius=8)  # draw a rectangle (used for UI panels/buttons)
        self.screen.blit(self.restart_text_surface, self.restart_text_rect)  # draw that image/text onto the screen
        status_text_str = "Victory!" if self.win else "Game Over" if self.game_over else "Playing..."  # set status text str; used for layout or sizing
        status_text = self.status_font.render(status_text_str, True, COLOR_TEXT)  # call a function/method here
        status_rect = status_text.get_rect(center=(SCREEN_WIDTH / 2, 80))  # center this text/image where I want it
        self.screen.blit(status_text, status_rect)  # draw that image/text onto the screen

    def draw_labels(self):  # function draw_labels: does this specific task for the game
        """Draws the A-J column and 1-10 row labels."""  # quick docstring/header note
        for i in range(GRID_SIZE):  # loop through items
            # Column labels (A-J)  # (note I left for myself)
            col_text = self.label_font.render(chr(ord('A') + i), True, COLOR_TEXT)  # call a function/method here
            col_rect = col_text.get_rect(
                center=(LABEL_AREA_SIZE + i * CELL_SIZE + CELL_SIZE / 2, HEADER_HEIGHT + LABEL_AREA_SIZE / 2))  # center this text/image where I want it
            self.screen.blit(col_text, col_rect)  # draw that image/text onto the screen
            # Row labels (1-10)  # (note I left for myself)
            row_text = self.label_font.render(str(i + 1), True, COLOR_TEXT)  # call a function/method here
            row_rect = row_text.get_rect(
                center=(LABEL_AREA_SIZE / 2, HEADER_HEIGHT + LABEL_AREA_SIZE + i * CELL_SIZE + CELL_SIZE / 2))  # center this text/image where I want it
            self.screen.blit(row_text, row_rect)  # draw that image/text onto the screen


# =============================================================================
# 5. Main Execution Block
# =============================================================================
if __name__ == "__main__":  # if this condition holds, do the next bit
    while True:  # repeat while this stays true
        try:  # try this; if it fails, handle it below
            num_mines = int(input("Enter the number of mines (10-20): "))  # call a function/method here
            if 10 <= num_mines <= 20:  # if this condition holds, do the next bit
                break  # hand back a value / finish here
            else:  # fallback when none of the above matched
                print("Invalid range. Please enter a number between 10 and 20.")  # call a function/method here
        except ValueError:  # caught a specific error
            print("Invalid input. Please enter a valid number.")  # call a function/method here

    game = Game(num_mines)  # call a function/method here
    game.run()  # call a function/method here


