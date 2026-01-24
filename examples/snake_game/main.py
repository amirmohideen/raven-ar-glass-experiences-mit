# Nokia Snake Game for Raven Glass
# A classic snake game with gaze-based controls

from enum import Enum
from random import randint

from PySide6.QtCore import Qt, QObject, QEvent

from raven_framework import RavenApp, RunApp, TextBox, Container, Button
from raven_framework.components.cards import TextCardWithButton, TextCardWithTwoButtons
from raven_framework.helpers.routine import Routine
from raven_framework.helpers.animation_utils import fade_in


# Game constants
GRID_SIZE = 20  # 20x20 grid
GRID_CELL_SIZE = 20  # Each cell is 20x20 pixels
GAME_SPEED = 300  # Milliseconds between moves
CONTAINER_WIDTH = 450
WALL_THICKNESS = 5


# Direction enum
class Direction(Enum):
    """Snake movement directions."""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)


# Game state enum
class GameState(Enum):
    """Game state enumeration."""
    MENU = "menu"
    TUTORIAL = "tutorial"
    PLAYING = "playing"
    GAME_OVER = "game_over"


class SnakeGame(RavenApp):
    """Classic Nokia Snake game for Raven Glass."""

    def __init__(self, parent=None) -> None:
        """Initialize the Snake Game application."""
        super().__init__(parent)

        # Game state
        self.game_state = GameState.MENU
        self.score = 0
        self.high_score = 0

        # Snake and food
        self.snake = [(10, 10), (10, 11), (10, 12)]  # Head first
        self.direction = Direction.UP
        self.next_direction = Direction.UP
        self.food = self._generate_food()

        # Game routine
        self.game_routine = None

        # Mouse tracking
        self.cursor_x = 0
        self.cursor_y = 0

        # Install event filter for mouse tracking
        self.app.setMouseTracking(True)
        self.app.installEventFilter(self)

        # Initialize UI
        self.init_ui()
        fade_in(self.app)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Track mouse movement and update snake direction."""
        if event.type() == QEvent.Type.MouseMove and self.game_state == GameState.PLAYING:
            # Get cursor position relative to the app
            pos = event.position()
            self.cursor_x = pos.x()
            self.cursor_y = pos.y()
            
            # Update direction based on cursor position
            self._update_direction_from_cursor()
        
        return super().eventFilter(obj, event)

    def _update_direction_from_cursor(self):
        """Update snake direction based on cursor position relative to snake head."""
        if not self.snake:
            return
        
        # Get snake head position in pixels (account for wall offset)
        head_x, head_y = self.snake[0]
        head_pixel_x = WALL_THICKNESS + (head_x * GRID_CELL_SIZE) + (GRID_CELL_SIZE / 2)
        head_pixel_y = WALL_THICKNESS + (head_y * GRID_CELL_SIZE) + (GRID_CELL_SIZE / 2)
        
        # Calculate difference between cursor and snake head
        dx = self.cursor_x - head_pixel_x
        dy = self.cursor_y - head_pixel_y
        
        # Determine primary direction (larger difference wins)
        if abs(dx) > abs(dy):
            # Horizontal movement
            if dx > 0:
                new_direction = Direction.RIGHT
            else:
                new_direction = Direction.LEFT
        else:
            # Vertical movement
            if dy > 0:
                new_direction = Direction.DOWN
            else:
                new_direction = Direction.UP
        
        # Apply direction (prevent reversing)
        self.set_direction(new_direction)

    def _generate_food(self):
        """Generate food at random position not occupied by snake."""
        while True:
            food = (randint(0, GRID_SIZE - 1), randint(0, GRID_SIZE - 1))
            if food not in self.snake:
                return food

    def _update_game(self):
        """Update game state (called by routine each frame)."""
        # Update direction if a new one is queued
        self.direction = self.next_direction

        # Calculate new head position
        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)

        # Check wall collision
        if (
            new_head[0] < 0
            or new_head[0] >= GRID_SIZE
            or new_head[1] < 0
            or new_head[1] >= GRID_SIZE
        ):
            self._end_game()
            return

        # Check self collision
        if new_head in self.snake:
            self._end_game()
            return

        # Add new head
        self.snake.insert(0, new_head)

        # Check food collision
        if new_head == self.food:
            self.score += 10
            self.food = self._generate_food()
        else:
            # Remove tail if no food eaten
            self.snake.pop()

        # Redraw game
        self._draw_game()

    def _draw_game(self):
        """Draw the game board."""
        # Clear and rebuild UI
        self.app.clear()

        # Create game board canvas
        board_width = GRID_SIZE * GRID_CELL_SIZE
        board_height = GRID_SIZE * GRID_CELL_SIZE

        board = Container(
            width=board_width, height=board_height, background_color="#000000"
        )

        # Draw red walls (borders)
        # Top wall
        top_wall = Container(width=board_width + WALL_THICKNESS * 2, height=WALL_THICKNESS, background_color="#FF0000")
        # Bottom wall
        bottom_wall = Container(width=board_width + WALL_THICKNESS * 2, height=WALL_THICKNESS, background_color="#FF0000")
        # Left wall
        left_wall = Container(width=WALL_THICKNESS, height=board_height + WALL_THICKNESS * 2, background_color="#FF0000")
        # Right wall
        right_wall = Container(width=WALL_THICKNESS, height=board_height + WALL_THICKNESS * 2, background_color="#FF0000")

        # Draw food
        fx, fy = self.food
        food_widget = Container(
            width=GRID_CELL_SIZE,
            height=GRID_CELL_SIZE,
            background_color="#FFFF00",
        )
        board.add(food_widget, x=fx * GRID_CELL_SIZE, y=fy * GRID_CELL_SIZE)

        # Draw snake
        for i, (sx, sy) in enumerate(self.snake):
            # Head is brighter
            if i == 0:
                color = "#00FF00"
            else:
                color = "#00AA00"

            snake_segment = Container(
                width=GRID_CELL_SIZE - 1,
                height=GRID_CELL_SIZE - 1,
                background_color=color,
            )
            board.add(snake_segment, x=sx * GRID_CELL_SIZE, y=sy * GRID_CELL_SIZE)

        # Add board to app
        self.app.add(top_wall, x=0, y=0)
        self.app.add(left_wall, x=0, y=0)
        self.app.add(board, x=WALL_THICKNESS, y=WALL_THICKNESS)
        self.app.add(bottom_wall, x=0, y=board_height + WALL_THICKNESS)
        self.app.add(right_wall, x=board_width + WALL_THICKNESS, y=0)

        # Add score display
        score_text = TextBox(
            text=f"Score: {self.score}", text_color="#FFFFFF", font_size=24
        )
        self.app.add(score_text, x=WALL_THICKNESS + 10, y=WALL_THICKNESS + 10)

        # Add direction control buttons
        up_button = Button(center_text="↑", width=60, height=50)
        up_button.on_clicked(self.set_direction, Direction.UP)

        down_button = Button(center_text="↓", width=60, height=50)
        down_button.on_clicked(self.set_direction, Direction.DOWN)

        left_button = Button(center_text="←", width=60, height=50)
        left_button.on_clicked(self.set_direction, Direction.LEFT)

        right_button = Button(center_text="→", width=60, height=50)
        right_button.on_clicked(self.set_direction, Direction.RIGHT)

        # Position direction buttons at right side
        button_start_x = board_width + WALL_THICKNESS + 20
        button_start_y = WALL_THICKNESS

        self.app.add(up_button, x=button_start_x + 60, y=button_start_y)
        self.app.add(
            left_button, x=button_start_x, y=button_start_y + 60
        )
        self.app.add(
            right_button, x=button_start_x + 120, y=button_start_y + 60
        )
        self.app.add(down_button, x=button_start_x + 60, y=button_start_y + 120)

    def set_direction(self, direction):
        """Set the next direction for the snake."""
        # Prevent reversing into itself
        opposite_directions = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT,
        }

        if direction != opposite_directions[self.direction]:
            self.next_direction = direction

    def _end_game(self):
        """End the game."""
        if self.score > self.high_score:
            self.high_score = self.score

        self.game_state = GameState.GAME_OVER
        if self.game_routine:
            self.game_routine.stop()
            self.game_routine = None
        self.init_ui()

    def _start_game(self):
        """Start a new game."""
        self.snake = [(10, 10), (10, 11), (10, 12)]
        self.direction = Direction.UP
        self.next_direction = Direction.UP
        self.food = self._generate_food()
        self.score = 0
        self.game_state = GameState.PLAYING

        # Start game routine
        self.game_routine = Routine(interval_ms=GAME_SPEED, invoke=self._update_game)
        self.init_ui()

    def _show_tutorial(self):
        """Show the tutorial screen."""
        self.game_state = GameState.TUTORIAL
        self.init_ui()

    def init_ui(self):
        """Initialize the UI based on game state."""
        self.app.clear()

        if self.game_state == GameState.MENU:
            # Main menu
            card = TextCardWithTwoButtons(
                text="Snake Attack\n\nEat food and grow!",
                button_text_1="Play",
                button_text_2="Tutorial",
                on_button_1_click=self._start_game,
                on_button_2_click=self._show_tutorial,
                container_width=CONTAINER_WIDTH,
            )
            self.app.add(
                card, x=self.app.width() - card.width(), y=50
            )

        elif self.game_state == GameState.TUTORIAL:
            # Tutorial screen
            tutorial_text = """How to Play:

↑ ↓ ← → Controls

Eat yellow food
to grow!

Avoid red walls
and yourself!"""
            card = TextCardWithButton(
                text=tutorial_text,
                button_text="Got it!",
                on_button_click=self._return_to_menu,
                container_width=CONTAINER_WIDTH,
            )
            self.app.add(
                card, x=self.app.width() - card.width(), y=20
            )

        elif self.game_state == GameState.PLAYING:
            self._draw_game()

        elif self.game_state == GameState.GAME_OVER:
            # Game over screen
            card = TextCardWithTwoButtons(
                text=f"Game Over!\n\nScore: {self.score}\nHigh Score: {self.high_score}",
                button_text_1="Play Again",
                button_text_2="Menu",
                on_button_1_click=self._start_game,
                on_button_2_click=self._return_to_menu,
                container_width=CONTAINER_WIDTH,
            )
            self.app.add(
                card, x=self.app.width() - card.width(), y=50
            )

    def _return_to_menu(self):
        """Return to main menu."""
        self.game_state = GameState.MENU
        if self.game_routine:
            self.game_routine.stop()
            self.game_routine = None
        self.init_ui()


if __name__ == "__main__":
    RunApp.run(
        lambda: SnakeGame(),
        app_id="",
        app_key="",
    )
