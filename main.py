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
RIGHT_FACING = 0
LEFT_FACING = 1

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
        super().__init__(walk_textures[0][0], scale=ENEMY_SCALING)
        self.center_x = x
        self.center_y = y

        self.game_view = game_view

        self.max_health = max_health
        self.current_health = max_health
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary

        self.walk_textures = walk_textures
        self.attack_textures = attack_textures
        self.takedamage_textures = takedamage_textures
        self.death_textures = death_textures

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
        if self.is_dead:
            return

        bottom = self.center_y + HEALTH_BAR_Y_OFFSET
        top = bottom + HEALTH_BAR_HEIGHT
        left = self.center_x - HEALTH_BAR_WIDTH / 2
        right = left + HEALTH_BAR_WIDTH

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

    def update(self):
        if self.is_dead:
            return

        self.center_x += self.change_x
        if self.center_x < self.left_boundary:
            self.change_x = 1
            self.direction = RIGHT_FACING
        elif self.center_x > self.right_boundary:
            self.change_x = -1
            self.direction = LEFT_FACING

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def update_animation(self, delta_time: float = 1 / 60):
        if self.is_dead:
            frame = min(
                self.cur_texture // UPDATES_PER_FRAME,
                len(self.death_textures) - 1,
            )
            self.texture = self.death_textures[frame][self.direction]
            self.cur_texture += 1
            return

        if self.is_taking_damage:
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
        if self.is_dead:
            return

        raw_x = player_sprite.center_x - self.center_x
        distance_x = abs(raw_x)
        distance_y = abs(player_sprite.center_y - self.center_y)

        player_in_boundaries = (
            self.left_boundary
            <= player_sprite.center_x
            <= self.right_boundary
        )
        current_frame = self.cur_texture // UPDATES_PER_FRAME

        if self.is_attacking:
            self.change_x = 0

            if current_frame == 6 and not self.has_dealt_damage:
                if (
                    distance_x < ENEMY_ATTACK_RANGE_X
                    and distance_y < ENEMY_ATTACK_RANGE_Y
                ):
                    if player_sprite.invulnerable_timer <= 0:
                        player_sprite.take_damage(MUSHROOM_ENEMY_DAMAGE)
                        self.has_dealt_damage = True

            if current_frame >= len(self.attack_textures) - 1:
                self.has_dealt_damage = False
            return

        if player_in_boundaries:
            self.direction = LEFT_FACING if raw_x < 0 else RIGHT_FACING

            if (
                distance_x < ENEMY_DETECTION_RANGE_X
                and distance_y < ENEMY_DETECTION_RANGE_Y
            ):
                if self.attack_cooldown <= 0:
                    self.is_attacking = True
                    self.change_x = 0
                    self.cur_texture = 0
            else:
                self.change_x = (
                    -ENEMY_CHASE_SPEED if raw_x < 0 else ENEMY_CHASE_SPEED
                )
        else:
            if self.direction == RIGHT_FACING:
                self.change_x = 1
                if self.center_x >= self.right_boundary:
                    self.direction = LEFT_FACING
            else:
                self.change_x = -1
                if self.center_x <= self.left_boundary:
                    self.direction = RIGHT_FACING

    def take_damage(self, amount):
        if self.is_dead:
            return

        self.current_health -= amount
        arcade.play_sound(self.game_view.hit_sound, volume=1.4)
        self.is_taking_damage = True
        self.takedamage_frame = 0
        self.is_attacking = False

        if self.current_health <= 0:
            self.is_dead = True
            self.cur_texture = 0


class PlayerCharacter(arcade.Sprite):
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
        super().__init__(idle_textures[0][0], scale=PLAYER_SCALING)

        self.game_view = game_view

        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0
        self.jump_frame = 0
        self.attack_frame = 0
        self.takedamage_frame = 0
        self.death_frame = 0
        self.invulnerable_timer = 0

        self.is_attacking = False
        self.is_taking_damage = False
        self.is_dead = False
        self.has_dealt_damage = False

        self.idle_textures = idle_textures
        self.run_textures = run_textures
        self.jump_textures = jump_textures
        self.fall_textures = fall_textures
        self.attack_textures = attack_textures
        self.takedamage_textures = takedamage_textures
        self.death_textures = death_textures

        self.enemy_list = enemy_list
        self.attack_range = PLAYER_ATTACK_RANGE
        self.attack_height = PLAYER_ATTACK_HEIGHT
        self.attack_damage_frame = PLAYER_ATTACK_FRAME

        self.max_health = max_health
        self.current_health = max_health

    def take_damage(self, damage):
        if self.is_dead or self.invulnerable_timer > 0:
            return

        self.current_health -= damage
        arcade.play_sound(self.game_view.hit_sound, volume=1.4)
        self.invulnerable_timer = INVULNERABILITY_FRAMES
        self.is_taking_damage = True
        self.takedamage_frame = 0

        if self.current_health <= 0:
            self.current_health = 0
            self.is_dead = True
            self.death_frame = 0

    def draw_health_bar(self):
        bottom = self.center_y + HEALTH_BAR_Y_OFFSET
        top = bottom + HEALTH_BAR_HEIGHT
        left = self.center_x - HEALTH_BAR_WIDTH / 2
        right = left + HEALTH_BAR_WIDTH

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
        if not self.is_attacking and self.change_y == 0:
            self.is_attacking = True
            arcade.play_sound(self.game_view.sword_sound, volume=0.3)
            self.cur_texture = 0

    def update_animation(self, delta_time: float = 1 / 60):
        if self.change_x < 0:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0:
            self.character_face_direction = RIGHT_FACING

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        if self.is_dead:
            self.death_frame += 1
            frame = self.death_frame // UPDATES_PER_FRAME
            if frame < len(self.death_textures):
                self.texture = self.death_textures[frame][
                    self.character_face_direction
                ]
                self.change_x = 0
                self.change_y = 0
            return

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
                self.is_taking_damage = False
            return

        if self.change_y > 0:
            self.jump_frame = min(
                self.jump_frame + 1, len(self.jump_textures) - 1
            )
            self.texture = self.jump_textures[self.jump_frame][
                self.character_face_direction
            ]
            return
        elif self.change_y < 0:
            self.jump_frame = min(
                self.jump_frame + 1, len(self.fall_textures) - 1
            )
            self.texture = self.fall_textures[self.jump_frame][
                self.character_face_direction
            ]
            return
        else:
            self.jump_frame = 0

        if self.is_attacking:
            self.change_x = 0
            current_frame = self.attack_frame // UPDATES_PER_FRAME

            if (
                current_frame == self.attack_damage_frame
                and not self.has_dealt_damage
            ):
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
                        enemy.take_damage(PLAYER_ATTACK_DAMAGE)
                self.has_dealt_damage = True
            elif current_frame != self.attack_damage_frame:
                self.has_dealt_damage = False

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

        if self.change_x != 0:
            self.cur_texture += 1
            max_texture = len(self.run_textures) * UPDATES_PER_FRAME
            if self.cur_texture >= max_texture:
                self.cur_texture = 0
            frame = self.cur_texture // UPDATES_PER_FRAME
            self.texture = self.run_textures[frame][
                self.character_face_direction
            ]
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
    def __init__(self):
        super().__init__()
        self.title_y = WINDOW_HEIGHT + 100
        self.title_drop_speed = 200
        self.title_target_y = WINDOW_HEIGHT * 0.7

    def on_show(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()

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

        arcade.draw_text(
            "Press any key to start",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2,
            arcade.color.WHITE,
            SUBTITLE_FONT_SIZE,
            anchor_x="center",
        )

        arcade.draw_text(
            "Arrow Keys/WASD to Move | SPACE to Attack |",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 - 50,
            arcade.color.LIGHT_GRAY,
            INSTRUCTION_FONT_SIZE,
            anchor_x="center",
        )
        arcade.draw_text(
            "Spikes are instant death!",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 - 100,
            arcade.color.LIGHT_GRAY,
            INSTRUCTION_FONT_SIZE,
            anchor_x="center",
        )

    def on_update(self, delta_time):
        if self.title_y > self.title_target_y:
            self.title_y -= delta_time * self.title_drop_speed

    def on_key_press(self, key, _modifiers):
        self.start_game()

    def start_game(self):
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)


class DeathScreen(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        self.current_level = game_view.level

    def on_draw(self):
        self.clear()
        arcade.draw_text(
            "GAME OVER",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 + 50,
            arcade.color.RED,
            GAME_OVER_FONT_SIZE,
            anchor_x="center",
        )
        arcade.draw_text(
            "Press any key to restart",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 - 50,
            arcade.color.WHITE,
            END_SCREEN_OPTION_SIZE,
            anchor_x="center",
        )

    def on_key_press(self, key, _modifiers):
        game_view = GameView()
        game_view.level = self.current_level
        game_view.setup()
        self.window.show_view(game_view)


class EndScreen(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view

    def on_draw(self):
        self.clear()
        arcade.set_background_color(arcade.color.BLACK)

        arcade.draw_text(
            "THANKS FOR PLAYING!",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 + 100,
            arcade.color.GOLD,
            END_SCREEN_TITLE_SIZE,
            anchor_x="center",
            font_name="Kenney Future",
        )

        arcade.draw_text(
            "R - Restart Game",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2,
            arcade.color.WHITE,
            END_SCREEN_OPTION_SIZE,
            anchor_x="center",
        )

        arcade.draw_text(
            "Q - Quit Game",
            WINDOW_WIDTH // 2,
            WINDOW_HEIGHT // 2 - 50,
            arcade.color.WHITE,
            END_SCREEN_OPTION_SIZE,
            anchor_x="center",
        )

    def on_key_press(self, key, _modifiers):
        if key == arcade.key.R:
            game_view = GameView()
            game_view.setup()
            self.window.show_view(game_view)
        elif key == arcade.key.Q:
            arcade.close_window()


class GameView(arcade.View):
    def __init__(self):
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

        self.setup()

    def setup(self):
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

        def _load_texture_pair(path):
            tex = arcade.load_texture(path)
            return (tex, tex.flip_left_right())

        # Player textures
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

        # Create player
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
        self.player_sprite.center_x = 196
        self.player_sprite.center_y = 4800
        self.player_list.append(self.player_sprite)

        # Load map
        file_path = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(
            file_path, f"resources/maps/level{self.level}.tmx"
        )

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

        self.tile_map = arcade.load_tilemap(
            map_path, TILE_SCALING, layer_options
        )
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.load_enemies_from_map()

        self.boundaries_list = self.tile_map.sprite_lists["Boundaries"]
        self.wall_list = self.tile_map.sprite_lists["Ground"]
        self.finish_list = self.tile_map.sprite_lists["Finish"]
        self.spikes_list = self.tile_map.sprite_lists["Spikes"]
        self.decorations = self.scene["Decorations"]
        self.background_filler = self.scene["Background_Filler"]
        self.background = self.scene["Background"]
        self.midground = self.scene["Midground"]
        self.foreground = self.scene["Foreground"]

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

        if self.tile_map.background_color:
            self.window.background_color = self.tile_map.background_color

        platforms = [self.wall_list]
        if self.moving_platforms:
            platforms.append(self.moving_platforms)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, platforms, gravity_constant=GRAVITY
        )

        # Camera
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
        if "Mushroom_Enemies" not in self.tile_map.object_lists:
            return

        for enemy_obj in self.tile_map.object_lists["Mushroom_Enemies"]:
            x = enemy_obj.shape[0]
            y = enemy_obj.shape[1]
            left = enemy_obj.properties.get(
                "left_boundary", x - ENEMY_PATROL_DISTANCE
            )
            right = enemy_obj.properties.get(
                "right_boundary", x + ENEMY_PATROL_DISTANCE
            )

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
            self.enemy_list.append(enemy)

    def on_draw(self):
        self.camera.use()
        self.clear()

        self.scene["Background"].draw()
        self.scene["Midground"].draw()
        self.scene["Foreground"].draw()
        self.scene["Background_Filler"].draw()
        self.scene["Decorations"].draw()

        self.frame_count += 1

        self.wall_list.draw()
        self.moving_platforms.draw()
        self.finish_list.draw()
        self.spikes_list.draw()
        self.enemy_list.draw()
        self.player_list.draw()

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
        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = JUMP_SPEED
                arcade.play_sound(self.jump_sound, volume=1.5)
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.SPACE:
            self.space_pressed = True
            self.player_sprite.start_attack()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.SPACE:
            self.space_pressed = False

    def on_update(self, delta_time):
        if self.player_sprite.is_dead:
            if (
                self.player_sprite.death_frame
                > len(self.player_sprite.death_textures) * UPDATES_PER_FRAME
            ):
                death_screen = DeathScreen(self)
                self.window.show_view(death_screen)
                return


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

            # Then update physics
            self.physics_engine.update()
            self.player_sprite.update_animation(delta_time)

            if arcade.check_for_collision_with_list(
                self.player_sprite, self.finish_list
            ):
                if self.level == 3:
                    end_screen = EndScreen(self)
                    self.window.show_view(end_screen)
                else:
                    self.level += 1
                    self.setup()

            self.hazards = [self.spikes_list, self.boundaries_list]

            # Then check collisions in one loop
            for hazard in self.hazards:
                if arcade.check_for_collision_with_list(
                    self.player_sprite, hazard
                ):
                    self.player_sprite.current_health = 0
                    self.player_sprite.is_dead = True
                    break  # Exit early if any hazard hits

            for enemy in self.enemy_list:
                enemy.update()
                enemy.detect_player(self.player_sprite)
                enemy.update_animation(delta_time)

        self.pan_camera_to_user(CAMERA_PAN_SPEED)

    def pan_camera_to_user(self, panning_fraction: float = 1.0):
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
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    start_view = StartScreen()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()
