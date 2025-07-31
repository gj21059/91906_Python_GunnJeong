"""
Adventurer's Impact
 - Built with Python and Arcade

This game features:
- Player movement and combat
- Enemy AI with patrol and attack behaviors
- Multiple levels with tile-based maps
- Health systems and attack
- Animated sprites and sound effects
"""

# Importing the libraries that are used for this game.
import time
import arcade
import os

# Constants
TILE_SCALING = 2.5
PLAYER_SCALING = 2.2
ENEMY_SCALING = 2

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Adventurer's Impact"
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING
CAMERA_PAN_SPEED = 0.30

PLAYER_HEALTH = 5
PLAYER_ATTACK_DAMAGE = 1
MUSHROOM_ENEMY_HEALTH = 3
MUSHROOM_ENEMY_DAMAGE = 2
PLAYER_SPAWN_X = 196
PLAYER_SPAWN_Y = 4800
RIGHT_FACING = 0
LEFT_FACING = 1
FINAL_LEVEL = 3

PLAYER_ATTACK_RANGE = 80
PLAYER_ATTACK_HEIGHT = 40
PLAYER_ATTACK_FRAME = 4

MOVEMENT_SPEED = 5
UPDATES_PER_FRAME = 5
IDLE_UPDATES_PER_FRAME = 5
JUMP_SPEED = 20
GRAVITY = 1.1

# Constants for health bars
HEALTH_BAR_WIDTH = 50
HEALTH_BAR_HEIGHT = 5
HEALTH_BAR_Y_OFFSET = 14
HEALTH_BAR_TEXT_SIZE = 10

# Constants for enemy behavior
ENEMY_PATROL_DISTANCE = 100
ENEMY_CHASE_SPEED = 4
ENEMY_ATTACK_COOLDOWN = 60
ENEMY_ATTACK_RANGE_X = 50
ENEMY_ATTACK_RANGE_Y = 50
ENEMY_DETECTION_RANGE_X = 50
ENEMY_DETECTION_RANGE_Y = 40

# Constants for player invulnerability
INVULNERABILITY_FRAMES = 60

# Constants for animation
PLAYER_RUN_FRAMES = 8
PLAYER_JUMP_FRAMES = 8
PLAYER_FALL_FRAMES = 6
PLAYER_IDLE_FRAMES = 6
PLAYER_ATTACK_FRAMES = 6
PLAYER_TAKEDAMAGE_FRAMES = 4
PLAYER_DEATH_FRAMES = 12
ENEMY_WALK_FRAMES = 4
ENEMY_ATTACK_FRAMES = 8
ENEMY_DEATH_FRAMES = 4
ENEMY_TAKEDAMAGE_FRAMES = 4
ENEMY_ATTACKING_FRAME = 6

# Constants for UI
TITLE_FONT_SIZE = 80
SUBTITLE_FONT_SIZE = 24
INSTRUCTION_FONT_SIZE = 18
GAME_OVER_FONT_SIZE = 72
END_SCREEN_TITLE_SIZE = 54
END_SCREEN_OPTION_SIZE = 36

# Constant for camera
CAMERA_BOUNDS_PADDING = 2.0


class EnemyCharacter(arcade.Sprite):
    """
    This class represents the  enemy
    character in the game. The enemy can walk back
    and forth between  boundaries, detect and chase the player,
    attack when in range, take damage with animation
    and sound feedback, and eventually die.
    """
    def __init__(
        self,
        x,
        y,
        max_health,
        left_boundary,
        right_boundary,
        walk_textures,
        attack_textures,
        takedamage_textures,
        death_textures,
        game_view,
    ):
        """
        Initializes the enemy's position, health, movement limits,
        animations, and game context. Upon creation,
        the enemy starts walking from its spawn
        point and is prepared with
        texture sets for all possible actions. It also stores a
        reference to the main game view
        to access sounds when taking damage.
        """
        super().__init__(walk_textures[0][0], scale=ENEMY_SCALING)
        self.center_x = x
        self.center_y = y

        self.game_view = game_view

        self.max_health = max_health
        self.current_health = max_health
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary

        # Textures for animations in each state
        self.walk_textures = walk_textures
        self.attack_textures = attack_textures
        self.takedamage_textures = takedamage_textures
        self.death_textures = death_textures

        # Boolean flags to track current behavior
        # used to prevent repeated damage per attack.        
        self.is_attacking = False
        self.is_taking_damage = False
        self.is_dead = False
        self.has_dealt_damage = False

        self.cur_texture = 0
        self.direction = RIGHT_FACING
        self.takedamage_frame = 0
        self.attack_cooldown = 0
        self.attack_cooldown_max = ENEMY_ATTACK_COOLDOWN

        self.change_x = 1

    def draw_health_bar(self):
        """
        Draws a visual health bar above the enemy's
        head if they are alive. The bar includes a red background
        showing maximum health and a green
        foreground indicating current health.
        A health value is also drawn above it.
        """
        if self.is_dead:
            return

        bottom = self.center_y + HEALTH_BAR_Y_OFFSET
        top = bottom + HEALTH_BAR_HEIGHT
        left = self.center_x - HEALTH_BAR_WIDTH / 2
        right = left + HEALTH_BAR_WIDTH

        # Draw the health bar background and current health
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top, arcade.color.RED
        )

        # Calculate the width of the current health
        current_health_width = (
            self.current_health / self.max_health
        ) * HEALTH_BAR_WIDTH
        arcade.draw_lrbt_rectangle_filled(
            left,
            left + current_health_width,
            bottom,
            top,
            arcade.color.GREEN,
        )
        # Draw the health value as text
        health_string = f"{self.current_health}/{self.max_health}"
        arcade.draw_text(
            health_string,
            self.center_x,
            top + 2,
            arcade.color.WHITE,
            HEALTH_BAR_TEXT_SIZE,
            anchor_x="center",
        )

    def update(self):
        """
        Handles enemy patrol logic and cooldown updates.
        The enemy moves horizontally between left and right
        boundaries and reverses direction upon reaching them.
        It also gradually reduces its attack cooldown over time.
        """
        # If the enemy is dead, skip updates
        if self.is_dead:
            return
        # Update position based on current change_x
        self.center_x += self.change_x
        if self.center_x < self.left_boundary:
            self.change_x = 1
            self.direction = RIGHT_FACING
        elif self.center_x > self.right_boundary:
            self.change_x = -1
            self.direction = LEFT_FACING

        # Reduce attack cooldown if it's greater than zero
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def update_animation(self, delta_time: float = 1 / 60):
        """
        Switches animation frames based on the current
        state of the enemy. This method plays different animation
        sequences depending on whether the enemy is walking,
        attacking, taking damage, or dying.
        It ensures the correct texture is
        shown each frame, timed by frame rate constants.
        """
        if self.is_dead:
            # If the enemy is dead, play death animation
            # it works by cycling through the death textures
            # and stops when the animation is complete.
            frame = min(
                self.cur_texture // UPDATES_PER_FRAME,
                len(self.death_textures) - 1,
            )
            self.texture = self.death_textures[frame][self.direction]
            self.cur_texture += 1
            return

        if self.is_taking_damage:
            # If the enemy is taking damage,
            # play takedamage animation
            # works by the same logic as the death animation.
            if (
                self.takedamage_frame
                < len(self.takedamage_textures) * UPDATES_PER_FRAME
            ):
                frame = self.takedamage_frame // UPDATES_PER_FRAME
                self.texture = self.takedamage_textures[frame][
                    self.direction
                ]
                self.takedamage_frame += 1
            else:
                self.is_taking_damage = False
            return

        if self.is_attacking:
            # If the enemy is attacking, play attack animation
            # works by the same logic as the death animation.
            frame = self.cur_texture // UPDATES_PER_FRAME

            if frame >= len(self.attack_textures):
                self.cur_texture = 0
                self.is_attacking = False
                self.attack_cooldown = self.attack_cooldown_max
            else:
                self.texture = self.attack_textures[frame][self.direction]
                self.cur_texture += 1
            return

        self.cur_texture += 1
        if self.cur_texture >= len(self.walk_textures) * UPDATES_PER_FRAME:
            self.cur_texture = 0
        frame = self.cur_texture // UPDATES_PER_FRAME
        self.texture = self.walk_textures[frame][self.direction]

    def detect_player(self, player_sprite):
        """
        Detects the player's location and changes the enemy's
        behavior accordingly. If the player is within
        the patrol area, the enemy may begin chasing
        or attacking them depending on distance and cooldown.
        Attack triggers only when the player is in range
        and the correct animation frame is reached.
        Outside the detection range, the enemy
        does normal patrolling behavior.
        """
        if self.is_dead:
            return

        # Calculate the distance to the player
        raw_x = player_sprite.center_x - self.center_x
        distance_x = abs(raw_x)
        distance_y = abs(player_sprite.center_y - self.center_y)

        # Check if the player is within the enemy's 
        # patrol boundaries.
        player_in_boundaries = (
            self.left_boundary
            <= player_sprite.center_x
            <= self.right_boundary
        )
        current_frame = self.cur_texture // UPDATES_PER_FRAME

        if self.is_attacking:
            # If the enemy is attacking, it stops moving.
            self.change_x = 0

            # Check if the attack animation frame is 
            # the one that deals damage.
            if current_frame == ENEMY_ATTACKING_FRAME and \
                not self.has_dealt_damage:
                # If the player is within attack range 
                # and not invulnerable,
                # deal damage to the player.
                if (
                    distance_x < ENEMY_ATTACK_RANGE_X
                    and distance_y < ENEMY_ATTACK_RANGE_Y
                ):
                    if player_sprite.invulnerable_timer <= 0:
                        player_sprite.take_damage(MUSHROOM_ENEMY_DAMAGE)
                        self.has_dealt_damage = True
            # Reset the attack state after the animation to 
            # allow for future attacks.
            if current_frame >= len(self.attack_textures) - 1:
                self.has_dealt_damage = False
            return

        if player_in_boundaries:
            # Faces the player and either chases or attacks
            # based on the distance.
            self.direction = LEFT_FACING if raw_x < 0 else RIGHT_FACING

            # Detects if the player is within attack range.
            if (
                distance_x < ENEMY_DETECTION_RANGE_X
                and distance_y < ENEMY_DETECTION_RANGE_Y
            ):
                if self.attack_cooldown <= 0:
                    self.is_attacking = True
                    self.change_x = 0
                    self.cur_texture = 0
            else:
                # Chases the player.
                self.change_x = (
                    -ENEMY_CHASE_SPEED if raw_x < 0 else ENEMY_CHASE_SPEED
                )
        else:
            # Resumes patrol if player is out of bounds.
            if self.direction == RIGHT_FACING:
                self.change_x = 1
                if self.center_x >= self.right_boundary:
                    self.direction = LEFT_FACING
            else:
                self.change_x = -1
                if self.center_x <= self.left_boundary:
                    self.direction = RIGHT_FACING

    def take_damage(self, amount):
        """
        Reduces the enemy's health and handles transitions
        to damaged or dead states. This method plays a hit sound,
        triggers a brief damage animation, and interrupts
        any attack in progress.
        If health drops to zero, the enemy becomes permanently dead.
        """
        if self.is_dead:
            return

        self.current_health -= amount
        arcade.play_sound(self.game_view.hit_sound, volume=2.6)

        # Triggers hurt animation and canecels any attack.
        self.is_taking_damage = True
        self.takedamage_frame = 0
        self.is_attacking = False
        
        # Checks if the enemy's health has dropped to zero.
        # If so, it sets the enemy to dead state.
        if self.current_health <= 0:
            self.is_dead = True
            self.cur_texture = 0


class PlayerCharacter(arcade.Sprite):
    """
    This class defines the player character in the game.
    It manages the character's animation states
    (idle, running, jumping, attacking, etc.),
    health, and interactions with enemies. 
    It inherits from the arcade.Sprite class.
    """

    def __init__(
        self,
        max_health,
        idle_textures,
        run_textures,
        jump_textures,
        fall_textures,
        attack_textures,
        takedamage_textures,
        death_textures,
        enemy_list,
        game_view,
    ):
        """
        Sets up the player character's initial state,
        including health, animation textures,
        and default values for control and animation logic.
        """

        # Call the parent class constructor to initialize 
        # the sprite with the idle texture and scaling.       
        super().__init__(idle_textures[0][0], scale=PLAYER_SCALING)

        # Store a reference to the current game
        # view to access sounds and other resources.
        self.game_view = game_view

        # Initialize variables to track the
        # current direction and animation frames.
        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0
        self.jump_frame = 0
        self.attack_frame = 0
        self.takedamage_frame = 0
        self.death_frame = 0
        self.invulnerable_timer = 0

        # Flags representing the player's state.
        # These flags are used to control the player's behaviour.
        self.is_attacking = False
        self.is_taking_damage = False
        self.is_dead = False
        self.has_dealt_damage = False

        # Assign animation textures for different states.
        self.idle_textures = idle_textures
        self.run_textures = run_textures
        self.jump_textures = jump_textures
        self.fall_textures = fall_textures
        self.attack_textures = attack_textures
        self.takedamage_textures = takedamage_textures
        self.death_textures = death_textures

        # Stores a list of enemies to check for attacks.
        # This allows the player to interact with enemies.
        self.enemy_list = enemy_list

        # Defines the attack hitbox sizes and 
        # the specific frames where the damage occurs.
        self.attack_range = PLAYER_ATTACK_RANGE
        self.attack_height = PLAYER_ATTACK_HEIGHT
        self.attack_damage_frame = PLAYER_ATTACK_FRAME

        # Max and current health of the player.
        self.max_health = max_health
        self.current_health = max_health

    def take_damage(self, damage):
        """
        Processes damage to the player, handling health reduction,
        invulnerability frames, and
        triggering damage or death animations.
        """
        # Ignores damage if the player is already dead
        # or invulnerable.
        if self.is_dead or self.invulnerable_timer > 0:
            return

        # Reduces the player's health by the damage amount,
        # and plays a hit sound.
        self.current_health -= damage
        arcade.play_sound(self.game_view.hit_sound, volume=2.6)
        self.invulnerable_timer = INVULNERABILITY_FRAMES
        self.is_taking_damage = True
        self.takedamage_frame = 0

        # If the player's health drops to zero, this triggers death.
        if self.current_health <= 0:
            self.current_health = 0
            self.is_dead = True
            self.death_frame = 0
            

    def draw_health_bar(self):
        """
        Draws the health bar above the player,
        showing remaining health with a red background
        and a green foreground bar.
        """
        # Calculates the vertical and horizontal positions of 
        # the health bar based on the player's position.
        bottom = self.center_y + HEALTH_BAR_Y_OFFSET
        top = bottom + HEALTH_BAR_HEIGHT
        left = self.center_x - HEALTH_BAR_WIDTH / 2
        right = left + HEALTH_BAR_WIDTH

        # Draws the health bar background and current health
        # a full red rectangle is drawn first,
        # then a green rectangle representing current health.
        arcade.draw_lrbt_rectangle_filled(
            left, right, bottom, top, arcade.color.RED
        )
        current_health_width = (
            self.current_health / self.max_health
        ) * HEALTH_BAR_WIDTH
        arcade.draw_lrbt_rectangle_filled(
            left,
            left + current_health_width,
            bottom,
            top,
            arcade.color.GREEN,
        )

        health_string = f"{self.current_health}/{self.max_health}"
        arcade.draw_text(
            health_string,
            self.center_x,
            top + 2,
            arcade.color.WHITE,
            HEALTH_BAR_TEXT_SIZE,
            anchor_x="center",
        )

    def start_attack(self):
        """
        Begins the attack animation  if the player 
        is not already attacking and is standing on 
        solid ground (not jumping or falling).
        """
        # Only initiates attack if the player is not
        # attacking nor in the air.
        if not self.is_attacking and self.change_y == 0:
            self.is_attacking = True
            # Plays the attack sound effect and resets the texture
            # to the first frame of the attack animation.
            arcade.play_sound(self.game_view.sword_sound, volume=0.5)
            self.cur_texture = 0

    def update_animation(self, delta_time: float = 1 / 60):
        """
        Updates the player’s sprite texture based on current 
        movement, actions, and animation frames. 
        This controls  idle, running, jumping, attacking, 
        taking damage, and death states.
        """
        # Updates the direction the character is facing 
        # based on horizontal movement  
        if self.change_x < 0:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0:
            self.character_face_direction = RIGHT_FACING

        # Reduce invulnerability timer by one frame if active
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        # If the player is dead, play death
        # animation frames and stop movement
        if self.is_dead:
            self.death_frame += 1
            frame = self.death_frame // UPDATES_PER_FRAME
            if frame < len(self.death_textures):
                self.texture = self.death_textures[frame][
                    self.character_face_direction
                ]
                # Stops all movement when dead so 
                # that the player cannot move or jump.
                self.change_x = 0
                self.change_y = 0
            return

        # While taking damage, play damage animation
        # and prevent movement
        if self.is_taking_damage:
            max_frame = len(self.takedamage_textures) * UPDATES_PER_FRAME
            if self.takedamage_frame < max_frame:
                frame = self.takedamage_frame // UPDATES_PER_FRAME
                self.texture = self.takedamage_textures[frame][
                    self.character_face_direction
                ]
                self.takedamage_frame += 1
                self.change_x = 0
            else:
                # End damage animation once complete.
                self.is_taking_damage = False
            return
        # If the player is jumping or falling, updates the jump frame
        # and set the textures accordingly.
        if self.change_y > 0:
            self.jump_frame = min(
                self.jump_frame + 1, len(self.jump_textures) - 1
            )
            self.texture = self.jump_textures[self.jump_frame][
                self.character_face_direction
            ]
            return
        # If the player is falling, updates the fall frame.
        elif self.change_y < 0:
            self.jump_frame = min(
                self.jump_frame + 1, len(self.fall_textures) - 1
            )
            self.texture = self.fall_textures[self.jump_frame][
                self.character_face_direction
            ]
            return
        else:
            # If the player is on the ground, resets the jump frame.
            self.jump_frame = 0

        # This block handles the player's attack state it calculates
        # the current frame of the attack animation and checks if
        # the player is currently attacking.
        if self.is_attacking:
            self.change_x = 0
            current_frame = self.attack_frame // UPDATES_PER_FRAME

            # If the current frame is the one that deals damage,
            # it will check for collisions with enemies.
            if (
                current_frame == self.attack_damage_frame
                and not self.has_dealt_damage
            ):
                # Loops through all enemies and checks if they
                # are within attack range and height
                for enemy in self.enemy_list:
                    dx = abs(enemy.center_x - self.center_x)
                    dy = abs(enemy.center_y - self.center_y)
                    right = (
                        self.character_face_direction == RIGHT_FACING
                        and enemy.center_x > self.center_x
                    )
                    left = (
                        self.character_face_direction == LEFT_FACING
                        and enemy.center_x < self.center_x
                    )

                    if (
                        dx < self.attack_range
                        and dy < self.attack_height
                        and (right or left)
                    ):
                        # If the enemy is within range
                        # it takes damage.
                        enemy.take_damage(PLAYER_ATTACK_DAMAGE)
                self.has_dealt_damage = True
            elif current_frame != self.attack_damage_frame:
                self.has_dealt_damage = False

            # Updates the attack frame and texture
            # based on the current frame.
            self.attack_frame += 1
            max_frame = len(self.attack_textures) * UPDATES_PER_FRAME
            if self.attack_frame >= max_frame:
                self.attack_frame = 0
                self.is_attacking = False
            else:
                self.texture = self.attack_textures[current_frame][
                    self.character_face_direction
                ]
            return

        # If the player is not attacking, then the movement
        # animations should play.
        if self.change_x != 0:
            self.cur_texture += 1
            max_texture = len(self.run_textures) * UPDATES_PER_FRAME
            if self.cur_texture >= max_texture:
                self.cur_texture = 0
            frame = self.cur_texture // UPDATES_PER_FRAME
            self.texture = self.run_textures[frame][
                self.character_face_direction
            ]
        # If the player is not moving then
        # the idle animation should play.
        else:
            self.cur_texture += 1
            max_texture = len(self.idle_textures) * IDLE_UPDATES_PER_FRAME
            if self.cur_texture >= max_texture:
                self.cur_texture = 0
            frame = self.cur_texture // IDLE_UPDATES_PER_FRAME
            self.texture = self.idle_textures[frame][
                self.character_face_direction
            ]


class StartScreen(arcade.View):
    """
    This class represents the start screen of the game.
    It displays the game title and shows gameplay instructions. 
    It transitions to the main game view when the player 
    presses any key.
    """
    def __init__(self):
        """
        Initialize the start screen view by setting 
        the drop speed for the animation, and the
        position where the title should stop.
        """

        # Starts the title off-screen above the window sets the
        # speed at which the title falls then reaches the
        # final y position of the title
        super().__init__()
        self.title_y = WINDOW_HEIGHT + 100
        self.title_drop_speed = 200
        self.title_target_y = WINDOW_HEIGHT * 0.7

    def on_show(self):
        """
        Called when this view is shown.
        Sets the background color of the window.
        """        
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):

        self.clear()
        """
        Draws the contents of the start screen,
        including the game title, subtitle, and instructions.
        """
        # Draws the title at the center of the screen
        title = "Adventurer's Impact"
        arcade.draw_text(
            title,
            WINDOW_WIDTH // 2,
            self.title_y,
            arcade.color.WHITE,
            TITLE_FONT_SIZE,
            anchor_x="center",
            font_name="Press Start 2P",
        )

        # Draws the subtitle below the title 
        arcade.draw_text(
            "Press any key to start",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2,
            arcade.color.WHITE,
            SUBTITLE_FONT_SIZE,
            anchor_x="center",
        )

        # Draws the gameplay instructions for jumping, moving
        # and attacking.
        arcade.draw_text(
            "Arrow Keys/WASD to Move | SPACE to Attack |",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 - 50,
            arcade.color.LIGHT_GRAY,
            INSTRUCTION_FONT_SIZE,
            anchor_x="center",
        )

        # Draws the instructions for spikes.
        arcade.draw_text(
            "Spikes are instant death!",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 - 100,
            arcade.color.LIGHT_GRAY,
            INSTRUCTION_FONT_SIZE,
            anchor_x="center",
        )

    def on_update(self, delta_time):
        """
        Updates the position of the title to create a
        falling effect."""
        if self.title_y > self.title_target_y:
            self.title_y -= delta_time * self.title_drop_speed

    def on_key_press(self, key, _modifiers):
        """
        Called when any key is pressed.
        """
        self.start_game()

    def start_game(self):
        """
        Initializes the main game view and switches
        the current view to it.
        """
        # Initializes the main game view
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)


class DeathScreen(arcade.View):
    """
    This class represents the screen shown 
    when the player dies in the game.
    It displays a Game Over message and 
    waits for the player to press any key
    to restart the level they died on.
    """
    def __init__(self, game_view):
        """
        Initialize the death screen with a
        reference to the previous game view
        so the current level can be the same.
        Also plays a game over sound effect.
        """
        # Store reference to the game view that 
        # was active before death
        # then keeps track of the leve the player was on
        # finally plays the game over sound effect.
        super().__init__()
        self.game_view = game_view
        self.current_level = game_view.level
        arcade.play_sound(self.game_view.game_over_sound)
        
        
    def on_draw(self):
        """
        Render the "Game Over" message and 
        instructions to restart the game.
        """
        self.clear()

        # Draws the main game over text. 
        arcade.draw_text(
            "GAME OVER",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 + 50,
            arcade.color.RED,
            GAME_OVER_FONT_SIZE,
            anchor_x="center",
        )
        # Draws the instructions to restart the game.
        arcade.draw_text(
            "Press any key to restart",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 - 50,
            arcade.color.WHITE,
            END_SCREEN_OPTION_SIZE,
            anchor_x="center",
        )

    def on_key_press(self, key, _modifiers):
        """
        Handles the restart logic. When any key is pressed, 
        a new GameView is created,
        the previous level is reloaded, 
        and the game starts again.
        """
        # Set the level to the one where the player died.
        game_view = GameView()
        game_view.level = self.current_level
        game_view.setup()
        self.window.show_view(game_view)


class EndScreen(arcade.View):
    """
    This class represents the end screen 
    shown when the player completes the game.
    It thanks the player and provides options 
    to restart the game or quit.
    """
    def __init__(self, game_view):
        """
        Initialize the end screen with a reference
        to the previous game view
        """
        super().__init__()
        self.game_view = game_view

    def on_draw(self):
        """
        Render the end screen with a thank you
        message and restart/quit options.
        """
        self.clear()
        arcade.set_background_color(arcade.color.BLACK)

        # Draws the "Thanks for playing!" text.
        arcade.draw_text(
            "THANKS FOR PLAYING!",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 + 100,
            arcade.color.GOLD,
            END_SCREEN_TITLE_SIZE,
            anchor_x="center",
            font_name="Kenney Future",
        )
        # Draws the restart option.
        arcade.draw_text(
            "R - Restart Game",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2,
            arcade.color.WHITE,
            END_SCREEN_OPTION_SIZE,
            anchor_x="center",
        )
        # Draws the quit option.
        arcade.draw_text(
            "Q - Quit Game",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 - 50,
            arcade.color.WHITE,
            END_SCREEN_OPTION_SIZE,
            anchor_x="center",
        )

    def on_key_press(self, key, _modifiers):
        """
        Handles input from the user. Pressing 'R' restarts the game,
        while pressing 'Q' exits the game window.
        """
        # If either 'R' or 'Q' is pressed,
        # it will either restart the game or quit.
        if key == arcade.key.R:
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)
        elif key == arcade.key.Q:
            arcade.close_window()


class GameView(arcade.View):
    """
    The main game view class responsible for setting up and managing
    the game state, including sprites, tile maps, textures, physics,
    cameras, and sound effects.
    """
    def __init__(self):
        """
        Initialize the game view. 
        Sets up core components like sound effects,
        state variables, camera systems, and the setup method to 
        prepare the game environment.
        """
        super().__init__()

        # Game objects
        self.tile_map = None
        self.scene = None
        self.player_list = None
        self.enemy_list = None
        self.wall_list = None
        self.player_sprite = None
        self.physics_engine = None

        # Game state
        self.level = 1
        self.game_over = False

        # Camera
        self.camera = None
        self.gui_camera = None
        self.camera_bounds = None

        # Debug
        self.frame_count = 0
        self.last_time = None
        self.fps_text = None
        self.distance_text = None

        # Sound Effects
        self.jump_sound = arcade.load_sound("resources/sounds/jump.wav")
        self.sword_sound = arcade.load_sound("resources/sounds/sword.mp3")
        self.hit_sound = arcade.load_sound("resources/sounds/hit.wav")
        self.game_over_sound = arcade.load_sound("" \
        "resources/sounds/game_over.mp3")

        self.setup()

    def setup(self):
        """
        Initialises sprite lists, load textures, 
        create player and enemy objects, load tile map layers, 
        configure physics and camera systems.
        """
        # Player and enemy sprite lists
        # These lists will hold all player and enemy sprites.
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

        # Reset key states
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.space_pressed = False

        # Load textures
        character_path = "resources/sprites/blue_player"
        enemy_path = "resources/sprites/mushroom_enemy"

        # This is a helper function to load textures
        # for the player and enemy sprites. This is used as
        # a convenience to avoid repeating the same code
        # for loading textures for each animation state.
        def _load_texture_pair(path):
            tex = arcade.load_texture(path)
            return (tex, tex.flip_left_right())

        # This works by loading all the textures for the player
        # and enemy sprites from their respective directories.
        # the for loop iterates through the frames
        # and loads each texture pair for the animations.
        self.run_textures = [
            _load_texture_pair(
                f"{character_path}/player_run/player_run{i}.png"
            )
            for i in range(PLAYER_RUN_FRAMES)
        ]

        self.jump_textures = [
            _load_texture_pair(
                f"{character_path}/player_jump/player_jump{i}.png"
            )
            for i in range(PLAYER_JUMP_FRAMES)
        ]

        self.fall_textures = [
            _load_texture_pair(
                f"{character_path}/player_fall/player_fall{i}.png"
            )
            for i in range(PLAYER_FALL_FRAMES)
        ]

        self.idle_textures = [
            _load_texture_pair(
                f"{character_path}/player_idle/player_idle{i}.png"
            )
            for i in range(PLAYER_IDLE_FRAMES)
        ]

        self.attack_textures = [
            _load_texture_pair(
                f"{character_path}/player_attack/player_attack{i}.png"
            )
            for i in range(PLAYER_ATTACK_FRAMES)
        ]

        self.takedamage_textures = [
            _load_texture_pair(f"{character_path}/player_takedamage/"
                            f"player_takedamage{i}.png")
            for i in range(PLAYER_TAKEDAMAGE_FRAMES)
        ]

        self.death_textures = [
            _load_texture_pair(
                f"{character_path}/player_death/player_death{i}.png"
            )
            for i in range(PLAYER_DEATH_FRAMES)
        ]

        # Enemy textures
        self.enemy_walk_textures = [
            _load_texture_pair(
                f"{enemy_path}/mushroom_idle/mushroom_idle{i}.png"
            )
            for i in range(ENEMY_WALK_FRAMES)
        ]

        self.enemy_attack_textures = [
            _load_texture_pair(
                f"{enemy_path}/mushroom_attack/mushroom_attack{i}.png"
            )
            for i in range(ENEMY_ATTACK_FRAMES)
        ]

        self.enemy_death_textures = [
            _load_texture_pair(
                f"{enemy_path}/mushroom_death/mushroom_death{i}.png"
            )
            for i in range(ENEMY_DEATH_FRAMES)
        ]

        self.enemy_takedamage_textures = [
            _load_texture_pair(
                f"{enemy_path}/mushroom_takedamage/"
                f"mushroom_takedamage{i}.png"
            )
            for i in range(ENEMY_TAKEDAMAGE_FRAMES)
        ]

        # Therefore, the player sprite is created
        # with the loaded textures and initial position.
        self.player_sprite = PlayerCharacter(
            PLAYER_HEALTH,
            self.idle_textures,
            self.run_textures,
            self.jump_textures,
            self.fall_textures,
            self.attack_textures,
            self.takedamage_textures,
            self.death_textures,
            self.enemy_list,
            self,
        )
        # Sets the initial position of the player sprite
        # to the spawn point defined by constants.
        self.player_sprite.center_x = PLAYER_SPAWN_X
        self.player_sprite.center_y = PLAYER_SPAWN_Y
        self.player_list.append(self.player_sprite)

        # Load map
        file_path = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(
            file_path, f"resources/maps/level{self.level}.tmx"
        )

        # Configures the tile map layer properties.
        # This sets whether spatial hashing
        # is used for collision detection
        layer_options = {
            "Mushroom_Enemies": {"use_spatial_hash": True},
            "Finish": {"use_spatial_hash": True},
            "Spikes": {"use_spatial_hash": True},
            "Ground": {"use_spatial_hash": True},
            "Boundaries": {"use_spatial_hash": True},
            "Decorations": {"use_spatial_hash": False},
            "Background_Filler": {"use_spatial_hash": False},
            "Background": {"use_spatial_hash": False},
            "Midground": {"use_spatial_hash": False},
            "Foreground": {"use_spatial_hash": False},
            "Moving_Platforms": {"use_spatial_hash": True},
        }
        # Loads the tile map from the specified path
        # with the defined scaling and layer options.
        self.tile_map = arcade.load_tilemap(
            map_path, TILE_SCALING, layer_options
        )

        # Create the scene from the tile map and loads the
        # enemies from the map.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.load_enemies_from_map()

        # This assigns references to the specific tile layers.
        self.boundaries_list = self.tile_map.sprite_lists["Boundaries"]
        self.wall_list = self.tile_map.sprite_lists["Ground"]
        self.finish_list = self.tile_map.sprite_lists["Finish"]
        self.spikes_list = self.tile_map.sprite_lists["Spikes"]
        self.decorations = self.scene["Decorations"]
        self.background_filler = self.scene["Background_Filler"]
        self.background = self.scene["Background"]
        self.midground = self.scene["Midground"]
        self.foreground = self.scene["Foreground"]

        # Loads and configures the moving platforms.
        # This works by checking if the "Moving_Platforms" 
        # layer exists in the tile map and then 
        # iterating through its sprites.
        # then it sets the boundaries and movement speed
        # for each platform based on its properties.
        self.moving_platforms = arcade.SpriteList()
        if "Moving_Platforms" in self.tile_map.sprite_lists:
            for platform in self.tile_map.sprite_lists["Moving_Platforms"]:
                platform.boundary_left = platform.properties.get(
                    "boundary_left",
                    platform.center_x - ENEMY_PATROL_DISTANCE,
                )
                platform.boundary_right = platform.properties.get(
                    "boundary_right",
                    platform.center_x + ENEMY_PATROL_DISTANCE,
                )
                platform.change_x = platform.properties.get("change_x", 0)
                self.moving_platforms.append(platform)

        # If the tile map has a background color, set it as it is.
        if self.tile_map.background_color:
            self.window.background_color = self.tile_map.background_color

        # For efficient collision detection,
        # it appends the moving platforms to the list.
        # This is done to ensure that the physics engine
        # can handle collisions with both static 
        # and moving platforms.
        platforms = [self.wall_list]
        if self.moving_platforms:
            platforms.append(self.moving_platforms)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, platforms, gravity_constant=GRAVITY
        )

        # Sets the camera for the game view and GUI.
        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        max_x = GRID_PIXEL_SIZE * self.tile_map.width
        max_y = GRID_PIXEL_SIZE * self.tile_map.height
        self.camera_bounds = arcade.LRBT(
            self.window.width / CAMERA_BOUNDS_PADDING,
            max_x - self.window.width / CAMERA_BOUNDS_PADDING,
            0,
            max_y,
        )

        # Debug
        self.fps_text = arcade.Text(
            "", x=10, y=40, color=arcade.color.WHITE, font_size=14
        )
        self.distance_text = arcade.Text(
            "0.0", x=10, y=20, color=arcade.color.WHITE, font_size=14
        )

        self.pan_camera_to_user()
        self.game_over = False

    def load_enemies_from_map(self):
        """Load enemies from the tilemap object layer 
        if it exists. Creates enemy instances with their positions 
        and patrol boundaries from map properties.
        """
        # Checks if the current map has any mushroom enemies defined.
        if "Mushroom_Enemies" not in self.tile_map.object_lists:
            return

        # This proccess each enemy object in the map's 
        # mushroom layer.
        for enemy_obj in self.tile_map.object_lists["Mushroom_Enemies"]:
            # Gets enemy position from map object.
            x = enemy_obj.shape[0]
            y = enemy_obj.shape[1]

            # If the enemy has a custom left and right boundary,
            # it uses those values, otherwise it uses the default.
            left = enemy_obj.properties.get(
                "left_boundary", x - ENEMY_PATROL_DISTANCE
            )
            right = enemy_obj.properties.get(
                "right_boundary", x + ENEMY_PATROL_DISTANCE
            )

            # Creates the enemy character instance.
            enemy = EnemyCharacter(
                x=x,
                y=0,
                left_boundary=left,
                right_boundary=right,
                max_health=MUSHROOM_ENEMY_HEALTH,
                walk_textures=self.enemy_walk_textures,
                attack_textures=self.enemy_attack_textures,
                takedamage_textures=self.enemy_takedamage_textures,
                death_textures=self.enemy_death_textures,
                game_view=self,
            )
            enemy.bottom = y
            # Adds the enemy to the game's enemy list.
            self.enemy_list.append(enemy)

    def on_draw(self):
        """Render all game elements including background, 
        sprites, UI elements. 
        Called every frame to update the display.
        """

        # Activate the camera.
        self.camera.use()
        self.clear()

        # Draw the background layers in the proper order.
        self.scene["Background"].draw()
        self.scene["Midground"].draw()
        self.scene["Foreground"].draw()
        self.scene["Background_Filler"].draw()
        self.scene["Decorations"].draw()


        self.frame_count += 1

        # Draw all in game objects and level elements.
        self.wall_list.draw()
        self.moving_platforms.draw()
        self.finish_list.draw()
        self.spikes_list.draw()
        self.enemy_list.draw()
        self.player_list.draw()

        # Draws the health bars for player and enemies.
        # this is done by iterating through the player and
        # enemy lists
        # and calling the draw_health_bar method for each sprite.
        for sprite in self.player_list:
            sprite.draw_health_bar()


        for enemy in self.enemy_list:
            enemy.draw_health_bar()
            arcade.draw_line(
                enemy.left_boundary,
                enemy.center_y - 50,
                enemy.left_boundary,
                enemy.center_y + 50,
                arcade.color.RED,
                2,
            )
            arcade.draw_line(
                enemy.right_boundary,
                enemy.center_y - 50,
                enemy.right_boundary,
                enemy.center_y + 50,
                arcade.color.GREEN,
                2,
            )
            arcade.draw_line(
                enemy.left_boundary,
                enemy.center_y,
                enemy.right_boundary,
                enemy.center_y,
                arcade.color.BLUE,
                1,
            )

        # Draw the GUI camera for UI elements.
        self.gui_camera.use()

        if self.last_time and self.frame_count % 60 == 0:
            fps = round(1.0 / (time.time() - self.last_time) * 60)
            self.fps_text.text = f"FPS: {fps:3d}"

        self.fps_text.draw()

        if self.frame_count % 60 == 0:
            self.last_time = time.time()

        distance = self.player_sprite.right
        self.distance_text.text = f"Distance: {distance}"
        self.distance_text.draw()

    def on_key_press(self, key, modifiers):
        """Handles key presses for player movement and actions.
        Sets the corresponding flags for movement and actions.
        """
        # Handles key presses for player movement and actions.
        # This sets the flags for movement and actions 
        # based on the key pressed. If the player presses the up
        # arrow or W key, it sets the up_pressed flag to True and
        # checks if the player can jump. If so, it sets the player's
        # vertical speed to the jump speed and plays the jump sound.
        # the rest of the keys follow the same logic.
        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = JUMP_SPEED
                arcade.play_sound(self.jump_sound, volume=4.3)
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.SPACE:
            self.space_pressed = True
            self.player_sprite.start_attack()

    def on_key_release(self, key, modifiers):
        """Handles key releases for player movement and actions.
        Resets the corresponding flags for movement and actions.
        """
        # Handles key releases for player movement and actions.
        # This resets the flags for movement and actions
        # based on the key released. If the player releases the up
        # arrow or W key, it sets the up_pressed flag to False.
        # the rest of the keys follow the same logic.
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.SPACE:
            self.space_pressed = False

    def on_update(self, delta_time):
        """Updates the game state, which handles player death and 
        screen transitions, player movement, enemy behaviour and AI,
        moving platforms, physics updates, and camera panning."""

        # Handles player death and screen transitions.
        if self.player_sprite.is_dead:
            # Wait for the death animation to finish
            # before showing the death screen.
            if (
                self.player_sprite.death_frame
                > len(self.player_sprite.death_textures) * UPDATES_PER_FRAME
            ):
                death_screen = DeathScreen(self)
                self.window.show_view(death_screen)
                return

        # Only proceed with game logic if the game is not over.
        # This prevents any updates to the game state when the 
        # player is dead or the game is over.
        if not self.game_over:
            # Only update movement if player is not attacking and not dead
            if (
                not self.player_sprite.is_attacking
                and not self.player_sprite.is_dead
            ):
                if self.left_pressed and not self.right_pressed:
                    self.player_sprite.change_x = -MOVEMENT_SPEED
                elif self.right_pressed and not self.left_pressed:
                    self.player_sprite.change_x = MOVEMENT_SPEED
                else:
                    self.player_sprite.change_x = 0
            else:
                # Stop movement if attacking or dead
                self.player_sprite.change_x = 0
                self.player_sprite.change_y = 0

            # Move platforms FIRST
            for platform in self.moving_platforms:
                platform.center_x += platform.change_x
                if (
                    platform.change_x > 0
                    and platform.center_x > platform.boundary_right
                ):
                    platform.change_x *= -1
                elif (
                    platform.change_x < 0
                    and platform.center_x < platform.boundary_left
                ):
                    platform.change_x *= -1

            # Then update physics so that the player
            # can interact with them.
            self.physics_engine.update()
            self.player_sprite.update_animation(delta_time)

            # Check for collisions with the finish line.
            # If the player collides with the finish line,
            # it checks if the level is complete.
            # If the level is complete, it either shows the end screen
            # or advances to the next level.
            # If the player is on the last level
            # it shows the end screen.
            if arcade.check_for_collision_with_list(
                self.player_sprite, self.finish_list
            ):
                if self.level == FINAL_LEVEL:
                    end_screen = EndScreen(self)
                    self.window.show_view(end_screen)
                else:
                    self.level += 1
                    self.setup()

            # This is a list of hazards that the 
            # player can collide with.
            self.hazards = [self.spikes_list, self.boundaries_list]

            # Then check collisions in one loop
            for hazard in self.hazards:
                if arcade.check_for_collision_with_list(
                    self.player_sprite, hazard
                ):
                    self.player_sprite.current_health = 0
                    self.player_sprite.is_dead = True
                    # Exit early if any hazard hits
                    break  
            
            # Updates all the enemies in the game.
            # This iterates through the enemy list and updates.
            for enemy in self.enemy_list:
                enemy.update()
                enemy.detect_player(self.player_sprite)
                enemy.update_animation(delta_time)

        # Smoothly moves the camera to follow the player.
        self.pan_camera_to_user(CAMERA_PAN_SPEED)

    def pan_camera_to_user(self, panning_fraction: float = 1.0):
        """Smoothly moves the camera to follow the player position
        using arcade.math.smerp_2d for smooth panning.
        Constrains the camera position within the defined bounds."""

        # Calculate the new camera position based on the 
        # player's position
        self.camera.position = arcade.math.smerp_2d(
            self.camera.position,
            self.player_sprite.position,
            self.window.delta_time,
            panning_fraction,
        )
        self.camera.position = arcade.camera.grips.constrain_xy(
            self.camera.view_data,
            self.camera_bounds,
        )


def main():
    """
    Main Function of the code
    """
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    start_view = StartScreen()
    window.show_view(start_view)
    arcade.run()

# Runs the code.
if __name__ == "__main__":
    main()