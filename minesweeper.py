"""
-----------------------------------------------------------------------------
  Minesweeper
-----------------------------------------------------------------------------
  Version:  1.2
  Authors:  Asa Maker & Zach Sevart
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
  EECS 581 Project 1 assignment. A special thanks to Kevin Likani for
  assistance with this project.
-----------------------------------------------------------------------------
"""

from typing import Callable, Literal, TypeVar, Optional
import pygame
import random
import sys

# TYPES
Difficulty = Literal['easy', 'medium', 'hard']

# =============================================================================
# 1. Game Constants and Configuration
# =============================================================================
# This section defines the core parameters for the game window, grid, and colors.

# Grid and Cell Dimensions
GRID_SIZE = 10
CELL_SIZE = 50  # Reduced size to better fit labels
LABEL_AREA_SIZE = 40
GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE
HEADER_HEIGHT = 100

# Window Dimensions
SCREEN_WIDTH = GRID_WIDTH + LABEL_AREA_SIZE
SCREEN_HEIGHT = GRID_HEIGHT + HEADER_HEIGHT + LABEL_AREA_SIZE

# Colors - A modern, clean color palette
COLOR_BG = (28, 28, 30)
COLOR_HEADER_BG = (45, 45, 48)
COLOR_GRID_LINES = (62, 62, 66)
COLOR_CELL_COVERED = (62, 62, 66)
COLOR_CELL_UNCOVERED = (45, 45, 48)
COLOR_FLAG = (240, 81, 47)
COLOR_MINE = (200, 70, 70)
COLOR_TEXT = (220, 220, 220)
COLOR_TEXT_HEADER = (255, 255, 255)
COLOR_RESTART_BUTTON = (86, 156, 214)
COLOR_NUMBERS = {
    1: (86, 156, 214), 2: (78, 201, 176), 3: (206, 145, 120),
    4: (189, 99, 197), 5: (215, 186, 125), 6: (75, 180, 184),
    7: (174, 174, 174), 8: (120, 120, 120)
}


# =============================================================================
# 2. Cell Class
# =============================================================================
class Cell:
    """Represents a single cell in the Minesweeper grid."""

    def __init__(self, row, col):
        self.row = row
        self.col = col
        # Adjust x, y coordinates to account for the label area
        self.x = col * CELL_SIZE + LABEL_AREA_SIZE
        self.y = row * CELL_SIZE + HEADER_HEIGHT + LABEL_AREA_SIZE
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_mines = 0

    def draw(self, screen, font):
        """Renders the cell on the screen based on its current state."""
        rect = pygame.Rect(self.x, self.y, CELL_SIZE, CELL_SIZE)
        if self.is_revealed:
            pygame.draw.rect(screen, COLOR_CELL_UNCOVERED, rect)
            if self.is_mine:
                self.draw_mine(screen, rect)
            elif self.adjacent_mines > 0:
                text_surface = font.render(str(self.adjacent_mines), True, COLOR_NUMBERS[self.adjacent_mines])
                text_rect = text_surface.get_rect(center=rect.center)
                screen.blit(text_surface, text_rect)
        else:
            pygame.draw.rect(screen, COLOR_CELL_COVERED, rect)
            if self.is_flagged:
                self.draw_flag(screen, rect)
        pygame.draw.rect(screen, COLOR_GRID_LINES, rect, 1)

    def draw_flag(self, screen, rect):
        """Draws a flag icon in the center of the cell's rectangle."""
        center_x, center_y = rect.center
        flag_pole = pygame.Rect(center_x - 1, center_y - 12, 3, 24)
        flag_triangle = [(center_x, center_y - 12), (center_x + 12, center_y - 8), (center_x, center_y - 4)]
        pygame.draw.rect(screen, COLOR_TEXT, flag_pole)
        pygame.draw.polygon(screen, COLOR_FLAG, flag_triangle)

    def draw_mine(self, screen, rect):
        """Draws a mine icon in the center of the cell's rectangle."""
        pygame.draw.circle(screen, COLOR_MINE, rect.center, CELL_SIZE * 0.3)
        pygame.draw.circle(screen, COLOR_BG, rect.center, CELL_SIZE * 0.15)


# =============================================================================
# 3. Board Class
# =============================================================================
class Board:
    """Manages the grid of cells and core game logic."""

    def __init__(self, num_mines: int, difficulty: str):
        self.uncover_cell = getattr(self, f"uncover_cell_{difficulty}")
        self.grid = [[Cell(row, col) for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]
        self.num_mines = num_mines

    def place_mines(self, first_click_row, first_click_col):
        """Randomly places mines, ensuring the first clicked cell is safe."""
        safe_zone = set()
        for r_offset in range(-1, 2):
            for c_offset in range(-1, 2):
                r, c = first_click_row + r_offset, first_click_col + c_offset
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    safe_zone.add((r, c))

        possible_mine_locations = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE) if
                                   (r, c) not in safe_zone]
        mine_locations = random.sample(possible_mine_locations, self.num_mines)

        for r, c in mine_locations:
            self.grid[r][c].is_mine = True
        self.calculate_all_adjacent_mines()

    def calculate_all_adjacent_mines(self):
        """Calculates adjacent mines for each non-mine cell."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if not self.grid[r][c].is_mine:
                    self.grid[r][c].adjacent_mines = self.count_adjacent_mines(r, c)

    def count_adjacent_mines(self, row, col):
        """Counts mines adjacent to a given cell."""
        count = 0
        for r_offset in range(-1, 2):
            for c_offset in range(-1, 2):
                if r_offset == 0 and c_offset == 0: continue
                r, c = row + r_offset, col + c_offset
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and self.grid[r][c].is_mine:
                    count += 1
        return count

    def uncover_cell_easy(self) -> Cell:
        print("Uncovering cell (Easy)")
        r = random.randint(0, self.num_mines-1)
        c = random.randint(0, self.num_mines-1)
        cell = self.grid[r][c]
        while (cell.is_revealed and (not cell.is_flagged)):
            r = random.randint(0, self.num_mines-1)
            c = random.randint(0, self.num_mines-1)
            cell = self.grid[r][c]
        print(f"Picked cell {r + 1}:{chr(c + 65)}")
        self.reveal_cell(r, c)
        return cell

    def reveal_cell(self, row, col):
        """Recursively reveals cells."""
        cell = self.grid[row][col]
        if cell.is_revealed or cell.is_flagged: return
        cell.is_revealed = True
        if cell.adjacent_mines == 0 and not cell.is_mine:
            for r_offset in range(-1, 2):
                for c_offset in range(-1, 2):
                    if r_offset == 0 and c_offset == 0: continue
                    r, c = row + r_offset, col + c_offset
                    if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                        self.reveal_cell(r, c)

    def reveal_all_mines(self):
        """Reveals all mines at the end of a game."""
        for row in self.grid:
            for cell in row:
                if cell.is_mine:
                    cell.is_revealed = True


# =============================================================================
# 4. Game Class
# =============================================================================
class Game:
    """Main class to manage the game loop, state, and rendering."""

    def __init__(self, num_mines: int, difficulty: str):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("EECS 581 Minesweeper")

        # Fonts
        self.header_font = pygame.font.Font(None, 50)
        self.cell_font = pygame.font.Font(None, 32)
        self.status_font = pygame.font.Font(None, 30)
        self.label_font = pygame.font.Font(None, 24)

        # Pre-rendered static text
        self.title_text_surface = self.header_font.render("MINESWEEPER", True, COLOR_TEXT_HEADER)
        self.title_text_rect = self.title_text_surface.get_rect(center=(SCREEN_WIDTH / 2, 40))

        # Restart button
        self.restart_text_surface = self.status_font.render("Restart", True, COLOR_TEXT_HEADER)
        self.restart_button_rect = pygame.Rect(SCREEN_WIDTH - 120, 30, 100, 40)
        self.restart_text_rect = self.restart_text_surface.get_rect(center=self.restart_button_rect.center)

        self.difficulty = difficulty
        self.num_mines = num_mines
        self.last_game_status = None  # To track the result of the previous game
        self.reset_game()

    def reset_game(self):
        """Resets the game to its initial state, recording the previous game's result."""
        # Before resetting, check if a game was just completed and record its status.
        # The hasattr check ensures this doesn't run on the very first initialization.
        if hasattr(self, 'game_over') and self.game_over:
            self.last_game_status = "Victory!" if self.win else "Loss"

        self.board = Board(self.num_mines, self.difficulty)
        self.game_over = False
        self.win = False
        self.first_click = True
        self.running = True
        self.flags_placed = 0

    def run(self):
        """The main game loop."""
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Processes all user inputs."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.restart_button_rect.collidepoint(event.pos):
                    self.reset_game()
                    return

                if not self.game_over:
                    x, y = event.pos
                    # Adjust click coordinates for the label area offset
                    if x > LABEL_AREA_SIZE and y > HEADER_HEIGHT + LABEL_AREA_SIZE:
                        col = (x - LABEL_AREA_SIZE) // CELL_SIZE
                        row = (y - HEADER_HEIGHT - LABEL_AREA_SIZE) // CELL_SIZE

                        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                            cell = self.board.grid[row][col]
                            if event.button == 1 and not cell.is_flagged:
                                if self.first_click:
                                    self.board.place_mines(row, col)
                                    self.first_click = False

                                self.board.reveal_cell(row, col)
                                if cell.is_mine:
                                    self.game_over = True
                                    self.win = False
                                    self.board.reveal_all_mines()
                                    return

                                cell = self.board.uncover_cell() # Always 
                                if cell.is_mine:
                                    self.game_over = True
                                    self.win = False
                                    self.board.reveal_all_mines()

                            elif event.button == 3 and not cell.is_revealed:
                                if not cell.is_flagged and self.flags_placed < self.num_mines:
                                    cell.is_flagged = True
                                    self.flags_placed += 1
                                elif cell.is_flagged:
                                    cell.is_flagged = False
                                    self.flags_placed -= 1

                                # cell = self.board.uncover_cell() # Always 
                                # if cell.is_mine:
                                #     self.game_over = True
                                #     self.win = False
                                #     self.board.reveal_all_mines()

    def update(self):
        """Updates the game state, such as checking for a win."""
        if not self.game_over and not self.first_click:
            self.check_win_condition()

    def check_win_condition(self):
        """Checks if all non-mine cells have been revealed."""
        revealed_count = sum(1 for r in self.board.grid for c in r if c.is_revealed and not c.is_mine)
        if revealed_count == (GRID_SIZE * GRID_SIZE) - self.num_mines:
            self.game_over = True
            self.win = True

    def draw(self):
        """Renders all game elements to the screen."""
        self.screen.fill(COLOR_BG)
        self.draw_header()
        self.draw_labels()
        for row in self.board.grid:
            for cell in row:
                cell.draw(self.screen, self.cell_font)
        pygame.display.flip()

    def draw_header(self):
        """Draws the top header panel."""
        pygame.draw.rect(self.screen, COLOR_HEADER_BG, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))
        self.screen.blit(self.title_text_surface, self.title_text_rect)
        flags_remaining = self.num_mines - self.flags_placed
        flag_text = self.status_font.render(f"Mines: {flags_remaining}", True, COLOR_TEXT)
        self.screen.blit(flag_text, (20, 35))

        # Display last game status if available
        if self.last_game_status:
            last_game_text = self.status_font.render(f"Last Game: {self.last_game_status}", True, COLOR_TEXT)
            self.screen.blit(last_game_text, (20, 65))

        pygame.draw.rect(self.screen, COLOR_RESTART_BUTTON, self.restart_button_rect, border_radius=8)
        self.screen.blit(self.restart_text_surface, self.restart_text_rect)
        status_text_str = "Victory!" if self.win else "Game Over" if self.game_over else "Playing..."
        status_text = self.status_font.render(status_text_str, True, COLOR_TEXT)
        status_rect = status_text.get_rect(center=(SCREEN_WIDTH / 2, 80))
        self.screen.blit(status_text, status_rect)

    def draw_labels(self):
        """Draws the A-J column and 1-10 row labels."""
        for i in range(GRID_SIZE):
            # Column labels (A-J)
            col_text = self.label_font.render(chr(ord('A') + i), True, COLOR_TEXT)
            col_rect = col_text.get_rect(
                center=(LABEL_AREA_SIZE + i * CELL_SIZE + CELL_SIZE / 2, HEADER_HEIGHT + LABEL_AREA_SIZE / 2))
            self.screen.blit(col_text, col_rect)
            # Row labels (1-10)
            row_text = self.label_font.render(str(i + 1), True, COLOR_TEXT)
            row_rect = row_text.get_rect(
                center=(LABEL_AREA_SIZE / 2, HEADER_HEIGHT + LABEL_AREA_SIZE + i * CELL_SIZE + CELL_SIZE / 2))
            self.screen.blit(row_text, row_rect)

T = TypeVar("T")

def get_val(prompt: str,
            cast: Callable[[str], T],
            *,
            validate: Optional[Callable[[T], bool]] = None,
            error: Optional[str] = None
            ) -> T:
    while True:
        user_input = input(prompt)
        try:
            val = cast(user_input)
            if validate is not None and validate(val):
                return val
            else:
                print(error)
        except ValueError:
            print(f"Invalid input. Please enter a valid {cast}.")

# =============================================================================
# 5. Main Execution Block
# =============================================================================
if __name__ == "__main__":
    validate_mine = lambda x: x >= 10 and x <= 20
    error_mine = "Invalid range. Please enter a number between 10 and 20."
    num_mines = get_val("Enter a number of mines [10-20]: ", int, validate=validate_mine, error=error_mine)

    def validate_difficulty(val: str):
        val = val.lower().strip()
        return val in ("easy", "medium", "hard")
    error_difficulty = "Invalid difficulty. Please enter a difficulty of easy, medium, or hard."
    difficulty = get_val("Enter a difficulty [Easy, Medium, Hard]: ", str, validate=validate_difficulty, error=error_difficulty)

    game = Game(num_mines, difficulty)
    game.run()


