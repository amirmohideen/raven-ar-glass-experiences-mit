# Nokia Snake Game for Raven Glass
# A classic snake game with gaze-based controls

from enum import Enum
from random import randint

from PySide6.QtGui import QCursor
from PySide6.QtCore import QEvent

from raven_framework import RavenApp, RunApp, TextBox, Container, Button, VerticalContainer
from raven_framework.components.cards import TextCardWithButton, TextCardWithTwoButtons
from raven_framework.components.scroll_view import ScrollView
from raven_framework.helpers.routine import Routine
from raven_framework.helpers.animation_utils import fade_in


# Game constants
GRID_SIZE_HEIGHT = 20  # Grid height (rows)
GRID_SIZE_BUTTONS = 22  # Grid width for button mode
GRID_SIZE_CURSOR = 30  # Grid width for cursor mode (wider)
GRID_CELL_SIZE = 20  # Each cell is 20x20 pixels
GAME_SPEED = 300  # Milliseconds between moves
CONTAINER_WIDTH = 450
WALL_THICKNESS = 10
BUTTON_THICKNESS = 60  # Thickness of direction buttons


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
    CONTROLS = "controls"
    TUTORIAL = "tutorial"
    PLAYING = "playing"
    PAUSED = "paused"
    GAME_OVER = "game_over"


# Control mode enum
class ControlMode(Enum):
    """Control mode enumeration."""
    CURSOR = "cursor"
    BUTTONS = "buttons"


class SnakeGame(RavenApp):
    """Classic Nokia Snake game for Raven Glass."""

    def __init__(self, parent=None) -> None:
        """Initialize the Snake Game application."""
        super().__init__(parent)

        # Game state
        self.game_state = GameState.MENU
        self.score = 0
        self.high_score = 0
        self.control_mode = ControlMode.CURSOR  # Default to cursor control

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

        # Double-click detection for pause
        self.last_click_time = 0
        self.double_click_threshold = 400  # milliseconds

        # Install event filter for double-click detection
        self.installEventFilter(self)

        # Initialize UI
        self.init_ui()
        fade_in(self.app)

    def eventFilter(self, obj, event):
        """Handle double-click events to pause the game."""
        if event.type() == QEvent.Type.MouseButtonDblClick:
            if self.game_state == GameState.PLAYING:
                self._pause_game()
                return True
        return super().eventFilter(obj, event)

    def _update_cursor_position(self):
        """Update cursor position from global cursor."""
        if self.game_state != GameState.PLAYING:
            return
        
        # Only update if cursor control mode is enabled
        if self.control_mode != ControlMode.CURSOR:
            return
            
        # Get global cursor position and map to widget coordinates
        global_pos = QCursor.pos()
        local_pos = self.mapFromGlobal(global_pos)
        
        # Account for the app container offset (centered in 720x720 window)
        app_offset = 40
        self.cursor_x = local_pos.x() - app_offset
        self.cursor_y = local_pos.y() - app_offset
        
        # Update direction based on cursor position
        self._update_direction_from_cursor()

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
        grid_width = self._get_grid_width()
        while True:
            food = (randint(0, grid_width - 1), randint(0, GRID_SIZE_HEIGHT - 1))
            if food not in self.snake:
                return food

    def _update_game(self):
        """Update game state (called by routine each frame)."""
        # Update cursor position and direction before each move
        self._update_cursor_position()
        
        # Update direction if a new one is queued
        self.direction = self.next_direction

        # Calculate new head position
        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)

        # Check wall collision
        grid_width = self._get_grid_width()
        if (
            new_head[0] < 0
            or new_head[0] >= grid_width
            or new_head[1] < 0
            or new_head[1] >= GRID_SIZE_HEIGHT
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

    def _get_grid_width(self):
        """Get grid width based on control mode."""
        if self.control_mode == ControlMode.CURSOR:
            return GRID_SIZE_CURSOR
        return GRID_SIZE_BUTTONS

    def _draw_game(self):
        """Draw the game board."""
        # Clear and rebuild UI
        self.app.clear()

        # Get grid dimensions based on control mode
        grid_width = self._get_grid_width()
        grid_height = GRID_SIZE_HEIGHT

        # Create game board canvas
        board_width = grid_width * GRID_CELL_SIZE
        board_height = grid_height * GRID_CELL_SIZE

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
        # Draw food (red square)
        fx, fy = self.food
        food_widget = Container(
            width=GRID_CELL_SIZE - 2,
            height=GRID_CELL_SIZE - 2,
            background_color="#FF0000",
        )
        board.add(food_widget, x=fx * GRID_CELL_SIZE + 1, y=fy * GRID_CELL_SIZE + 1)

        # Draw snake
        for i, (sx, sy) in enumerate(self.snake):
            # Head is brighter
            if i == 0:
                color = "#00FF00"
            else:
                color = "#00DD00"

            snake_segment = Container(
                width=GRID_CELL_SIZE - 1,
                height=GRID_CELL_SIZE - 1,
                background_color=color,
            )
            board.add(snake_segment, x=sx * GRID_CELL_SIZE, y=sy * GRID_CELL_SIZE)

        # Calculate offsets based on control mode
        if self.control_mode == ControlMode.BUTTONS:
            # In button mode, offset board to make room for surrounding buttons
            board_offset_x = BUTTON_THICKNESS
            board_offset_y = BUTTON_THICKNESS
        else:
            # In cursor mode, no offset needed
            board_offset_x = 0
            board_offset_y = 0

        # Add walls and board to app
        self.app.add(top_wall, x=board_offset_x, y=board_offset_y)
        self.app.add(left_wall, x=board_offset_x, y=board_offset_y)
        self.app.add(board, x=board_offset_x + WALL_THICKNESS, y=board_offset_y + WALL_THICKNESS)
        self.app.add(bottom_wall, x=board_offset_x, y=board_offset_y + board_height + WALL_THICKNESS)
        self.app.add(right_wall, x=board_offset_x + board_width + WALL_THICKNESS, y=board_offset_y)

        # Add direction control buttons only in button mode
        if self.control_mode == ControlMode.BUTTONS:
            # Total board with walls dimensions
            total_board_width = board_width + WALL_THICKNESS * 2
            total_board_height = board_height + WALL_THICKNESS * 2

            # Up button - above top wall, spans board width
            up_button = Button(center_text="↑", width=total_board_width, height=BUTTON_THICKNESS)
            up_button.on_clicked(self.set_direction, Direction.UP)
            self.app.add(up_button, x=board_offset_x, y=0)

            # Down button - below bottom wall, spans board width
            down_button = Button(center_text="↓", width=total_board_width, height=BUTTON_THICKNESS)
            down_button.on_clicked(self.set_direction, Direction.DOWN)
            self.app.add(down_button, x=board_offset_x, y=board_offset_y + total_board_height)

            # Left button - left of left wall, spans board height
            left_button = Button(center_text="←", width=BUTTON_THICKNESS, height=total_board_height)
            left_button.on_clicked(self.set_direction, Direction.LEFT)
            self.app.add(left_button, x=0, y=board_offset_y)

            # Right button - right of right wall, spans board height
            right_button = Button(center_text="→", width=BUTTON_THICKNESS, height=total_board_height)
            right_button.on_clicked(self.set_direction, Direction.RIGHT)
            self.app.add(right_button, x=board_offset_x + total_board_width, y=board_offset_y)

            # Add score display below the down button
            score_text = TextBox(
                text=f"Score: {self.score}", text_color="#FFFFFF", font_size=24, width=total_board_width, alignment="center"
            )
            self.app.add(score_text, x=board_offset_x, y=board_offset_y + total_board_height + BUTTON_THICKNESS + 10)
        else:
            # In cursor mode, score below the board
            score_text = TextBox(
                text=f"Score: {self.score}", text_color="#FFFFFF", font_size=24, width=board_width, alignment="center"
            )
            self.app.add(score_text, x=WALL_THICKNESS, y=board_height + WALL_THICKNESS * 2 + 10)

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

    def _pause_game(self):
        """Pause the game."""
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            if self.game_routine:
                self.game_routine.stop()
                self.game_routine = None
            self.init_ui()

    def _resume_game(self):
        """Resume the game from pause."""
        self.game_state = GameState.PLAYING
        self.game_routine = Routine(interval_ms=GAME_SPEED, invoke=self._update_game)
        self.init_ui()

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

    def _show_controls(self):
        """Show the controls selection screen."""
        self.game_state = GameState.CONTROLS
        self.init_ui()

    def _set_cursor_mode(self):
        """Set control mode to cursor."""
        self.control_mode = ControlMode.CURSOR
        self._return_to_menu()

    def _set_buttons_mode(self):
        """Set control mode to buttons."""
        self.control_mode = ControlMode.BUTTONS
        self._return_to_menu()

    def init_ui(self):
        """Initialize the UI based on game state."""
        self.app.clear()

        if self.game_state == GameState.MENU:
            # Main menu with 3 buttons
            mode_text = "Cursor" if self.control_mode == ControlMode.CURSOR else "Buttons"
            
            menu_container = Container(
                width=CONTAINER_WIDTH,
                background_color="#1a1a1a",
                corner_radius=20,
                inner_margin=30,
            )
            
            vbox = VerticalContainer(width=CONTAINER_WIDTH - 60)
            
            title = TextBox(
                text="Snake Snack",
                font_type="title",
                alignment="center",
                width=CONTAINER_WIDTH - 60,
            )
            
            play_button = Button(center_text="Play", width=CONTAINER_WIDTH - 60)
            play_button.on_clicked(self._start_game)
            
            tutorial_button = Button(center_text="Tutorial", width=CONTAINER_WIDTH - 60)
            tutorial_button.on_clicked(self._show_tutorial)
            
            controls_button = Button(center_text="Controls", width=CONTAINER_WIDTH - 60)
            controls_button.on_clicked(self._show_controls)
            
            subtitle = TextBox(
                text=f"Control: {mode_text}",
                font_type="body",
                alignment="center",
                width=CONTAINER_WIDTH - 60,
            )
            
            vbox.add(title, play_button, tutorial_button, controls_button, subtitle)
            menu_container.add(vbox)
            
            self.app.add(
                menu_container, x=self.app.width() - menu_container.width(), y=30
            )

        elif self.game_state == GameState.CONTROLS:
            # Controls selection screen
            card = TextCardWithTwoButtons(
                text=f"Select Control Mode:\n\nCurrent: {'Cursor' if self.control_mode == ControlMode.CURSOR else 'Buttons'}",
                button_text_1="Cursor",
                button_text_2="Buttons",
                on_button_1_click=self._set_cursor_mode,
                on_button_2_click=self._set_buttons_mode,
                container_width=CONTAINER_WIDTH,
            )
            self.app.add(
                card, x=self.app.width() - card.width(), y=50
            )

        elif self.game_state == GameState.TUTORIAL:
            # Tutorial screen with scrollable instructions
            tutorial_width = 550  # Wider container for tutorial
            text_width = 460  # Leave room for scrollbar
            
            tutorial_container = Container(
                width=tutorial_width,
                background_color="#1a1a1a",
                corner_radius=20,
                inner_margin=20,
            )
            
            # Create content for scroll view
            content = VerticalContainer(width=text_width, inner_margin=10)
            
            # Title
            title = TextBox(
                text="How to Play",
                font_type="title",
                alignment="center",
                width=text_width,
            )
            content.add(title)
            
            # Objective section
            objective_title = TextBox(
                text="Objective",
                font_type="headline",
                width=text_width,
            )
            objective_text = TextBox(
                text="Guide the snake to eat the red food. Each food makes the snake grow longer and adds 10 points to your score.",
                font_type="body",
                width=text_width,
                wrap_words=True,
            )
            content.add(objective_title, objective_text)
            
            # Controls section
            controls_title = TextBox(
                text="Controls",
                font_type="headline",
                width=text_width,
            )
            
            cursor_text = TextBox(
                text="Cursor Mode: Move your cursor/gaze in the direction you want the snake to go. The snake follows your gaze!",
                font_type="body",
                width=text_width,
                wrap_words=True,
            )
            
            buttons_text = TextBox(
                text="Button Mode: Look at the direction buttons surrounding the play area to change direction.",
                font_type="body",
                width=text_width,
                wrap_words=True,
            )
            content.add(controls_title, cursor_text, buttons_text)
            
            # Danger section
            danger_title = TextBox(
                text="Game Over When",
                font_type="headline",
                width=text_width,
            )
            danger_text = TextBox(
                text="• Snake hits the red walls\n• Snake collides with itself",
                font_type="body",
                width=text_width,
                wrap_words=True,
            )
            content.add(danger_title, danger_text)
            
            # Tips section
            tips_title = TextBox(
                text="Tips",
                font_type="headline",
                width=text_width,
            )
            tips_text = TextBox(
                text="• Plan ahead - the snake can't reverse direction\n• Use the edges wisely\n• Watch your tail as you grow longer!",
                font_type="body",
                width=text_width,
                wrap_words=True,
            )
            content.add(tips_title, tips_text)
            
            # Create scroll view (wider to accommodate scrollbar)
            scroll_view = ScrollView(
                content_widget=content,
                width=tutorial_width - 40,
                height=450,
            )
            
            # Back button
            back_button = Button(center_text="Got it!", width=text_width)
            back_button.on_clicked(self._return_to_menu)
            
            # Add scroll view and button to container
            inner_vbox = VerticalContainer(width=tutorial_width - 40)
            inner_vbox.add(scroll_view, back_button)
            tutorial_container.add(inner_vbox)
            
            self.app.add(
                tutorial_container, x=self.app.width() - tutorial_container.width(), y=10
            )

        elif self.game_state == GameState.PLAYING:
            self._draw_game()

        elif self.game_state == GameState.PAUSED:
            # Draw the game in background (frozen)
            self._draw_game()
            
            # Pause menu overlay
            pause_container = Container(
                width=CONTAINER_WIDTH,
                background_color="#1a1a1a",
                corner_radius=20,
                inner_margin=30,
            )
            
            vbox = VerticalContainer(width=CONTAINER_WIDTH - 60)
            
            pause_title = TextBox(
                text="Paused",
                font_type="title",
                alignment="center",
                width=CONTAINER_WIDTH - 60,
            )
            
            score_text = TextBox(
                text=f"Score: {self.score}",
                font_type="headline",
                alignment="center",
                width=CONTAINER_WIDTH - 60,
            )
            
            high_score_text = TextBox(
                text=f"High Score: {self.high_score}",
                font_type="body",
                alignment="center",
                width=CONTAINER_WIDTH - 60,
            )
            
            resume_button = Button(center_text="Resume", width=CONTAINER_WIDTH - 60)
            resume_button.on_clicked(self._resume_game)
            
            exit_button = Button(center_text="Exit to Menu", width=CONTAINER_WIDTH - 60)
            exit_button.on_clicked(self._return_to_menu)
            
            vbox.add(pause_title, score_text, high_score_text, resume_button, exit_button)
            pause_container.add(vbox)
            
            # Center pause menu in the play area
            if self.control_mode == ControlMode.BUTTONS:
                board_width = GRID_SIZE_BUTTONS * GRID_CELL_SIZE
                board_height = GRID_SIZE_HEIGHT * GRID_CELL_SIZE
                board_offset_x = BUTTON_THICKNESS
                board_offset_y = BUTTON_THICKNESS
                center_x = board_offset_x + (board_width - pause_container.width()) // 2
                center_y = board_offset_y + (board_height - pause_container.height()) // 2
            else:
                board_width = GRID_SIZE_CURSOR * GRID_CELL_SIZE
                board_height = GRID_SIZE_HEIGHT * GRID_CELL_SIZE
                center_x = WALL_THICKNESS + (board_width - pause_container.width()) // 2
                center_y = WALL_THICKNESS + (board_height - pause_container.height()) // 2
            
            self.app.add(pause_container, x=center_x, y=center_y)

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
