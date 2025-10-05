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

"""
================================================================================
Module:    minesweeper.py   (Maintenance Release for EECS 581 Project 1)
Function:  Launches and runs a 10x10 Minesweeper game using Pygame with:
           • AI Solver feature (auto cell selection via timer; easy/medium/hard)
           • Sound Effects feature (click, flag, flood/cascade, explosion, win,
             restart) integrated into game events.

Classes:   Audio  – façade over pygame.mixer; loads and plays named SFX.
           Cell   – represents one square; state + drawing.
           Board  – builds 10×10 grid; mine placement; adjacency; flood reveal;
                    AI helper strategies (easy/medium/hard).
           Game   – main loop; event handling; rendering; win/lose; SFX/AI glue.

Inputs:    • Console at startup:
              - Mine count (10–20)
              - Play against AI? (y/n)   → enables/disables solver timer
              - Difficulty: easy | medium | hard
           • Mouse:
              - Left click: reveal cell
              - Right click: toggle flag
              - Restart button (top-right): reset game

Outputs:   • Rendered game window with labels and status
           • Sound effects for key events (click/flag/cascade/boom/win/restart)

External Sources & Attribution:
           • Sound asset files in ./sfx/ :
              - mouse-click-153941.mp3, pop-94319.mp3, fast-whoosh-118248.mp3,
                explosion-6055.mp3, success-fanfare-trumpets-6185.mp3

Original Authors (Base Project v1.2):  Asa Maker & Zach Sevart
Original Creation/Modification Dates:  2025-09-10 / 2025-09-15
Maintainer(s) – This Release:          Aniketh and Yaeesh
Creation Date – This Release:           2025-10-02

"""

from typing import Callable, Generator, Literal, TypeVar, Optional
import pygame
import random
import sys

# -----------------------------------------------------------------------------
# Type aliases
# -----------------------------------------------------------------------------
Difficulty = Literal['easy', 'medium', 'hard']
Self = TypeVar('Self')  # used for decorator type annotation


# =============================================================================
# 1. Game Constants and Configuration
# =============================================================================
# Window/grid dimensions and a neutral color palette used by the renderer.
GRID_SIZE = 10
CELL_SIZE = 50        # Slightly reduced to make room for label gutters
LABEL_AREA_SIZE = 40  # Gutter for A–J and 1–10 labels
GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE
HEADER_HEIGHT = 100   # Header area for title, status, restart

SCREEN_WIDTH = GRID_WIDTH + LABEL_AREA_SIZE
SCREEN_HEIGHT = GRID_HEIGHT + HEADER_HEIGHT + LABEL_AREA_SIZE

# Colors (UI theme + per-number tinting for adjacent mine counts)
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

# border to highlight the last AI-chosen cell
BORDER_THICKNESS = 2
BORDER_COLOR = (255, 255, 0)

# AI solver cadence
AI_SOLVER_TIMEOUT = 500


# =============================================================================
# 1.5 Audio Class (Sound Effects Feature)  [Maintained – new for this release]
# =============================================================================
class Audio:
    """
    Loads named sound assets once and exposes
    play(name) for the Game layer. If mixer init fails (e.g., no audio device),
    audio stays disabled and the game remains playable without sound.

    Event names → assets (located under ./sfx/):
      'click'   : safe single reveal (left click)
      'flag'    : flag toggle (place/remove)
      'cascade' : flood/chain reveal of zero-adjacent cells
      'boom'    : mine clicked (explosion)
      'win'     : victory
      'restart' : restart button pressed
    """

    def __init__(self):
        # Initialize audio with typical settings;
        self.enabled = True
        try:
            pygame.mixer.pre_init(44100, -16, 2, 256)  # sample rate, 16-bit, stereo, buffer
            pygame.mixer.init()
        except Exception as e:
            print(f"[Audio disabled] {e}")
            self.enabled = False
            return

        def load(path: str):
            # Load each sound if audio is enabled; otherwise store None
            return pygame.mixer.Sound(path) if self.enabled else None

        # Logical event names map to loaded Sound objects
        self.sounds = {
            "click":     load("sfx/mouse-click-153941.mp3"),
            "flag":      load("sfx/pop-94319.mp3"),
            "cascade":   load("sfx/fast-whoosh-118248.mp3"),
            "boom":      load("sfx/explosion-6055.mp3"),
            "win":       load("sfx/success-fanfare-trumpets-6185.mp3"),
            "restart":   load("sfx/mouse-click-153941.mp3"),
        }

    def play(self, name: str):
        """Play by logical name if audio is enabled and the asset exists."""
        if self.enabled and (snd := self.sounds.get(name)):
            snd.play()


# =============================================================================
# 2. Cell Class  [Original project]
# =============================================================================
class Cell:
    """Represents one square in the grid and knows how to draw itself."""

    def __init__(self, row: int, col: int):
        # Immutable grid coordinates
        self.row = row
        self.col = col

        # Pixel coordinates adjusted by header + label gutters
        self.x = col * CELL_SIZE + LABEL_AREA_SIZE
        self.y = row * CELL_SIZE + HEADER_HEIGHT + LABEL_AREA_SIZE

        # Gameplay state
        self.is_mine = False
        self.is_revealed = False
        self.is_flagged = False
        self.adjacent_mines = 0

        # Optional visual border (used to show the AI's last pick)
        self._border = False

    @property
    def border(self) -> bool:
        return self._border

    @border.setter
    def border(self, value: bool) -> None:
        self._border = value

    def draw(self, screen, font) -> None:
        """Render this cell based on its current state."""
        rect = pygame.Rect(self.x, self.y, CELL_SIZE, CELL_SIZE)

        if self.is_revealed:
            pygame.draw.rect(screen, COLOR_CELL_UNCOVERED, rect)
            if self.is_mine:
                self.draw_mine(screen, rect)
            elif self.adjacent_mines > 0:
                text_surface = font.render(str(self.adjacent_mines), True,
                                           COLOR_NUMBERS[self.adjacent_mines])
                text_rect = text_surface.get_rect(center=rect.center)
                screen.blit(text_surface, text_rect)
        else:
            pygame.draw.rect(screen, COLOR_CELL_COVERED, rect)
            if self.is_flagged:
                self.draw_flag(screen, rect)

        # Optional highlight (AI last chosen)
        if self.border:
            pygame.draw.rect(screen, BORDER_COLOR, rect, BORDER_THICKNESS)

        # Always draw cell border lines
        pygame.draw.rect(screen, COLOR_GRID_LINES, rect, 1)

    def draw_flag(self, screen, rect) -> None:
        """Draw a simple flag icon centered in this cell."""
        center_x, center_y = rect.center
        flag_pole = pygame.Rect(center_x - 1, center_y - 12, 3, 24)
        flag_triangle = [(center_x, center_y - 12),
                         (center_x + 12, center_y - 8),
                         (center_x, center_y - 4)]
        pygame.draw.rect(screen, COLOR_TEXT, flag_pole)
        pygame.draw.polygon(screen, COLOR_FLAG, flag_triangle)

    def draw_mine(self, screen, rect) -> None:
        """Draw a mine (circle) centered in this cell."""
        pygame.draw.circle(screen, COLOR_MINE, rect.center, int(CELL_SIZE * 0.3))
        pygame.draw.circle(screen, COLOR_BG, rect.center, int(CELL_SIZE * 0.15))


# =============================================================================
# 3. Board Class  [Original + Maintained (AI helpers)]
# =============================================================================
class Board:
    """
    Manages the 10×10 grid and core game logic:
      - grid construction and mine placement (first-click safe zone)
      - adjacent mine counts
      - recursive flood reveal for zero-adjacent cells
    Maintenance additions:
      - neighbors() helper
      - AI strategies: uncover_cell_easy / _medium / _hard
      - wrap_uncover() decorator to unify AI behavior & visual border
    """

    def __init__(self, num_mines: int, difficulty: str):
        # Select the AI strategy method based on difficulty label
        self.uncover_cell = getattr(self, f"uncover_cell_{difficulty}")
        self.grid = [[Cell(row, col) for col in range(GRID_SIZE)] for row in range(GRID_SIZE)]
        self.num_mines = num_mines
        self.last_cell: Optional[Cell] = None  # track last AI-picked cell

    @staticmethod
    def wrap_uncover(func: Callable[[Self], Cell]):
        """
        Decorator for AI 'uncover_cell_*' strategies.
        Responsibilities:
          • Call the wrapped strategy to pick a cell.
          • Clear previous highlight; set border=True on the chosen cell.
          • If not the very first pick (mines not yet placed), also reveal it.
        """
        def wrapper(self, is_first: bool = False) -> Cell:
            cell = func(self)
            if self.last_cell:
                self.last_cell.border = False
            cell.border = True
            self.last_cell = cell
            if not is_first:
                self.reveal_cell(cell.row, cell.col)
            return cell
        return wrapper

    def place_mines(self, first_click_row: int, first_click_col: int) -> None:
        """
        Randomly place mines AFTER the first click, guaranteeing the clicked cell
        and its 8 neighbors are safe (standard Minesweeper UX).
        """
        # Build a "safe zone" around the first click
        safe_zone = set()
        for r_offset in range(-1, 2):
            for c_offset in range(-1, 2):
                r, c = first_click_row + r_offset, first_click_col + c_offset
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    safe_zone.add((r, c))

        # Choose mine positions outside the safe zone
        possible = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
                    if (r, c) not in safe_zone]
        mine_locations = random.sample(possible, self.num_mines)

        # Mark mines and compute adjacency
        for r, c in mine_locations:
            self.grid[r][c].is_mine = True
        self.calculate_all_adjacent_mines()

    def calculate_all_adjacent_mines(self) -> None:
        """Compute and cache adjacent mine counts for each non-mine cell."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if not self.grid[r][c].is_mine:
                    self.grid[r][c].adjacent_mines = self.count_adjacent_mines(r, c)

    def count_adjacent_mines(self, row: int, col: int) -> int:
        """Return the number of mines of (row, col)."""
        count = 0
        for r_offset in range(-1, 2):
            for c_offset in range(-1, 2):
                if r_offset == 0 and c_offset == 0:
                    continue
                r, c = row + r_offset, col + c_offset
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and self.grid[r][c].is_mine:
                    count += 1
        return count

    def reveal_cell(self, row: int, col: int) -> None:
        """
        Reveal a cell and recursively flood adjacent zero-count cells.
        Stops when encountering edges, flagged cells, or already revealed cells.
        """
        cell = self.grid[row][col]
        if cell.is_revealed or cell.is_flagged:
            return
        cell.is_revealed = True

        # Flood expansion when the cell has no neighboring mines
        if cell.adjacent_mines == 0 and not cell.is_mine:
            for r_offset in range(-1, 2):
                for c_offset in range(-1, 2):
                    if r_offset == 0 and c_offset == 0:
                        continue
                    r, c = row + r_offset, col + c_offset
                    if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                        self.reveal_cell(r, c)

    def reveal_all_mines(self) -> None:
        """Show every mine (used on loss)."""
        for row in self.grid:
            for cell in row:
                if cell.is_mine:
                    cell.is_revealed = True

    def neighbors(self, cell: Cell) -> Generator[Cell, None, None]:
        """Yield the 8 neighbors around a given cell (bounds-checked)."""
        for r_offset in range(-1, 2):
            for c_offset in range(-1, 2):
                if r_offset == 0 and c_offset == 0:
                    continue
                r, c = cell.row + r_offset, cell.col + c_offset
                if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
                    yield self.grid[r][c]

    # ------------------------------ AI Strategies -----------------------------

    @wrap_uncover
    def uncover_cell_easy(self) -> Cell:
        """
        Easy AI: pick a random covered, unflagged cell uniformly.
        Used as fallback when no heuristics apply.
        """
        print("Uncovering cell (Easy)")
        r = random.randint(0, GRID_SIZE - 1)
        c = random.randint(0, GRID_SIZE - 1)
        cell = self.grid[r][c]
        while cell.is_revealed or cell.is_flagged:
            r = random.randint(0, GRID_SIZE - 1)
            c = random.randint(0, GRID_SIZE - 1)
            cell = self.grid[r][c]
        print(f"Picked cell {r + 1}:{chr(c + 65)}")
        return cell

    @wrap_uncover
    def uncover_cell_medium(self) -> Cell:
        """
        Medium AI: apply simple constraints around numbered revealed cells.
          - If flags placed equal the number, remaining covered neighbors are safe.
          - If covered neighbors count equals (number - flags), mark those as flags.
        """
        print("Uncovering cell (Medium)")
        safe_cells = set()
        flag_cells = set()

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell = self.grid[r][c]
                if cell.is_revealed and cell.adjacent_mines > 0:
                    covered_neighbors = [n for n in self.neighbors(cell)
                                         if not n.is_revealed and not n.is_flagged]
                    flagged_neighbors = [n for n in self.neighbors(cell) if n.is_flagged]

                    # All mines accounted for by flags → rest are safe
                    if len(flagged_neighbors) == cell.adjacent_mines:
                        safe_cells.update(covered_neighbors)

                    # If remaining covered must be mines → flag them
                    if len(covered_neighbors) == cell.adjacent_mines - len(flagged_neighbors):
                        flag_cells.update(covered_neighbors)

        # Prefer flagging when forced; otherwise pick a deduced safe cell
        if flag_cells:
            cell = random.choice(list(flag_cells))
            print(f"Picked cell {cell.row + 1}:{chr(cell.col + 65)} (flagged)")
            cell.is_flagged = True
            return cell

        if safe_cells:
            cell = random.choice(list(safe_cells))
            print(f"Picked cell {cell.row + 1}:{chr(cell.col + 65)} (safe)")
            return cell

        # No deductions → fall back to random (but mark is_first for decorator)
        return self.uncover_cell_easy(is_first=True)

    @wrap_uncover
    def uncover_cell_hard(self) -> Cell:
        """
        Hard AI (placeholder heuristic): choose any cell that is neither revealed
        nor flagged and (currently appears) non-mine; in a full solver this would
        incorporate probabilistic inference. Kept simple for project scope.
        """
        print("Uncovering cell (Hard)")
        candidates = []
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                cell = self.grid[r][c]
                is_safe = not cell.is_revealed and not cell.is_flagged and not cell.is_mine
                if is_safe:
                    candidates.append(cell)

        cell = random.choice(candidates)
        print(f"Picked cell {cell.row + 1}:{chr(cell.col + 65)}")
        return cell


# =============================================================================
# 4. Game Class  [Maintained – integrates AI + SFX]
# =============================================================================
class Game:
    """
    Orchestrates the window, event loop, labels, and end states.
    Owns Audio (composition) and manages Board. Integrates SFX triggers at:
      - restart, flag toggle, safe click, cascade/flood, explosion, win.
    Also owns the AI auto-pick timer when not in interactive mode.
    """
    AUTO_PICK = pygame.USEREVENT + 1  # custom event id for AI solver ticks

    def __init__(self, num_mines: int, difficulty: str, is_interactive: bool):
        # Init pygame subsystems
        pygame.init()
        pygame.font.init()

        # Composition: Game owns Audio; if this fails, sounds are silently disabled
        self.audio = Audio()

        # Screen setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("EECS 581 Minesweeper")

        # Fonts
        self.header_font = pygame.font.Font(None, 50)
        self.cell_font = pygame.font.Font(None, 32)
        self.status_font = pygame.font.Font(None, 30)
        self.label_font = pygame.font.Font(None, 24)

        # Pre-rendered static title
        self.title_text_surface = self.header_font.render("MINESWEEPER", True, COLOR_TEXT_HEADER)
        self.title_text_rect = self.title_text_surface.get_rect(center=(SCREEN_WIDTH / 2, 40))

        # Restart button UI
        self.restart_text_surface = self.status_font.render("Restart", True, COLOR_TEXT_HEADER)
        self.restart_button_rect = pygame.Rect(SCREEN_WIDTH - 120, 30, 100, 40)
        self.restart_text_rect = self.restart_text_surface.get_rect(center=self.restart_button_rect.center)

        # Gameplay config/state
        self.num_mines = num_mines
        self.difficulty = difficulty
        self.is_interactive = is_interactive
        self.last_game_status = None  # display result of previous game in header

        self.reset_game()

    def reset_game(self) -> None:
        """
        Reset game to initial state. If a game just concluded, record
        its result to show in the header on the next run.
        """
        if hasattr(self, 'game_over') and self.game_over:
            self.last_game_status = "Victory!" if self.win else "Loss"

        self.board = Board(self.num_mines, self.difficulty)
        self.game_over = False
        self.win = False
        self.first_click = True
        self.running = True
        self.flags_placed = 0

    def run(self) -> None:
        """
        Main loop:
          - In non-interactive mode, start the AI timer (AUTO_PICK every N ms).
          - Process events (mouse, quit, AI picks).
          - Update game state and render each frame.
        """
        if not self.is_interactive:
            pygame.time.set_timer(self.AUTO_PICK, AI_SOLVER_TIMEOUT)

        while self.running:
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit()

    def handle_events(self) -> None:
        """Centralized event dispatcher for mouse/AI/quit events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # -------------------------- AI auto-pick branch ---------------------
            if event.type == self.AUTO_PICK and not self.is_interactive and not self.game_over:
                flags_before = self.flags_placed

                # Track new reveals to decide between click vs cascade SFX
                pre_revealed = sum(1 for r in self.board.grid for c in r if c.is_revealed)
                cell = self.board.uncover_cell(is_first=self.first_click)
                post_revealed = sum(1 for r in self.board.grid for c in r if c.is_revealed)

                # If the AI flagged something, play the flag SFX
                if flags_before < self.flags_placed:
                    self.audio.play("flag")
                # Otherwise, if we actually revealed cells, pick click/cascade SFX
                elif cell.is_revealed:
                    if post_revealed - pre_revealed > 5:
                        self.audio.play("cascade")
                    else:
                        self.audio.play("click")

                # First AI pick seeds mines and reveals (safe first click)
                if self.first_click:
                    self.board.place_mines(cell.row, cell.col)
                    self.board.reveal_cell(cell.row, cell.col)
                    self.first_click = False

                # Loss condition for AI (revealed mine not flagged)
                if cell.is_mine and not cell.is_flagged:
                    self.game_over = True
                    self.win = False
                    self.board.reveal_all_mines()
                    self.audio.play("boom")
                continue  # Skip mouse handling on this loop iteration

            # ---------------------------- Mouse branch --------------------------
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Restart button
                if self.restart_button_rect.collidepoint(event.pos):
                    self.audio.play("restart")
                    self.reset_game()
                    return

                if not self.game_over:
                    x, y = event.pos
                    # Ensure clicks are within the board area (not headers/labels)
                    if x > LABEL_AREA_SIZE and y > HEADER_HEIGHT + LABEL_AREA_SIZE:
                        col = (x - LABEL_AREA_SIZE) // CELL_SIZE
                        row = (y - HEADER_HEIGHT - LABEL_AREA_SIZE) // CELL_SIZE

                        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                            cell = self.board.grid[row][col]

                            # Right-click: toggle flag
                            if event.button == 3 and not cell.is_revealed:
                                if not cell.is_flagged and self.flags_placed < self.num_mines:
                                    cell.is_flagged = True
                                    self.flags_placed += 1
                                    self.audio.play("flag")
                                elif cell.is_flagged:
                                    cell.is_flagged = False
                                    self.flags_placed -= 1
                                    self.audio.play("flag")

                                # allow an immediate AI follow-up action
                                cell2 = self.board.uncover_cell()
                                if cell2.is_mine and not cell2.is_flagged:
                                    self.game_over = True
                                    self.win = False
                                    self.board.reveal_all_mines()
                                    self.audio.play("boom")

                            # Left-click: reveal (ignore if flagged)
                            if event.button == 1 and not cell.is_flagged:
                                if self.first_click:
                                    # Seed mines on the first reveal to guarantee safety
                                    self.board.place_mines(row, col)
                                    self.first_click = False

                                # Choose SFX based on number of newly opened cells
                                pre_revealed = sum(1 for r in self.board.grid for c in r if c.is_revealed)
                                self.board.reveal_cell(row, col)
                                post_revealed = sum(1 for r in self.board.grid for c in r if c.is_revealed)

                                if cell.is_mine:
                                    self.game_over = True
                                    self.win = False
                                    self.board.reveal_all_mines()
                                    self.audio.play("boom")
                                    return
                                else:
                                    if post_revealed - pre_revealed > 5:
                                        self.audio.play("cascade")
                                    else:
                                        self.audio.play("click")

                                # Optional: allow an immediate AI follow-up action
                                cell2 = self.board.uncover_cell()
                                if cell2.is_mine and not cell2.is_flagged:
                                    self.game_over = True
                                    self.win = False
                                    self.board.reveal_all_mines()
                                    self.audio.play("boom")

    def update(self) -> None:
        """
        State updates independent of input:
          - When we first click we delay win checks until mines exist.
          - If win state flips from False → True, play the win sound once.
        """
        if not self.game_over and not self.first_click:
            was_won = self.win
            self.check_win_condition()
            # Edge-triggered 'win' SFX: only play on the transition to win=True
            if (not was_won) and self.win:
                self.audio.play("win")

    def check_win_condition(self) -> None:
        """Win when all non-mine cells are revealed."""
        revealed_count = sum(1 for r in self.board.grid for c in r
                             if c.is_revealed and not c.is_mine)
        if revealed_count == (GRID_SIZE * GRID_SIZE) - self.num_mines:
            self.game_over = True
            self.win = True

    def draw(self) -> None:
        """Render header, labels, and the 10×10 grid to the screen."""
        self.screen.fill(COLOR_BG)
        self.draw_header()
        self.draw_labels()
        for row in self.board.grid:
            for cell in row:
                cell.draw(self.screen, self.cell_font)
        pygame.display.flip()

    def draw_header(self) -> None:
        """Draw the title, status text, prior result, and restart button."""
        pygame.draw.rect(self.screen, COLOR_HEADER_BG, (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))
        self.screen.blit(self.title_text_surface, self.title_text_rect)

        flags_remaining = self.num_mines - self.flags_placed
        flag_text = self.status_font.render(f"Mines: {flags_remaining}", True, COLOR_TEXT)
        self.screen.blit(flag_text, (20, 35))

        # Show last game's result if we have one
        if self.last_game_status:
            last_game_text = self.status_font.render(f"Last Game: {self.last_game_status}", True, COLOR_TEXT)
            self.screen.blit(last_game_text, (20, 65))

        # Restart button
        pygame.draw.rect(self.screen, COLOR_RESTART_BUTTON, self.restart_button_rect, border_radius=8)
        self.screen.blit(self.restart_text_surface, self.restart_text_rect)

        # Current status text (centered)
        status_text_str = "Victory!" if self.win else "Game Over" if self.game_over else "Playing..."
        status_text = self.status_font.render(status_text_str, True, COLOR_TEXT)
        status_rect = status_text.get_rect(center=(SCREEN_WIDTH / 2, 80))
        self.screen.blit(status_text, status_rect)

    def draw_labels(self) -> None:
        """Draw A–J along the top gutter and 1–10 along the left gutter."""
        for i in range(GRID_SIZE):
            # Columns: A, B, ..., J
            col_text = self.label_font.render(chr(ord('A') + i), True, COLOR_TEXT)
            col_rect = col_text.get_rect(
                center=(LABEL_AREA_SIZE + i * CELL_SIZE + CELL_SIZE / 2,
                        HEADER_HEIGHT + LABEL_AREA_SIZE / 2))
            self.screen.blit(col_text, col_rect)

            # Rows: 1, 2, ..., 10
            row_text = self.label_font.render(str(i + 1), True, COLOR_TEXT)
            row_rect = row_text.get_rect(
                center=(LABEL_AREA_SIZE / 2,
                        HEADER_HEIGHT + LABEL_AREA_SIZE + i * CELL_SIZE + CELL_SIZE / 2))
            self.screen.blit(row_text, row_rect)


# =============================================================================
# 5. CLI Helpers and Main Entrypoint
# =============================================================================
T = TypeVar("T")

def get_val(prompt: str,
            cast: Callable[[str], T],
            *,
            validate: Callable[[T], bool] = lambda _: True,
            error: Optional[str] = None) -> T:
    """
    Prompt -> cast -> validate loop.
      - cast:     converts raw input string to type T (e.g., int or bool)
      - validate: returns True if value is acceptable; otherwise prints 'error'
                  and re-prompts.
    """
    while True:
        user_input = input(prompt)
        try:
            val = cast(user_input)
            if validate(val):
                return val
            else:
                print(error)
        except ValueError:
            print(f"Invalid input. Please enter a valid {cast}.")


# Main execution block: collect settings, construct Game, and run the loop.
if __name__ == "__main__":
    # --- Mine count -----------------------------------------------------------
    validate_mine = lambda x: x >= 10 and x <= 20
    error_mine = "Invalid range. Please enter a number between 10 and 20."
    num_mines = get_val("Enter a number of mines [10-20]: ",
                        int, validate=validate_mine, error=error_mine)

    # --- Interactive vs AI-driven -------------------------------------------
    def cast_interactive(val: str) -> bool:
        # Treat 'y'/'yes' or empty as interactive=True for a friendlier default
        return val.strip().lower() in ("yes", "y", "")

    is_interactive = get_val("Play against AI [y/n]: ", cast_interactive)

    # --- Difficulty label ----------------------------------------------------
    def validate_difficulty(val: str) -> bool:
        val = val.lower().strip()
        return val in ("easy", "medium", "hard")

    error_difficulty = "Invalid difficulty. Please enter a difficulty of easy, medium, or hard."
    difficulty = get_val("Enter a difficulty [easy, medium, hard]: ",
                         str, validate=validate_difficulty, error=error_difficulty)

    # --- Launch --------------------------------------------------------------
    game = Game(num_mines, difficulty, is_interactive)
    game.run()
