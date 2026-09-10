import math
import random
import sys

import pygame

WIDTH, HEIGHT = 900, 500
FPS = 60

GROUND_Y = 380
GRAVITY = 0.9
JUMP_VELOCITY = -15.5

BASE_SPEED = 6.0
MAX_SPEED = 13.0
SPEED_RAMP = 0.0011

FINISH_DISTANCE = 2200

SKY_TOP = (110, 170, 225)
SKY_HORIZON = (255, 200, 165)
ROAD = (70, 70, 78)
ROAD_LINE = (230, 230, 230)
GROUND_DIRT = (90, 130, 70)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK = (30, 30, 40)

CUTOUT_BORDER = (250, 244, 230)
SHADOW_RGBA = (20, 15, 10, 90)

BUILDING_COLORS = [
    (120, 110, 100),
    (90, 100, 115),
    (150, 120, 95),
    (105, 95, 130),
    (100, 110, 90),
]

RIVAL_COLORS = [(90, 90, 200), (200, 90, 90), (90, 170, 90)]

PLAYER_X = 140
HORSE_W, HORSE_H = 78, 52

KOREAN_FONT_CANDIDATES = [
    "malgun gothic",
    "applegothic",
    "applesdgothicneo",
    "notosanscjkkr",
    "notosanskr",
    "nanumgothic",
    "nanumbarungothic",
    "unbatang",
    "unfonts",
    "gulim",
    "batang",
    "droidsansfallback",
]


def load_korean_font(size, bold=False):
    for name in KOREAN_FONT_CANDIDATES:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont(None, size, bold=bold)


def shade(color, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in color)


def vertical_gradient(size, top_color, bottom_color):
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(int(top_color[i] + (bottom_color[i] - top_color[i]) * t) for i in range(3)) + (255,)
        pygame.draw.line(surf, color, (0, y), (w, y))
    return surf


def clip_to_ellipse(rect_surface):
    w, h = rect_surface.get_size()
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(mask, (255, 255, 255, 255), mask.get_rect())
    rect_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return rect_surface


def draw_alpha_ellipse(surface, color_rgba, rect):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.ellipse(s, color_rgba, s.get_rect())
    surface.blit(s, rect.topleft)


def make_grain_overlay(width, height):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    rng = random.Random(20240917)
    step = 2
    for y in range(0, height, step):
        for x in range(0, width, step):
            if rng.random() < 0.10:
                v = 255 if rng.random() < 0.7 else 0
                alpha = rng.randint(5, 22)
                surf.set_at((x, y), (v, v, v, alpha))
    return surf


def make_vignette(width, height):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    cx, cy = width / 2, height / 2
    maxd = math.hypot(cx, cy)
    step = 4
    for y in range(0, height, step):
        for x in range(0, width, step):
            d = math.hypot(x - cx, y - cy) / maxd
            if d > 0.6:
                alpha = min(130, int((d - 0.6) * 260))
                pygame.draw.rect(surf, (10, 8, 5, alpha), (x, y, step, step))
    return surf


def draw_horse(surface, x, y, color, leg_phase, ducking=False):
    body_h = HORSE_H - 14 if ducking else HORSE_H
    body_w = HORSE_W - 18

    shadow_rect = pygame.Rect(int(x) - 4, int(y) - 6, HORSE_W + 4, 14)
    draw_alpha_ellipse(surface, SHADOW_RGBA, shadow_rect)

    light = shade(color, 1.3)
    dark = shade(color, 0.65)

    body_rect = pygame.Rect(int(x), int(y - body_h), body_w, body_h - 10)
    pygame.draw.ellipse(surface, CUTOUT_BORDER, body_rect.inflate(6, 6))
    grad = clip_to_ellipse(vertical_gradient((body_rect.width, body_rect.height), light, dark))
    surface.blit(grad, body_rect.topleft)

    neck_top = (x + HORSE_W - 30, y - body_h - 18)
    neck_pts = [
        (x + HORSE_W - 34, y - body_h + 6),
        neck_top,
        (x + HORSE_W - 4, y - body_h + 2),
    ]
    border_pts = [(px + (6 if px > x + HORSE_W - 20 else -3), py - 3) for px, py in neck_pts]
    pygame.draw.polygon(surface, CUTOUT_BORDER, border_pts)
    pygame.draw.polygon(surface, light, neck_pts)

    head_center = (int(x + HORSE_W - 6), int(y - body_h - 16))
    pygame.draw.circle(surface, CUTOUT_BORDER, head_center, 14)
    pygame.draw.circle(surface, light, head_center, 11)
    pygame.draw.circle(surface, dark, (head_center[0] + 3, head_center[1] + 3), 5)
    pygame.draw.circle(surface, (30, 20, 15), (head_center[0] + 4, head_center[1] - 2), 2)

    pygame.draw.polygon(
        surface,
        shade(color, 0.5),
        [
            (x + HORSE_W - 12, y - body_h - 24),
            (x + HORSE_W - 4, y - body_h - 30),
            (x + HORSE_W - 2, y - body_h - 18),
        ],
    )

    tail_base = (x + 2, y - body_h + 8)
    sway = math.sin(leg_phase) * 6
    tail_tip = (tail_base[0] - 16, tail_base[1] + 18 + sway)
    pygame.draw.line(surface, CUTOUT_BORDER, tail_base, tail_tip, 8)
    pygame.draw.line(surface, shade(color, 0.45), tail_base, tail_tip, 5)

    offsets = [0, math.pi * 0.5, math.pi, math.pi * 1.5]
    leg_x_positions = [x + 6, x + 24, x + HORSE_W - 42, x + HORSE_W - 24]
    leg_h = 20
    for lx, off in zip(leg_x_positions, offsets):
        swing = math.sin(leg_phase + off) * 10
        ly = y - 10
        pygame.draw.line(surface, shade(color, 0.4), (lx, ly), (lx + swing * 0.3, ly + leg_h), 7)
        pygame.draw.line(surface, (40, 28, 16), (lx, ly), (lx + swing * 0.3, ly + leg_h), 4)

    return pygame.Rect(int(x), int(y - body_h - 16), HORSE_W - 4, body_h + 16)


class Player:
    def __init__(self):
        self.x = PLAYER_X
        self.y = GROUND_Y
        self.vel_y = 0
        self.on_ground = True
        self.leg_phase = 0
        self.alive = True
        self.distance = 0.0

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_VELOCITY
            self.on_ground = False

    def update(self, speed):
        if self.on_ground:
            self.leg_phase += 0.35 + speed * 0.03
        else:
            self.vel_y += GRAVITY
            self.y += self.vel_y
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.vel_y = 0
                self.on_ground = True
        self.distance += speed * 0.12

    def rect(self):
        body_h = HORSE_H
        return pygame.Rect(int(self.x) + 4, int(self.y - body_h - 14), HORSE_W - 14, body_h + 12)

    def draw(self, surface):
        draw_horse(surface, self.x, self.y, (150, 100, 55), self.leg_phase)


class Obstacle:
    KINDS = ["barrel", "cone", "puddle"]
    PAD = 6

    def __init__(self, x):
        self.kind = random.choice(self.KINDS)
        self.x = x
        if self.kind == "barrel":
            self.w, self.h = 32, 40
        elif self.kind == "cone":
            self.w, self.h = 24, 34
        else:
            self.w, self.h = 60, 10
        self.sprite = self._build_sprite()

    def _build_sprite(self):
        pad = self.PAD
        sprite = pygame.Surface((self.w + pad * 2, self.h + pad * 2), pygame.SRCALPHA)
        local = pygame.Rect(pad, pad, self.w, self.h)

        if self.kind == "barrel":
            pygame.draw.rect(sprite, CUTOUT_BORDER, local.inflate(6, 6), border_radius=8)
            grad = vertical_gradient((local.width, local.height), shade((150, 90, 40), 1.3), shade((150, 90, 40), 0.6))
            sprite.blit(grad, local.topleft)
            pygame.draw.rect(sprite, (90, 55, 22), local, width=2, border_radius=8)
            pygame.draw.line(sprite, (90, 55, 22), (local.left, local.centery), (local.right, local.centery), 3)
        elif self.kind == "cone":
            border_pts = [
                (local.centerx, local.top - 4),
                (local.left - 4, local.bottom + 2),
                (local.right + 4, local.bottom + 2),
            ]
            pygame.draw.polygon(sprite, CUTOUT_BORDER, border_pts)
            base_pts = [(local.centerx, local.top), (local.left, local.bottom), (local.right, local.bottom)]
            pygame.draw.polygon(sprite, shade((230, 110, 30), 0.7), base_pts)
            highlight_pts = [
                (local.centerx, local.top),
                (local.left + 6, local.bottom - 10),
                (local.right - 6, local.bottom - 10),
            ]
            pygame.draw.polygon(sprite, shade((230, 110, 30), 1.25), highlight_pts)
            pygame.draw.rect(sprite, WHITE, (local.left, local.bottom - 8, local.width, 5))
        else:
            pygame.draw.ellipse(sprite, CUTOUT_BORDER, local.inflate(6, 4))
            grad = vertical_gradient((local.width, local.height), shade((120, 170, 220), 1.15), shade((55, 95, 145), 0.85))
            grad = clip_to_ellipse(grad)
            sprite.blit(grad, local.topleft)
            pygame.draw.ellipse(sprite, (255, 255, 255, 110), (local.left + 4, local.top + 1, local.width // 3, 4))

        return sprite

    def update(self, speed):
        self.x -= speed

    def offscreen(self):
        return self.x < -80

    def rect(self):
        if self.kind == "puddle":
            return pygame.Rect(int(self.x), GROUND_Y - self.h + 4, self.w, self.h)
        return pygame.Rect(int(self.x), GROUND_Y - self.h, self.w, self.h)

    def draw(self, surface):
        r = self.rect()
        surface.blit(self.sprite, (r.x - self.PAD, r.y - self.PAD))


class Coin:
    _sprite = None
    RADIUS = 10

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.radius = self.RADIUS
        if Coin._sprite is None:
            Coin._sprite = self._build_sprite()

    @classmethod
    def _build_sprite(cls):
        r = cls.RADIUS
        pad = 4
        size = r * 2 + pad * 2
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(sprite, CUTOUT_BORDER, center, r + 3)
        grad = vertical_gradient((r * 2, r * 2), shade((255, 225, 110), 1.1), shade((200, 140, 20), 0.9))
        grad = clip_to_ellipse(grad)
        sprite.blit(grad, (center[0] - r, center[1] - r))
        pygame.draw.circle(sprite, (150, 100, 10), center, r, 2)
        pygame.draw.circle(sprite, (255, 255, 255, 160), (center[0] - 3, center[1] - 3), 2)
        return sprite

    def update(self, speed):
        self.x -= speed

    def offscreen(self):
        return self.x < -30

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

    def draw(self, surface, t):
        bob = math.sin(t * 0.15 + self.x * 0.05) * 4
        sprite = Coin._sprite
        surface.blit(sprite, (int(self.x - sprite.get_width() / 2), int(self.y + bob - sprite.get_height() / 2)))


class Building:
    PAD = 8

    def __init__(self, x, w, h, color, layer):
        self.x = x
        self.w = w
        self.h = h
        self.color = color
        self.layer = layer
        self.sprite = self._build_sprite()

    def _build_sprite(self):
        pad = self.PAD
        body_h = self.h + 80
        sprite = pygame.Surface((self.w + pad * 2, body_h + pad * 2), pygame.SRCALPHA)
        body_rect = pygame.Rect(pad, pad, self.w, body_h)

        pygame.draw.rect(sprite, CUTOUT_BORDER, body_rect.inflate(6, 6), border_radius=4)
        light = shade(self.color, 1.25)
        dark = shade(self.color, 0.7)
        grad = vertical_gradient((body_rect.width, body_rect.height), light, dark)
        sprite.blit(grad, body_rect.topleft)

        win_lit = (255, 232, 150)
        win_dark = shade(self.color, 0.5)
        rng = random.Random(int(self.x * 13 + self.w * 7 + self.h))
        for wy in range(body_rect.top + 10, body_rect.bottom - 10, 18):
            for wx in range(body_rect.left + 6, body_rect.right - 6, 14):
                lit = rng.random() < 0.4
                pygame.draw.rect(sprite, win_lit if lit else win_dark, (wx, wy, 6, 8))

        return sprite

    def update(self, speed):
        self.x -= speed * self.layer

    def draw(self, surface):
        top = GROUND_Y - 60 - self.h
        surface.blit(self.sprite, (self.x - self.PAD, top - self.PAD))


class Cloud:
    def __init__(self, x, y, scale):
        self.x = x
        self.y = y
        self.scale = scale
        self.sprite = self._build_sprite()

    def _build_sprite(self):
        w, h = int(90 * self.scale), int(40 * self.scale)
        sprite = pygame.Surface((w, h), pygame.SRCALPHA)
        for cx, cy, r in [
            (w * 0.3, h * 0.6, h * 0.5),
            (w * 0.55, h * 0.4, h * 0.6),
            (w * 0.8, h * 0.6, h * 0.45),
        ]:
            pygame.draw.circle(sprite, (255, 255, 255, 150), (int(cx), int(cy)), int(r))
        return sprite

    def update(self, speed):
        self.x -= speed * 0.15

    def draw(self, surface):
        surface.blit(self.sprite, (self.x, self.y))


class Rival:
    def __init__(self, name, color, skill):
        self.name = name
        self.color = color
        self.skill = skill
        self.distance = 0.0

    def update(self, speed):
        variance = random.uniform(-1.2, 1.4)
        self.distance += (speed * self.skill + variance) * 0.12
        if self.distance < 0:
            self.distance = 0


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("City Gallop: Horse Race")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = load_korean_font(22)
        self.big_font = load_korean_font(46, bold=True)

        self.sky = vertical_gradient((WIDTH, HEIGHT), SKY_TOP, SKY_HORIZON)
        self.ground_grad = vertical_gradient((WIDTH, 60), shade(GROUND_DIRT, 1.15), shade(GROUND_DIRT, 0.75))
        self.road_grad = vertical_gradient((WIDTH, HEIGHT - GROUND_Y), shade(ROAD, 1.3), shade(ROAD, 0.65))
        self.grain_overlay = make_grain_overlay(WIDTH, HEIGHT)
        self.vignette_overlay = make_vignette(WIDTH, HEIGHT)

        self.reset()

    def reset(self):
        self.player = Player()
        self.obstacles = []
        self.coins = []
        self.buildings = []
        self.clouds = [
            Cloud(random.uniform(0, WIDTH), random.uniform(20, 140), random.uniform(0.7, 1.3)) for _ in range(4)
        ]
        self.rivals = [
            Rival("적토마", RIVAL_COLORS[0], 0.97),
            Rival("백마", RIVAL_COLORS[1], 1.0),
            Rival("흑마", RIVAL_COLORS[2], 1.03),
        ]
        self.speed = BASE_SPEED
        self.spawn_timer = 100
        self.coin_timer = 40
        self.time_elapsed = 0
        self.state = "START"
        self.score_coins = 0
        self.result_rank = None
        self.road_scroll = 0

        x = 0
        while x < WIDTH + 200:
            b = self.make_building(x)
            self.buildings.append(b)
            x += b.w + random.randint(10, 40)

    def make_building(self, x):
        h = random.randint(60, 200)
        w = random.randint(60, 120)
        layer = random.choice([0.3, 0.5])
        color = random.choice(BUILDING_COLORS)
        return Building(x, w, h, color, layer)

    def spawn_obstacle(self):
        self.obstacles.append(Obstacle(WIDTH + 40))

    def spawn_coin(self):
        y = GROUND_Y - random.choice([30, 70, 110])
        self.coins.append(Coin(WIDTH + 40, y))

    def handle_start(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.state = "PLAYING"

    def handle_playing_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP):
            self.player.jump()

    def handle_gameover_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.reset()

    def update_playing(self):
        self.time_elapsed += 1
        self.speed = min(MAX_SPEED, BASE_SPEED + self.time_elapsed * SPEED_RAMP)
        self.road_scroll = (self.road_scroll - self.speed) % 40

        self.player.update(self.speed)

        for cl in self.clouds:
            cl.update(self.speed)
            if cl.x + cl.sprite.get_width() < -20:
                cl.x = WIDTH + random.uniform(0, 100)
                cl.y = random.uniform(20, 140)

        for b in self.buildings:
            b.update(self.speed)
        self.buildings = [b for b in self.buildings if b.x + b.w > -20]
        if not self.buildings or self.buildings[-1].x + self.buildings[-1].w < WIDTH:
            last_x = self.buildings[-1].x + self.buildings[-1].w if self.buildings else WIDTH
            self.buildings.append(self.make_building(last_x + random.randint(10, 40)))

        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            self.spawn_timer = max(70, int(140 - self.speed * 5)) + random.randint(0, 25)

        self.coin_timer -= 1
        if self.coin_timer <= 0:
            self.spawn_coin()
            self.coin_timer = random.randint(50, 100)

        for o in self.obstacles:
            o.update(self.speed)
        self.obstacles = [o for o in self.obstacles if not o.offscreen()]

        for c in self.coins:
            c.update(self.speed)
        self.coins = [c for c in self.coins if not c.offscreen() and not c.collected]

        for rv in self.rivals:
            rv.update(self.speed)

        player_rect = self.player.rect()
        for o in self.obstacles:
            if player_rect.colliderect(o.rect()):
                self.trigger_gameover()
                return

        for c in self.coins:
            if not c.collected and player_rect.colliderect(c.rect()):
                c.collected = True
                self.score_coins += 1

        if self.player.distance >= FINISH_DISTANCE:
            self.trigger_finish()

    def trigger_gameover(self):
        self.state = "GAMEOVER"
        self.result_rank = self.compute_rank()

    def trigger_finish(self):
        self.state = "FINISH"
        self.result_rank = self.compute_rank()

    def compute_rank(self):
        ahead = sum(1 for rv in self.rivals if rv.distance > self.player.distance)
        return ahead + 1

    def apply_post_process(self):
        self.screen.blit(self.grain_overlay, (0, 0))
        self.screen.blit(self.vignette_overlay, (0, 0))

    def draw_background(self):
        self.screen.blit(self.sky, (0, 0))
        for cl in self.clouds:
            cl.draw(self.screen)
        for b in self.buildings:
            b.draw(self.screen)

        self.screen.blit(self.ground_grad, (0, GROUND_Y - 60))
        self.screen.blit(self.road_grad, (0, GROUND_Y))
        for i in range(-1, WIDTH // 40 + 2):
            lx = i * 40 + self.road_scroll
            pygame.draw.rect(self.screen, ROAD_LINE, (lx, GROUND_Y + 25, 22, 5))

    def draw_hud(self):
        bar_x, bar_y, bar_w, bar_h = 20, 14, WIDTH - 40, 96
        s = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 130), (0, 0, bar_w, bar_h), border_radius=8)
        self.screen.blit(s, (bar_x, bar_y))

        entries = [("나", self.player.distance, (150, 100, 55))]
        for rv in self.rivals:
            entries.append((rv.name, rv.distance, rv.color))

        row_h = bar_h // len(entries)
        for i, (name, dist, color) in enumerate(entries):
            y = bar_y + row_h // 2 + i * row_h
            pygame.draw.circle(self.screen, color, (bar_x + 12, y), 5)
            track_x = bar_x + 30
            track_w = bar_w - 120
            pygame.draw.rect(self.screen, (255, 255, 255), (track_x, y - 3, track_w, 6), 1)
            fill = min(1.0, dist / FINISH_DISTANCE) * track_w
            pygame.draw.rect(self.screen, color, (track_x, y - 3, max(2, fill), 6))
            label = self.font.render(name, True, WHITE)
            label_rect = label.get_rect(midleft=(track_x + track_w + 10, y))
            self.screen.blit(label, label_rect)

        dist_text = self.font.render(
            f"거리: {int(self.player.distance)} / {FINISH_DISTANCE} m   코인: {self.score_coins}", True, BLACK
        )
        self.screen.blit(dist_text, (20, HEIGHT - 30))

    def draw_playing(self):
        self.draw_background()
        for o in self.obstacles:
            o.draw(self.screen)
        for c in self.coins:
            c.draw(self.screen, self.time_elapsed)
        self.player.draw(self.screen)
        self.draw_hud()
        self.apply_post_process()

    def draw_center_text(self, lines, y_start=170):
        y = y_start
        for i, (text, font, color) in enumerate(lines):
            surf = font.render(text, True, color)
            rect = surf.get_rect(center=(WIDTH // 2, y))
            self.screen.blit(surf, rect)
            y += rect.height + 12

    def draw_start(self):
        self.draw_background()
        draw_horse(self.screen, PLAYER_X, GROUND_Y, (150, 100, 55), pygame.time.get_ticks() * 0.01)
        self.draw_center_text(
            [
                ("City Gallop: Horse Race", self.big_font, DARK),
                ("도시를 질주하는 말 경주 게임", self.font, DARK),
                ("SPACE / ENTER 로 시작 - SPACE 또는 위쪽 화살표로 점프", self.font, DARK),
            ],
            y_start=130,
        )
        self.apply_post_process()

    def draw_gameover(self):
        self.draw_playing()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        self.draw_center_text(
            [
                ("충돌! 경주 실패", self.big_font, (255, 90, 90)),
                (f"이동 거리: {int(self.player.distance)} m", self.font, WHITE),
                (f"현재 순위: {self.result_rank}위 / 4", self.font, WHITE),
                ("R 키를 눌러 다시 시작 - ESC 로 종료", self.font, WHITE),
            ]
        )

    def draw_finish(self):
        self.draw_playing()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        rank_text = {1: "1위! 우승!", 2: "2위", 3: "3위", 4: "4위"}[self.result_rank]
        self.draw_center_text(
            [
                ("결승선 통과!", self.big_font, (255, 215, 0)),
                (rank_text, self.font, WHITE),
                (f"완주 시간: {self.time_elapsed // FPS}초   코인: {self.score_coins}개", self.font, WHITE),
                ("R 키를 눌러 다시 시작 - ESC 로 종료", self.font, WHITE),
            ]
        )

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif self.state == "START":
                    self.handle_start(event)
                elif self.state == "PLAYING":
                    self.handle_playing_event(event)
                elif self.state in ("GAMEOVER", "FINISH"):
                    self.handle_gameover_event(event)

            if self.state == "PLAYING":
                self.update_playing()

            if self.state == "START":
                self.draw_start()
            elif self.state == "PLAYING":
                self.draw_playing()
            elif self.state == "GAMEOVER":
                self.draw_gameover()
            elif self.state == "FINISH":
                self.draw_finish()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
