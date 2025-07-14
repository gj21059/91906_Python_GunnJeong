import time
import arcade
import os

TILE_SCALING = 2.5
PLAYER_SCALING = 2

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Game"
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING
CAMERA_PAN_SPEED = 0.30

RIGHT_FACING = 0
LEFT_FACING = 1


# Physics
MOVEMENT_SPEED = 5
UPDATES_PER_FRAME = 5
IDLE_UPDATES_PER_FRAME = 20
JUMP_UPDATES_PER_FRAME = 20
JUMP_SPEED = 20
GRAVITY = 1.1

class PlayerCharacter(arcade.Sprite):
    def __init__(self, idle_textures, run_textures, jump_textures, fall_texture_pair):
        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0
        self.jump_frame_count = 0
        self.jump_frame = 0 

        self.idle_textures = idle_textures
        self.run_textures = run_textures
        self.jump_textures = jump_textures
        self.fall_texture_pair = fall_texture_pair

        super().__init__(self.idle_textures[0], scale=PLAYER_SCALING)

        self.jump_frame = 0  # initialize jump_frame here


    def update_animation(self, delta_time: float = 1 / 60):
        if self.change_x < 0:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0:
            self.character_face_direction = RIGHT_FACING

        if self.change_y > 0:
            self.jump_frame += 1
            if self.jump_frame_count >= 2100:
                self.jump_frame += 1
                self.jump_frame_count = 0
            if self.jump_frame >= len(self.jump_textures):
                self.jump_frame = len(self.jump_textures) - 1  
            self.texture = self.jump_textures[self.jump_frame][self.character_face_direction]
            return
        elif self.change_y < 0:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            self.jump_frame = 0
            return
        else:
            self.jump_frame = 0

        self.cur_texture += 1
        if self.cur_texture >= len(self.run_textures) * UPDATES_PER_FRAME:
            self.cur_texture = 0
        frame = self.cur_texture // UPDATES_PER_FRAME
        direction = self.character_face_direction
        self.texture = self.run_textures[frame][direction]

        if self.change_x == 0 and self.change_y == 0:
            self.cur_texture += 1
            if self.cur_texture >= len(self.idle_textures) * IDLE_UPDATES_PER_FRAME:
                self.cur_texture = 0
            frame = self.cur_texture // IDLE_UPDATES_PER_FRAME
            direction = self.character_face_direction
            self.texture = self.idle_textures[frame][direction]
            return




class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        self.tile_map = None
        self.player_list = None
        self.player = None
        self.wall_list = None
        self.score = 0
        self.player_sprite = None
        self.physics_engine = None
        self.end_of_map = 0
        self.game_over = False
        self.last_time = None
        self.frame_count = 0
        self.camera = None
        self.camera_bounds = None
        self.gui_camera = None

        self.fps_text = arcade.Text("", x=10, y=40, color=arcade.color.WHITE, font_size=14)
        self.distance_text = arcade.Text("0.0", x=10, y=20, color=arcade.color.WHITE, font_size=14)

      
        character_path = "resources/sprites"

        
        self.run_textures = []
        for i in range(8):  # Adjust range based on your walk sprites
            run_texture = arcade.load_texture(f"{character_path}/player_run/player_run{i}.png")
            self.run_textures.append((run_texture, run_texture.flip_left_right()))

        self.jump_textures = []
        for i in range(16):
            jump_textures = arcade.load_texture(f"{character_path}/player_jump/player_jump{i}.png")
            self.jump_textures.append((jump_textures, jump_textures.flip_left_right()))

        self.idle_textures = []
        for i in range(6):
            idle_textures = arcade.load_texture(f"{character_path}/player_idle/player_idle{i}.png")
            self.idle_textures.append((idle_textures, idle_textures.flip_left_right()))

        
        fall = arcade.load_texture(f"{character_path}/player_idle/player_idle1.png")

        self.fall_texture_pair = fall, fall.flip_left_right()




    def setup(self):
        self.player_list = arcade.SpriteList()

        self.player_sprite = PlayerCharacter(
            self.idle_textures,
            self.run_textures,
            self.jump_textures,
            self.fall_texture_pair,
            )
        self.player_sprite.center_x = 196
        self.player_sprite.center_y = 270
        self.player_list.append(self.player_sprite)

        
        file_path = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(file_path, "resources/maps/testmap.tmx")   

        layer_options = {
            "floor": {"use_spatial_hash": True},
        }

        self.tile_map = arcade.load_tilemap(
        map_path,
        scaling=TILE_SCALING,
        layer_options=layer_options,
        )
        
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        self.wall_list = self.tile_map.sprite_lists["floor"]

        # No coins layer, so create empty coin_list
        self.coin_list = arcade.SpriteList()

        if self.tile_map.background_color:
            self.window.background_color = self.tile_map.background_color

        walls = [self.wall_list]
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, walls, gravity_constant=GRAVITY
        )

        self.camera = arcade.Camera2D()
        self.gui_camera = arcade.Camera2D()

        max_x = GRID_PIXEL_SIZE * self.tile_map.width
        max_y = GRID_PIXEL_SIZE * self.tile_map.height
        self.camera_bounds = arcade.LRBT(
            self.window.width / 2.0,
            max_x - self.window.width / 2.0,
            self.window.height / 2.0,
            max_y,
        )

        self.pan_camera_to_user()
        self.game_over = False

    def on_draw(self):
        self.camera.use()
        self.clear()

        self.frame_count += 1

        self.player_list.draw()
        self.wall_list.draw()
        # Draw coin_list only if you have coins (empty here so safe)
        self.coin_list.draw()

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

        if self.game_over:
            arcade.draw_text(
                "Game Over",
                200,
                200,
                arcade.color.BLACK,
                30,
            )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = JUMP_SPEED
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = MOVEMENT_SPEED

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT or key == arcade.key.A or key == arcade.key.D:
            self.player_sprite.change_x = 0

    def on_update(self, delta_time):
        if self.player_sprite.right >= self.end_of_map:
            self.game_over = True

        if not self.game_over:
            self.physics_engine.update()
            self.player_sprite.update_animation(delta_time)

        coins_hit = arcade.check_for_collision_with_list(
            self.player_sprite, self.coin_list
        )
        for coin in coins_hit:
            coin.remove_from_sprite_lists()
            self.score += 1

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
    game = GameView()
    game.setup()

    window.show_view(game)
    window.run()


if __name__ == "__main__":
    main()
