import os
import pygame
import sys
import random
import math

os.chdir(os.path.dirname(os.path.abspath(__file__)))

ASSETS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets')

pygame.init()
WIDTH, HEIGHT = 1365, 700
BLOCK_SIZE = 40
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Starlight Runner")
clock = pygame.time.Clock()

golden_star_icon = pygame.image.load(os.path.join(ASSETS_PATH, "golden_star.png")).convert_alpha()
pygame.display.set_icon(golden_star_icon)

pygame.mixer.init()

bgm = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "bgm.ogg"))
jump_sound = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "jump.wav"))
timer_sound = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "timer.wav"))
xp_sound = pygame.mixer.Sound(os.path.join(ASSETS_PATH, "xp.wav"))

bgm.play(-1)

TEXT_COLOR  = (255, 255, 0)
XP_COLOR    = (255, 255, 0)

def get_pixel_font(size):
    return pygame.font.Font(os.path.join(ASSETS_PATH, "starlight_font.ttf"), size)

layer1_sky = pygame.image.load(os.path.join(ASSETS_PATH, "layer1_sky.png")).convert_alpha()
layer1_sky = pygame.transform.scale(layer1_sky, (WIDTH, HEIGHT))

layer2_mountains = pygame.image.load(os.path.join(ASSETS_PATH, "layer2_mountains.png")).convert_alpha()
layer2_mountains = pygame.transform.scale(layer2_mountains, (WIDTH, HEIGHT))

layer3_forest = pygame.image.load(os.path.join(ASSETS_PATH, "layer3_forest.png")).convert_alpha()
layer3_forest = pygame.transform.scale(layer3_forest, (WIDTH, HEIGHT))

layer4_clouds = pygame.image.load(os.path.join(ASSETS_PATH, "layer4_clouds.png")).convert_alpha()
layer4_clouds = pygame.transform.scale(layer4_clouds, (WIDTH, HEIGHT))

bg_layers = [
    (layer1_sky,       0.1),
    (layer2_mountains, 0.3),
    (layer3_forest,    0.5),
    (layer4_clouds,    0.7),
]

def draw_parallax_background(camera_offset_x):
    for layer_img, factor in bg_layers:
        layer_width = layer_img.get_width()
        offset = int(camera_offset_x * factor) % layer_width
        screen.blit(layer_img, (-offset, 0))
        screen.blit(layer_img, (-offset + layer_width, 0))

tile_block_img = pygame.image.load(os.path.join(ASSETS_PATH, "tile_block.png")).convert_alpha()
tile_block_img = pygame.transform.scale(tile_block_img, (BLOCK_SIZE, BLOCK_SIZE))

char_scale = (int(BLOCK_SIZE * 1.2), int(BLOCK_SIZE * 1.2))
expression_scale = (int(char_scale[0] * 0.9), int(char_scale[1] * 0.9))

player_body = pygame.image.load(os.path.join(ASSETS_PATH, "player_body.png")).convert_alpha()
player_body = pygame.transform.scale(player_body, char_scale)

ai_body1 = pygame.image.load(os.path.join(ASSETS_PATH, "ai_body1.png")).convert_alpha()
ai_body1 = pygame.transform.scale(ai_body1, char_scale)

ai_body2 = pygame.image.load(os.path.join(ASSETS_PATH, "ai_body2.png")).convert_alpha()
ai_body2 = pygame.transform.scale(ai_body2, char_scale)

ai_body3 = pygame.image.load(os.path.join(ASSETS_PATH, "ai_body3.png")).convert_alpha()
ai_body3 = pygame.transform.scale(ai_body3, char_scale)

expression_smile = pygame.image.load(os.path.join(ASSETS_PATH, "expression_smile.png")).convert_alpha()
expression_smile = pygame.transform.scale(expression_smile, expression_scale)

expression_angry = pygame.image.load(os.path.join(ASSETS_PATH, "expression_angry.png")).convert_alpha()
expression_angry = pygame.transform.scale(expression_angry, expression_scale)

expression_happy = pygame.image.load(os.path.join(ASSETS_PATH, "expression_happy.png")).convert_alpha()
expression_happy = pygame.transform.scale(expression_happy, expression_scale)

def draw_character(surface, rect, body_img, expression_type):
    surface.blit(body_img, rect)
    expr_rect = rect.copy()
    expr_rect.width, expr_rect.height = expression_scale
    expr_rect.x += (char_scale[0] - expression_scale[0]) // 2
    expr_rect.y += (char_scale[1] - expression_scale[1]) // 2

    if expression_type == "happy":
        overlay = expression_happy
    elif expression_type == "angry":
        overlay = expression_angry
    else:
        overlay = expression_smile
    surface.blit(overlay, expr_rect)

class Block:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
        self.visible = True

    def update(self, dt):
        pass

    def draw(self, surface, offset_x=0):
        if not self.visible:
            return
        offset_rect = self.rect.copy()
        offset_rect.x -= int(offset_x)
        surface.blit(tile_block_img, offset_rect)

class XPPoint:
    def __init__(self, x, y):
        self.x = x + BLOCK_SIZE // 2
        self.y = y + BLOCK_SIZE // 2
        self.radius = 10
        self.collected = False

    def draw(self, surface, offset_x=0):
        if self.collected:
            return
        cx = self.x - int(offset_x)
        cy = self.y
        r = self.radius
        points = []
        for i in range(10):
            angle = i * (math.pi / 5) - math.pi / 2
            rad = r if i % 2 == 0 else r / 2
            px = cx + rad * math.cos(angle)
            py = cy + rad * math.sin(angle)
            points.append((px, py))
        pygame.draw.polygon(surface, XP_COLOR, points)
        pygame.draw.polygon(surface, XP_COLOR, points, 1)

    def get_rect(self):
        return pygame.Rect(self.x - self.radius, self.y - self.radius,
                           self.radius * 2, self.radius * 2)

class Player:
    def __init__(self, x, y, starting_xp=0, body_img=None):
        self.rect = pygame.Rect(x, y, BLOCK_SIZE // 2, BLOCK_SIZE)
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_speed = 10
        self.on_ground = False
        self.xp = starting_xp
        self.name = "YOU"
        self.body_img = body_img
        self.expression = "smile"

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
        if keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = -self.jump_speed
            self.on_ground = False
            jump_sound.play()

    def apply_gravity(self):
        gravity = 0.5
        self.vel_y += gravity
        if self.vel_y > 10:
            self.vel_y = 10

    def move_and_collide(self, blocks):
        self.rect.x += self.vel_x
        for block in blocks:
            if block.visible and self.rect.colliderect(block.rect):
                if self.vel_x > 0:
                    self.rect.right = block.rect.left
                elif self.vel_x < 0:
                    self.rect.left = block.rect.right

        self.rect.y += self.vel_y
        self.on_ground = False
        for block in blocks:
            if block.visible and self.rect.colliderect(block.rect):
                if self.vel_y > 0:
                    self.rect.bottom = block.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.rect.bottom
                    self.vel_y = 0

    def update(self, blocks):
        self.handle_input()
        self.apply_gravity()
        self.move_and_collide(blocks)

    def draw(self, surface, offset_x=0):
        draw_rect = self.rect.copy()
        draw_rect.x -= int(offset_x)
        draw_rect.width, draw_rect.height = char_scale
        draw_character(surface, draw_rect, self.body_img, self.expression)
        font = get_pixel_font(18)
        name_surf = font.render(self.name, True, TEXT_COLOR)
        surface.blit(name_surf, (draw_rect.x, draw_rect.y - 25))

class Racer:
    def __init__(self, x, y, name="AI Racer", body_img=None):
        self.rect = pygame.Rect(x, y, BLOCK_SIZE // 2, BLOCK_SIZE)
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_speed = 10
        self.on_ground = False
        self.name = name
        self.body_img = body_img
        self.expression = "smile"
        self.reaction_timer = 0

    def ai_move(self, blocks, dt):
        self.vel_x = self.speed
        if self.reaction_timer > 0:
            self.reaction_timer -= dt
            return
        look_ahead_distance = 80
        ahead_rect = pygame.Rect(self.rect.right, self.rect.y,
                                 look_ahead_distance, self.rect.height)
        obstacle_count = 0
        for block in blocks:
            if block.visible and ahead_rect.colliderect(block.rect):
                obstacle_count += 1
        if obstacle_count > 0 and self.on_ground:
            self.vel_y = -self.jump_speed
            self.on_ground = False
            self.reaction_timer = 150

    def apply_gravity(self):
        gravity = 0.5
        self.vel_y += gravity
        if self.vel_y > 10:
            self.vel_y = 10

    def move_and_collide(self, blocks):
        self.rect.x += self.vel_x
        for block in blocks:
            if block.visible and self.rect.colliderect(block.rect):
                if self.vel_x > 0:
                    self.rect.right = block.rect.left
                elif self.vel_x < 0:
                    self.rect.left = block.rect.right

        self.rect.y += self.vel_y
        self.on_ground = False
        for block in blocks:
            if block.visible and self.rect.colliderect(block.rect):
                if self.vel_y > 0:
                    self.rect.bottom = block.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = block.rect.bottom
                    self.vel_y = 0

    def update(self, blocks, dt):
        self.ai_move(blocks, dt)
        self.apply_gravity()
        self.move_and_collide(blocks)

    def draw(self, surface, offset_x=0):
        draw_rect = self.rect.copy()
        draw_rect.x -= int(offset_x)
        draw_rect.width, draw_rect.height = char_scale
        draw_character(surface, draw_rect, self.body_img, self.expression)

pattern_heart = [
    (0,1), (0,3),
    (1,0), (1,2), (1,4),
    (2,0), (2,2), (2,4),
    (3,1), (3,3),
    (4,2)
]
pattern_circle = [
    (0,2),
    (1,1), (1,3),
    (2,0), (2,4),
    (3,1), (3,3),
    (4,2)
]
pattern_diamond = [
    (0,2),
    (1,1), (1,3),
    (2,0), (2,2), (2,4),
    (3,1), (3,3),
    (4,2)
]
pattern_triangle = [
    (0,2),
    (1,1), (1,2), (1,3),
    (2,0), (2,1), (2,2), (2,3), (2,4)
]
xp_patterns = [pattern_heart, pattern_circle, pattern_diamond, pattern_triangle]

def place_pattern(level, pattern, top_row, left_col):
    for (dr, dc) in pattern:
        if 0 <= top_row + dr < len(level) and 0 <= left_col + dc < len(level[0]):
            if level[top_row + dr][left_col + dc] == ' ':
                level[top_row + dr][left_col + dc] = 's'

def generate_level_map(width, rows=12, min_ground=2, max_ground=4):
    ground_heights = []
    current_height = random.randint(min_ground, max_ground)
    for i in range(width):
        if i == 0:
            current_height = random.randint(min_ground, max_ground)
        else:
            change = random.choice([-1, 0, 1])
            current_height += change
            current_height = max(min_ground, min(current_height, max_ground))
        ground_heights.append(current_height)

    level = [[' ' for _ in range(width)] for _ in range(rows)]
    for col in range(width):
        h = ground_heights[col]
        top = rows - h
        level[top][col] = 'G'
        for row in range(top+1, rows):
            level[row][col] = 'X'

    player_col = 5 if width > 5 else 0
    player_row = rows - ground_heights[player_col] - 1
    if player_row < 0:
        player_row = 0
    level[player_row][player_col] = 'P'

    for _ in range(2):
        pat = random.choice(xp_patterns)
        pat_height = max(r for (r, c) in pat) + 1
        pat_width = max(c for (r, c) in pat) + 1
        min_row = rows // 3
        max_row = (2 * rows) // 3 - pat_height
        if max_row < min_row:
            max_row = min_row
        top_row = random.randint(min_row, max_row)
        left_col = random.randint(0, width - pat_width)
        place_pattern(level, pat, top_row, left_col)

    return [''.join(row) for row in level]

levels = [generate_level_map(width) for width in range(160, 260, 10)]

def create_level(level_map, starting_xp):
    last_index = 0
    for i, row in enumerate(level_map):
        if any(ch in "XGPs" for ch in row):
            last_index = i
    level_map = level_map[:last_index+1]
    rows = len(level_map)
    vertical_offset = HEIGHT - rows * BLOCK_SIZE

    blocks = []
    xp_points = []
    player = None

    for row_idx, row in enumerate(level_map):
        for col_idx, char in enumerate(row):
            x = col_idx * BLOCK_SIZE
            y = row_idx * BLOCK_SIZE + vertical_offset
            if char in "GX":
                blocks.append(Block(x, y))
            elif char == "P":
                player = Player(x, y, starting_xp, body_img=player_body)
            elif char == "s":
                xp_points.append(XPPoint(x, y))

    finish_line_x = len(level_map[0]) * BLOCK_SIZE
    ai_racers = []
    if player is not None:
        start_x = player.rect.x
        start_y = player.rect.y
        ai_racers.append(Racer(start_x, start_y - 50, name="Racer 1", body_img=ai_body1))
        ai_racers.append(Racer(start_x, start_y,       name="Racer 2", body_img=ai_body2))
        ai_racers.append(Racer(start_x, start_y + 50,  name="Racer 3", body_img=ai_body3))

    return blocks, xp_points, player, ai_racers, finish_line_x

def show_main_menu():
    menu_font = get_pixel_font(50)
    info_font = get_pixel_font(28)
    while True:
        draw_parallax_background(0)
        title = menu_font.render("Starlight Runner", True, TEXT_COLOR)
        instr = info_font.render("Press ENTER to Start  |  ESC to Quit", True, TEXT_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
        screen.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT//2))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

def show_final_screen(avg_rank):
    font_title = get_pixel_font(44)
    font_info = get_pixel_font(26)
    clock = pygame.time.Clock()

    while True:
        draw_parallax_background(0)
        title_surf = font_title.render("Thanks for playing!", True, (0,255,0))
        rank_surf  = font_info.render(f"Your average rank: {avg_rank:.2f}", True, TEXT_COLOR)
        instr_surf = font_info.render('Press ENTER to play again or ESC to close', True, TEXT_COLOR)

        screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, HEIGHT//3))
        screen.blit(rank_surf,  (WIDTH//2 - rank_surf.get_width()//2, HEIGHT//2))
        screen.blit(instr_surf, (WIDTH//2 - instr_surf.get_width()//2, HEIGHT//2 + 50))

        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True
                elif event.key == pygame.K_ESCAPE:
                    return False

def draw_hud(surface, player, ai_racers, level_num):
    font = get_pixel_font(20)
    racers = [player] + ai_racers
    sorted_racers = sorted(racers, key=lambda r: r.rect.x, reverse=True)
    rank = sorted_racers.index(player) + 1
    level_text = f"Level {level_num}"
    xp_text = f"XP {player.xp}"
    rank_text = f"Rank {rank}/{len(racers)}"
    y_offset = 10
    surface.blit(font.render(level_text, True, TEXT_COLOR), (10, y_offset))
    y_offset += font.get_height() + 5
    surface.blit(font.render(xp_text, True, TEXT_COLOR), (10, y_offset))
    y_offset += font.get_height() + 5
    surface.blit(font.render(rank_text, True, TEXT_COLOR), (10, y_offset))
    pause_surf = font.render("p: pause", True, TEXT_COLOR)
    restart_surf = font.render("r: restart", True, TEXT_COLOR)
    surface.blit(pause_surf, (WIDTH - pause_surf.get_width() - 10, 10))
    surface.blit(restart_surf, (WIDTH - restart_surf.get_width() - 10,
                                10 + pause_surf.get_height() + 5))
    return rank

def race_finish_screen(surface, winner_name):
    font = get_pixel_font(40)
    text_surface = font.render(f"{winner_name} Won the Race!", True, (0,255,0))
    screen.blit(text_surface, (WIDTH//2 - text_surface.get_width()//2, HEIGHT//2 - 50))
    pygame.display.flip()
    pygame.time.delay(3000)

def level_countdown(surface, level_num):
    font_big = get_pixel_font(60)
    font_small = get_pixel_font(28)

    draw_parallax_background(0)
    level_text = font_small.render(f"Level {level_num}", True, TEXT_COLOR)
    screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2,
                             HEIGHT//2 - level_text.get_height() - 50))
    pygame.display.flip()
    pygame.time.delay(1000)

    for count in range(3, 0, -1):
        draw_parallax_background(0)
        count_text = font_big.render(str(count), True, TEXT_COLOR)
        screen.blit(count_text, (WIDTH//2 - count_text.get_width()//2,
                                 HEIGHT//2 - count_text.get_height()//2))
        pygame.display.flip()
        timer_sound.play()
        pygame.time.delay(1000)

    draw_parallax_background(0)
    go_text = font_big.render("Go!", True, TEXT_COLOR)
    screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2,
                          HEIGHT//2 - go_text.get_height()//2))
    pygame.display.flip()
    pygame.time.delay(500)

def restart_level_screen(surface):
    font = get_pixel_font(36)
    text_surface = font.render("You fell! Press r to restart", True, (255,0,0))
    surface.blit(text_surface, (WIDTH//2 - text_surface.get_width()//2,
                                HEIGHT//2 - text_surface.get_height()//2))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                waiting = False

def draw_finish_line(surface, finish_line_x, camera_offset_x):
    line_screen_x = finish_line_x - int(camera_offset_x)
    line_width = 20
    square_size = 10
    for y in range(0, HEIGHT, square_size):
        for x_off in range(0, line_width, square_size):
            if ((y // square_size) + (x_off // square_size)) % 2 == 0:
                color = (255,255,255)
            else:
                color = (0,0,0)
            rect_x = line_screen_x + x_off
            pygame.draw.rect(surface, color, (rect_x, y, square_size, square_size))

def main():
    show_main_menu()

    while True:
        ranks_per_level = []
        total_xp = 0
        current_level_index = 0
        total_levels = len(levels)
        paused = False

        while current_level_index < total_levels:
            level_map = levels[current_level_index]
            blocks, xp_points, player, ai_racers, finish_line_x = create_level(level_map, total_xp)

            level_num = current_level_index + 1
            level_countdown(screen, level_num)

            level_running = True
            race_finished = False

            while level_running:
                dt = clock.tick(FPS)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_p:
                            paused = not paused
                        elif event.key == pygame.K_r:
                            level_running = False
                            race_finished = False
                            break

                if paused:
                    pause_font = get_pixel_font(36)
                    pause_text = pause_font.render("Paused", True, TEXT_COLOR)
                    screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2,
                                             HEIGHT//2 - pause_text.get_height()//2))
                    pygame.display.flip()
                    continue

                camera_offset_x = max(0, player.rect.x - 100)

                draw_parallax_background(camera_offset_x)

                player.update(blocks)
                for racer in ai_racers:
                    racer.update(blocks, dt)

                for block in blocks:
                    block.update(dt)

                for xp in xp_points:
                    if not xp.collected and player.rect.colliderect(xp.get_rect()):
                        xp.collected = True
                        player.xp += 1
                        xp_sound.play()

                all_racers = [player] + ai_racers
                sorted_racers = sorted(all_racers, key=lambda r: r.rect.x, reverse=True)
                for i, racer in enumerate(sorted_racers):
                    if i == 0:
                        racer.expression = "happy"
                    elif i == len(sorted_racers) - 1:
                        racer.expression = "angry"
                    else:
                        racer.expression = "smile"

                valid_racers = [r for r in all_racers if r.rect.top <= HEIGHT]
                if not race_finished:
                    for racer in valid_racers:
                        if racer.rect.x >= finish_line_x:
                            race_finished = True
                            sorted_racers = sorted(valid_racers, key=lambda r: r.rect.x, reverse=True)
                            winner = sorted_racers[0]
                            race_finish_screen(screen, winner.name)
                            level_running = False
                            break

                for block in blocks:
                    block.draw(screen, camera_offset_x)
                for xp in xp_points:
                    xp.draw(screen, camera_offset_x)
                player.draw(screen, camera_offset_x)
                for racer in ai_racers:
                    racer.draw(screen, camera_offset_x)

                draw_finish_line(screen, finish_line_x, camera_offset_x)

                player_rank = draw_hud(screen, player, ai_racers, level_num)
                pygame.display.flip()

                if not race_finished and player.rect.top > HEIGHT:
                    restart_level_screen(screen)
                    level_running = False

            if race_finished:
                ranks_per_level.append(player_rank)
                total_xp = player.xp
                current_level_index += 1

        if len(ranks_per_level) > 0:
            avg_rank = sum(ranks_per_level) / len(ranks_per_level)
        else:
            avg_rank = 1.0

        replay = show_final_screen(avg_rank)
        if not replay:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()