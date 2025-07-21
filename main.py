import time
import arcade
import os

TILE_SCALING = 3
PLAYER_SCALING = 2.2
ENEMY_SCALING = 2

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Game"
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = SPRITE_PIXEL_SIZE * TILE_SCALING
CAMERA_PAN_SPEED = 0.30

PLAYER_HEALTH = 10
PLAYER_ATTACK_DAMAGE = 1
MUSHROOM_ENEMY_HEALTH = 3
MUSHROOM_ENEMY_DAMAGE = 1
RIGHT_FACING = 0
LEFT_FACING = 1

PLAYER_ATTACK_RANGE = 80
PLAYER_ATTACK_HEIGHT = 40
PLAYER_ATTACK_FRAME = 4
# Physics
MOVEMENT_SPEED = 5
UPDATES_PER_FRAME = 5
IDLE_UPDATES_PER_FRAME = 5
JUMP_UPDATES_PER_FRAME = 50
JUMP_SPEED = 20
GRAVITY = 1.1




class EnemyCharacter(arcade.Sprite):
    def __init__(self, x, y, max_health, left_boundary, right_boundary, walk_textures, attack_textures, takedamage_textures, death_textures):
        super().__init__(walk_textures[0][0], scale=ENEMY_SCALING)
        self.center_x = x
        self.center_y = y


        self.max_health = max_health
        self.left_boundary = left_boundary
        self.right_boundary = right_boundary
        self.walk_textures = walk_textures
        self.attack_textures = attack_textures
        self.death_textures = death_textures
        self.takedamage_textures = takedamage_textures
        self.death_textures = death_textures

        self.is_attacking = False
        self.is_taking_damage = False
        self.is_dead = False

        self.cur_texture = 0
        self.direction = RIGHT_FACING
        self.attack_cooldown = 0
        self.takedamage_frame = 0
        self.attack_cooldown = 0
        self.attack_cooldown_max = 60
        self.attack_damage_frame = 0
 
        self.has_dealt_damage = False
        self.current_health = max_health

        self.change_x = 1  # Start moving right

    def draw_health_bar(self):
        if self.is_dead:
            return
        
        bar_width = 50
        bar_height = 5
        y_offset = 14

        bottom = self.center_y + y_offset
        top = bottom + bar_height
        left = self.center_x - bar_width / 2
        right = left + bar_width

        # Background bar
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.RED)
        

        # Current health
        current_health_width = (self.current_health / self.max_health) * bar_width
        arcade.draw_lrbt_rectangle_filled(left, left + current_health_width, bottom, top, arcade.color.GREEN)

        # Health number
        health_string = f"{self.current_health}/{self.max_health}"
        arcade.draw_text(health_string, x=self.center_x, y=top + 2, font_size=10,
                        color=arcade.color.WHITE, anchor_x="center")
    def update(self):
        if self.is_dead:
            return

        # Patrol
        self.center_x += self.change_x
        if self.center_x < self.left_boundary:
            self.change_x = 1
            self.direction = RIGHT_FACING
        elif self.center_x > self.right_boundary:
            self.change_x = -1
            self.direction = LEFT_FACING


        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

    def update_animation(self, delta_time: float = 1/60):
        if self.is_dead:
            frame = min(self.cur_texture // UPDATES_PER_FRAME, len(self.death_textures) - 1)
            self.texture = self.death_textures[frame][self.direction]
            self.cur_texture += 1
            return
        

        if self.is_taking_damage:
            if self.takedamage_frame < len(self.takedamage_textures) * UPDATES_PER_FRAME:
                frame = self.takedamage_frame // UPDATES_PER_FRAME
                self.texture = self.takedamage_textures[frame][self.direction]
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
        


        # Walking
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
            self.left_boundary <= player_sprite.center_x <= self.right_boundary
        )
        current_frame = self.cur_texture // UPDATES_PER_FRAME

        if self.is_attacking:
            self.change_x = 0
            
            
            if current_frame == 6 and not self.has_dealt_damage:
                if distance_x < 50 and distance_y < 50:  
                    if player_sprite.invulnerable_timer <= 0:
                        player_sprite.take_damage(MUSHROOM_ENEMY_DAMAGE)
                        self.has_dealt_damage = True  
            
            # Reset the flag when attack animation ends
            if current_frame >= len(self.attack_textures) - 1:
                self.has_dealt_damage = False
                
            return 

        if player_in_boundaries:
            if raw_x < 0:
                self.direction = LEFT_FACING
            else:
                self.direction = RIGHT_FACING
            
            if distance_x < 50 and distance_y < 40:
                if self.attack_cooldown <= 0:
                    self.is_attacking = True
                    self.change_x = 0
                    self.cur_texture = 0 
                      
            else:
                chase_speed = 4
                if raw_x < 0:
                    self.change_x = -chase_speed  
                else:
                    self.change_x = chase_speed  
       
               # if self.change_x < 0 and self.center_x <= self.left_boundary:
                #    self.change_x = 0


              #  if self.change_x > 0 and self.center_x >= self.right_boundary:
               #    self.change_x = 0
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
        self.is_taking_damage = True
        self.takedamage_frame = 0
        self.is_attacking = False
        
        if self.current_health <= 0:
            self.is_dead = True
            self.cur_texture = 0
             


class PlayerCharacter(arcade.Sprite):
    def __init__(self, max_health, idle_textures, run_textures, jump_textures, fall_textures,
                 attack_textures, shield_textures, takedamage_textures, death_textures, enemy_list):
        super().__init__(idle_textures[0][0], scale=PLAYER_SCALING)

        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0
        self.jump_frame_count = 0
        self.jump_frame = 0
        self.attack_frame = 0
        self.shield_frame = 0
        self.takedamage_frame = 0
        self.death_frame = 0
        self.invulnerable_timer = 0
        

        self.is_attacking = False
        self.is_shielding = False
        self.is_taking_damage = False
        self.is_dead = False

        self.idle_textures = idle_textures
        self.run_textures = run_textures
        self.jump_textures = jump_textures
        self.fall_textures = fall_textures
        self.attack_textures = attack_textures
        self.shield_textures = shield_textures
        self.takedamage_textures = takedamage_textures
        self.death_textures = death_textures
        self.normal_hit_box = self.hit_box

        self.enemy_list = enemy_list  # Store reference to enemy list
        self.attack_range = PLAYER_ATTACK_RANGE
        self.attack_height = PLAYER_ATTACK_HEIGHT 
        self.has_dealt_damage = False
        self.attack_damage_frame = PLAYER_ATTACK_FRAME

        self.max_health = max_health
        self.current_health = max_health
    
    

    def take_damage(self, damage):
        if self.is_dead or self.invulnerable_timer > 0:
            return

        self.current_health -= damage
        self.invulnerable_timer = 60 # Set invulnerability for 1 second (60 frames)
        self.is_taking_damage = True
        self.takedamage_frame = 0


        if self.current_health <= 0:
            self.current_health = 0
            self.is_dead = True
            self.death_frame = 0
        else:
            self.is_taking_damage = True
            self.takedamage_frame = 0

    def heal(self, amount):
        self.current_health += amount
        if self.current_health > self.max_health:
            self.current_health = self.max_health

    def draw_health_bar(self):
        bar_width = 50
        bar_height = 5
        y_offset = 14

        bottom = self.center_y + y_offset
        top = bottom + bar_height
        left = self.center_x - bar_width / 2
        right = left + bar_width

        # Background bar
        arcade.draw_lrbt_rectangle_filled(left, right, bottom, top, arcade.color.RED)
        

        # Current health
        current_health_width = (self.current_health / self.max_health) * bar_width
        arcade.draw_lrbt_rectangle_filled(left, left + current_health_width, bottom, top, arcade.color.GREEN)

        # Health number
        health_string = f"{self.current_health}/{self.max_health}"
        arcade.draw_text(health_string, x=self.center_x, y=top + 2, font_size=10,
                         color=arcade.color.WHITE, anchor_x="center")

    def start_attack(self):
        if not self.is_attacking:
            self.is_attacking = True
            self.cur_texture = 0

    def start_shield(self):
        if not self.is_shielding:
            self.is_shielding = True
            self.cur_texture = 0


    def update_animation(self, delta_time: float = 1 / 60):
        if self.change_x < 0:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0:
            self.character_face_direction = RIGHT_FACING

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        # Death animation
        if self.is_dead:
            self.death_frame += 1
            if self.death_frame >= len(self.death_textures) * UPDATES_PER_FRAME:
                # Death animation finished, respawn the player
                self.death_frame = 0
                self.is_dead = False
                self.current_health = self.max_health
                # Reset position or any other respawn logic here
                self.center_x = 196  # Example respawn position x
                self.center_y = 270  # Example respawn position y

            else:
                frame = self.death_frame // UPDATES_PER_FRAME
                direction = self.character_face_direction
                self.texture = self.death_textures[frame][direction]
            return

        # Taking damage animation
        if self.is_taking_damage:
            if self.takedamage_frame < len(self.takedamage_textures) * UPDATES_PER_FRAME:
                frame = self.takedamage_frame // UPDATES_PER_FRAME
                self.texture = self.takedamage_textures[frame][self.character_face_direction]
                self.takedamage_frame += 1
            else:
                self.is_taking_damage = False
            return

        if self.change_y > 0:  # Moving upward (jumping)
            self.jump_frame += 1
            if self.jump_frame >= len(self.jump_textures):
                self.jump_frame = len(self.jump_textures) - 1  # Clamp to last jump frame
            self.texture = self.jump_textures[self.jump_frame][self.character_face_direction]
            return

        elif self.change_y < 0:  # Moving downward (falling)
            self.jump_frame += 1
            if self.jump_frame >= len(self.fall_textures):
                self.jump_frame = len(self.fall_textures) - 1  # Clamp to last fall frame
            self.texture = self.fall_textures[self.jump_frame][self.character_face_direction]
            return

        else:  # On ground (idle or running)
            self.jump_frame = 0  # Reset jump/fall animation

        
        if self.change_x != 0:
            self.cur_texture += 1
            if self.cur_texture >= len(self.run_textures) * UPDATES_PER_FRAME:
                self.cur_texture = 0
            frame = self.cur_texture // UPDATES_PER_FRAME
            direction = self.character_face_direction
            self.texture = self.run_textures[frame][direction]
        else:
            # Idle animation
            self.cur_texture += 1
            if self.cur_texture >= len(self.idle_textures) * IDLE_UPDATES_PER_FRAME:
                self.cur_texture = 0
            frame = self.cur_texture // IDLE_UPDATES_PER_FRAME
            direction = self.character_face_direction
            self.texture = self.idle_textures[frame][direction]



        if self.is_attacking:
            self.change_x = 0  # Lock movement
            current_frame = self.attack_frame // UPDATES_PER_FRAME

            # SIMPLIFIED DAMAGE CHECK - uses direct distance comparison
            if current_frame == self.attack_damage_frame and not self.has_dealt_damage:
                for enemy in self.enemy_list:
                    # Calculate distances
                    horizontal_range = abs(enemy.center_x - self.center_x)
                    vertical_range = abs(enemy.center_y - self.center_y)
                    
                    # Check if enemy is within attack range and in facing direction
                    if (horizontal_range < self.attack_range and 
                        vertical_range < self.attack_height and
                        ((self.character_face_direction == RIGHT_FACING and enemy.center_x > self.center_x) or
                         (self.character_face_direction == LEFT_FACING and enemy.center_x < self.center_x))):
                        enemy.take_damage(PLAYER_ATTACK_DAMAGE)
                self.has_dealt_damage = True
            elif current_frame != self.attack_damage_frame:
                self.has_dealt_damage = False  # Reset for next attack

            # Animation progression
            self.attack_frame += 1
            if self.attack_frame >= len(self.attack_textures) * UPDATES_PER_FRAME:
                self.attack_frame = 0
                self.is_attacking = False
            else:
                self.texture = self.attack_textures[current_frame][self.character_face_direction]
            return



        
        if self.is_shielding:
            self.shield_frame += 1
            if self.shield_frame >= len(self.shield_textures) * UPDATES_PER_FRAME:
                self.shield_frame = 0
                self.is_shielding = False
            else:
                frame = self.shield_frame // UPDATES_PER_FRAME
                direction = self.character_face_direction
                self.texture = self.shield_textures[frame][direction]
            return


class GameView(arcade.View):
    def __init__(self):
        super().__init__()

        self.tile_map = None
        self.player_list = None
        self.enemy_list = arcade.SpriteList()
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

        self.hit_box_base_colour = (255, 255, 255, 255)
        self.hit_box_collision_colour = (255, 0, 0, 255)
        self.colliding = False
        self.fps_text = arcade.Text("", x=10, y=40, color=arcade.color.WHITE, font_size=14)
        self.distance_text = arcade.Text("0.0", x=10, y=20, color=arcade.color.WHITE, font_size=14)

      
        character_path = "resources/sprites/blue_player"
        enemy_path = "resources/sprites/mushroom_enemy"

        
        self.run_textures = []
        for i in range(8):  # Adjust range based on your walk sprites
            run_texture = arcade.load_texture(f"{character_path}/player_run/player_run{i}.png")
            self.run_textures.append((run_texture, run_texture.flip_left_right()))

        self.jump_textures = []
        for i in range(8):
            jump_textures = arcade.load_texture(f"{character_path}/player_jump/player_jump{i}.png")
            self.jump_textures.append((jump_textures, jump_textures.flip_left_right()))

        self.fall_textures = []
        for i in range(6):
            fall_texture = arcade.load_texture(f"{character_path}/player_fall/player_fall{i}.png")
            self.fall_textures.append((fall_texture, fall_texture.flip_left_right()))

        self.idle_textures = []
        for i in range(6):
            idle_textures = arcade.load_texture(f"{character_path}/player_idle/player_idle{i}.png")
            self.idle_textures.append((idle_textures, idle_textures.flip_left_right()))

        self.attack_textures = []
        for i in range(6):
            attack_textures = arcade.load_texture(f"{character_path}/player_attack/player_attack{i}.png")
            self.attack_textures.append((attack_textures, attack_textures.flip_left_right()))

        self.shield_textures = []
        for i in range(3):
            shield_textures = arcade.load_texture(f"{character_path}/player_shield/player_shield{i}.png")
            self.shield_textures.append((shield_textures, shield_textures.flip_left_right()))
        
        self.takedamage_textures = []
        for i in range(4):
            tex = arcade.load_texture(f"{character_path}/player_takedamage/player_takedamage{i}.png")
            self.takedamage_textures.append((tex, tex.flip_left_right()))

        self.death_textures = []
        for i in range(12):
            tex = arcade.load_texture(f"{character_path}/player_death/player_death{i}.png")
            self.death_textures.append((tex, tex.flip_left_right()))


        self.enemy_walk_textures = []
        for i in range(4):  # or however many frames you have
            tex = arcade.load_texture(f"{enemy_path}/mushroom_idle/mushroom_idle{i}.png")
            self.enemy_walk_textures.append((tex, tex.flip_left_right()))

        self.enemy_attack_textures = []
        for i in range(8):
            tex = arcade.load_texture(f"{enemy_path}/mushroom_attack/mushroom_attack{i}.png")
            self.enemy_attack_textures.append((tex, tex.flip_left_right()))

        self.enemy_death_textures = []
        for i in range(4):
            tex = arcade.load_texture(f"{enemy_path}/mushroom_death/mushroom_death{i}.png")
            self.enemy_death_textures.append((tex, tex.flip_left_right()))

        self.enemy_takedamage_textures = []
        for i in range(4):
            tex = arcade.load_texture(f"{enemy_path}/mushroom_takedamage/mushroom_takedamage{i}.png")
            self.enemy_takedamage_textures.append((tex, tex.flip_left_right()))




        
        
        fall = arcade.load_texture(f"{character_path}/player_idle/player_idle1.png")

        self.fall_texture_pair = fall, fall.flip_left_right()




    def setup(self):
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()

        self.player_sprite = PlayerCharacter(
            PLAYER_HEALTH,
            self.idle_textures,
            self.run_textures,
            self.jump_textures,
            self.fall_textures,
            self.attack_textures,
            self.shield_textures,
            self.takedamage_textures,
            self.death_textures,
            self.enemy_list
        )
        self.player_sprite.center_x = 196
        self.player_sprite.center_y = 270
        self.player_list.append(self.player_sprite)

       # enemy = EnemyCharacter(
          #  x=600, y=270,  # position of the enemy
            #left_boundary=500,
           # right_boundary=1000,
           # max_health=MUSHROOM_ENEMY_HEALTH,
          #  walk_textures=self.enemy_walk_textures,
         #   attack_textures=self.enemy_attack_textures,
        #    takedamage_textures=self.enemy_takedamage_textures,
       #     death_textures=self.enemy_death_textures
      #  )
       # self.enemy_list.append(enemy)

        
        file_path = os.path.dirname(os.path.abspath(__file__))
        map_path = os.path.join(file_path, "resources/maps/testmap.tmx")   

        layer_options = {

            "Mushroom_Enemies": {"use_spatial_hash": True},

            "floor": {"use_spatial_hash": True},

            "Background_Filler": {"use_spatial_hash": False},

            "Background": {"use_spatial_hash": False},

            "Midground": {"use_spatial_hash": False},

            "Foreground": {"use_spatial_hash": False},
        }

        self.tile_map = arcade.load_tilemap(
        map_path,
        scaling=TILE_SCALING,
        layer_options=layer_options,
        )

        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        self.load_enemies_from_map()

        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        self.wall_list = self.tile_map.sprite_lists["floor"]
        self.background_filler = self.scene["Background_Filler"]
        self.background = self.scene["Background"]
        self.midground = self.scene["Midground"]
        self.foreground = self.scene["Foreground"]

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
        self.camera.use()  # World coordinate system for game world and player
        self.clear()

        self.scene["Background_Filler"].draw()
        self.scene["Background"].draw()
        self.scene["Midground"].draw()
        self.scene["Foreground"].draw()

        self.frame_count += 1

        self.player_list.draw()
        self.wall_list.draw()
        self.coin_list.draw()
        self.enemy_list.draw()

        # Draw health bars in world space *before* switching to GUI camera
        for sprite in self.player_list:
            sprite.draw_health_bar()


        for enemy in self.enemy_list:
    # Left boundary (red line)
            enemy.draw_health_bar()
            arcade.draw_line(
                enemy.left_boundary, enemy.center_y - 50,
                enemy.left_boundary, enemy.center_y + 50,
                arcade.color.RED, 2
            )
            # Right boundary (green line)
            arcade.draw_line(
                enemy.right_boundary, enemy.center_y - 50,
                enemy.right_boundary, enemy.center_y + 50,
                arcade.color.GREEN, 2
            )
            # Current path (blue line between boundaries)
            arcade.draw_line(
                enemy.left_boundary, enemy.center_y,
                enemy.right_boundary, enemy.center_y,
                arcade.color.BLUE, 1
            )
        

        if self.colliding:
            self.player_list.draw_hit_boxes(self.hit_box_collision_colour)
            arcade.draw_text(
                "Colliding with enemy!",
                self.player_sprite.center_x,
                self.player_sprite.center_y + 20,
                arcade.color.RED,
                font_size=24,
            )
            
        else:
            self.player_list.draw_hit_boxes(self.hit_box_base_colour)
  

        self.gui_camera.use()  # Now switch to screen-space for UI text

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

    def load_enemies_from_map(self):
        if "Mushroom_Enemies" not in self.tile_map.object_lists:
            return
        
        enemy_layer = self.tile_map.object_lists["Mushroom_Enemies"]

        for enemy_obj in enemy_layer:
            position_x = enemy_obj.shape[0]  # or enemy_obj.shape.x in newer versions
            position_y = enemy_obj.shape[1]  # or enemy_obj.shape.y


            left_boundary = enemy_obj.properties.get("left_boundary", position_x - 100)
            right_boundary = enemy_obj.properties.get("right_boundary", position_x + 100)

            enemy = EnemyCharacter(
                x=position_x,
                y=0,  # will set below
                left_boundary=left_boundary,
                right_boundary=right_boundary,
                max_health=MUSHROOM_ENEMY_HEALTH,
                walk_textures= self.enemy_walk_textures,
                attack_textures=self.enemy_attack_textures,
                takedamage_textures=self.enemy_takedamage_textures,
                death_textures=self.enemy_death_textures
            )
            enemy.bottom = position_y 
            self.enemy_list.append(enemy)


    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                self.player_sprite.change_y = JUMP_SPEED
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player_sprite.change_x = -MOVEMENT_SPEED
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player_sprite.change_x = MOVEMENT_SPEED

        elif key == arcade.key.SPACE:
            self.player_sprite.start_attack()
        
        elif key == arcade.key.E:
            self.player_sprite.start_shield()

        elif key == arcade.key.T:  # Press 'T' to take damage
            self.player_sprite.take_damage(1)

        elif key == arcade.key.Y:  # Press 'Y' to trigger death animation directly
            self.player_sprite.current_health = 0
            self.player_sprite.is_dead = True
            self.player_sprite.death_frame = 0

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
    game = GameView()
    game.setup()

    window.show_view(game)
    window.run()


if __name__ == "__main__":
    main()
