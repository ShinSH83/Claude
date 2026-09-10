import math
import random
import sys

import pygame

import audio

WIDTH, HEIGHT = 900, 500
FPS = 60

GROUND_Y = 380
GRAVITY = 0.9
JUMP_VELOCITY = -15.5

BASE_SPEED = 6.0
MAX_SPEED = 13.0
SPEED_RAMP = 0.0011

FINISH_DISTANCE = 2200

PIXEL_SCALE = 4

SKY_TOP = (120, 195, 245)
SKY_HORIZON = (255, 222, 190)
ROAD = (120, 96, 70)
ROAD_LINE = (255, 255, 255)
GROUND_GRASS = (108, 180, 78)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK = (30, 30, 40)

OUTLINE = (35, 26, 24)
OUTLINE_W = 4

PLAYER_COAT = (216, 144, 82)
PLAYER_MANE = (58, 40, 30)
PLAYER_JOCKEY = ((225, 55, 55), (250, 205, 40))

SKYLINE_COLORS = [
    (150, 160, 188),
    (132, 144, 172),
    (168, 158, 150),
    (145, 150, 178),
]

RIVAL_COLORS = [(90, 110, 235), (235, 90, 90), (90, 195, 120)]
RIVAL_COATS = [(150, 72, 46), (232, 228, 218), (58, 48, 44)]
RIVAL_MANES = [(62, 32, 20), (198, 192, 180), (24, 20, 18)]
RIVAL_HELMETS = [(255, 225, 70), (240, 245, 250), (230, 60, 60)]
RIVAL_LANE_OFFSETS = [-12, -26, -40]
RIVAL_DEPTH_SHEAR = 3.0
RIVAL_X_SCALE = 0.8
RIVAL_X_MAX_OFFSET = 200

PLAYER_X = 140
HORSE_W, HORSE_H = 78, 52

FLOOR_TILT = 40


def seam_y(x):
    return GROUND_Y - FLOOR_TILT + FLOOR_TILT * (x / WIDTH)

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


def pixelate(surface):
    w, h = surface.get_size()
    sw, sh = max(1, w // PIXEL_SCALE), max(1, h // PIXEL_SCALE)
    small = pygame.transform.scale(surface, (sw, sh))
    return pygame.transform.scale(small, (w, h))


def draw_tilted_gradient(surface, top_fn, bottom_fn, color_top, color_bottom, bands=8):
    for i in range(bands):
        t0, t1 = i / bands, (i + 1) / bands
        c = tuple(int(color_top[k] + (color_bottom[k] - color_top[k]) * (t0 + t1) / 2) for k in range(3))
        y0l = top_fn(0) + (bottom_fn(0) - top_fn(0)) * t0
        y0r = top_fn(WIDTH) + (bottom_fn(WIDTH) - top_fn(WIDTH)) * t0
        y1l = top_fn(0) + (bottom_fn(0) - top_fn(0)) * t1
        y1r = top_fn(WIDTH) + (bottom_fn(WIDTH) - top_fn(WIDTH)) * t1
        pygame.draw.polygon(surface, c, [(0, y0l), (WIDTH, y0r), (WIDTH, y1r), (0, y1l)])


def vertical_gradient(size, top_color, bottom_color):
    w, h = max(1, int(size[0])), max(1, int(size[1]))
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        t = y / max(1, h - 1)
        color = tuple(int(top_color[i] + (bottom_color[i] - top_color[i]) * t) for i in range(3)) + (255,)
        pygame.draw.line(surf, color, (0, y), (w, y))
    return surf


def draw_outlined_rect(surface, color, rect, border_radius=0):
    pygame.draw.rect(surface, OUTLINE, rect.inflate(OUTLINE_W * 2, OUTLINE_W * 2), border_radius=border_radius + OUTLINE_W)
    pygame.draw.rect(surface, color, rect, border_radius=border_radius)


def draw_outlined_ellipse(surface, color, rect):
    pygame.draw.ellipse(surface, OUTLINE, rect.inflate(OUTLINE_W * 2, OUTLINE_W * 2))
    pygame.draw.ellipse(surface, color, rect)


def draw_outlined_circle(surface, color, center, radius):
    pygame.draw.circle(surface, OUTLINE, center, radius + OUTLINE_W)
    pygame.draw.circle(surface, color, center, radius)


def draw_outlined_polygon(surface, color, points):
    cx = sum(p[0] for p in points) / len(points)
    cy = sum(p[1] for p in points) / len(points)
    big = []
    for px, py in points:
        dx, dy = px - cx, py - cy
        dist = math.hypot(dx, dy) or 1
        big.append((px + dx / dist * OUTLINE_W * 1.8, py + dy / dist * OUTLINE_W * 1.8))
    pygame.draw.polygon(surface, OUTLINE, big)
    pygame.draw.polygon(surface, color, points)


def draw_outlined_line(surface, color, p1, p2, width):
    pygame.draw.line(surface, OUTLINE, p1, p2, width + OUTLINE_W * 2)
    pygame.draw.line(surface, color, p1, p2, width)


def cel_shine_ellipse(surface, rect, color, scale=0.45):
    w, h = rect.width, rect.height
    shine_rect = pygame.Rect(0, 0, max(2, int(w * scale)), max(2, int(h * 0.32)))
    shine_rect.topleft = (int(rect.left + w * 0.14), int(rect.top + h * 0.12))
    pygame.draw.ellipse(surface, color, shine_rect)


def draw_jockey(surface, x, y, body_h, helmet_color, jersey_color):
    seat = (x + HORSE_W - 42, y - body_h - 8)

    draw_outlined_line(surface, (55, 45, 60), (seat[0] - 1, seat[1] - 2), (seat[0] - 9, y - body_h + 8), 5)
    draw_outlined_line(surface, jersey_color, (seat[0] - 1, seat[1] - 14), (x + HORSE_W - 16, y - body_h - 12), 4)

    torso_rect = pygame.Rect(int(seat[0] - 7), int(seat[1] - 22), 14, 20)
    draw_outlined_rect(surface, jersey_color, torso_rect, border_radius=3)

    head_c = (int(seat[0]), int(seat[1] - 27))
    draw_outlined_circle(surface, (235, 195, 160), head_c, 6)
    helmet_rect = pygame.Rect(head_c[0] - 7, head_c[1] - 9, 14, 8)
    draw_outlined_ellipse(surface, helmet_color, helmet_rect)


def draw_horse(surface, x, y, coat, mane, leg_phase, ducking=False, moving=False, jockey_colors=None, ground_ref_y=None):
    if ground_ref_y is None:
        ground_ref_y = GROUND_Y
    body_h = HORSE_H - 14 if ducking else HORSE_H
    body_w = HORSE_W - 18

    pygame.draw.ellipse(surface, shade(ROAD, 0.55), (int(x) - 2, ground_ref_y - 6, HORSE_W, 10))

    if moving:
        for i, dx in enumerate((16, 28, 40)):
            ly = y - body_h + 6 + i * 9
            pygame.draw.line(surface, WHITE, (x - dx, ly), (x - dx - 14, ly), 2)

    body_rect = pygame.Rect(int(x), int(y - body_h), body_w, body_h - 10)
    draw_outlined_ellipse(surface, coat, body_rect)
    cel_shine_ellipse(surface, body_rect, shade(coat, 1.3))

    blanket_rect = pygame.Rect(int(x + body_w * 0.28), int(y - body_h + 1), 20, 15)
    draw_outlined_rect(surface, jockey_colors[1] if jockey_colors else shade(coat, 0.55), blanket_rect, border_radius=2)

    neck_top = (x + HORSE_W - 30, y - body_h - 18)
    neck_pts = [
        (x + HORSE_W - 34, y - body_h + 6),
        neck_top,
        (x + HORSE_W - 4, y - body_h + 2),
    ]
    draw_outlined_polygon(surface, coat, neck_pts)

    for t in (0.2, 0.5, 0.8):
        px = neck_pts[0][0] + (neck_pts[1][0] - neck_pts[0][0]) * t
        py = neck_pts[0][1] + (neck_pts[1][1] - neck_pts[0][1]) * t
        draw_outlined_line(surface, mane, (px, py - 2), (px - 7, py + 10), 5)

    head_center = (int(x + HORSE_W - 6), int(y - body_h - 16))
    draw_outlined_circle(surface, coat, head_center, 13)
    pygame.draw.circle(surface, shade(coat, 0.75), (head_center[0] + 6, head_center[1] + 6), 6)
    pygame.draw.circle(surface, OUTLINE, (head_center[0] + 6, head_center[1] + 6), 6, 1)

    eye_c = (head_center[0] + 2, head_center[1] - 3)
    pygame.draw.circle(surface, OUTLINE, eye_c, 3)
    pygame.draw.circle(surface, WHITE, (eye_c[0] - 1, eye_c[1] - 1), 1)

    pygame.draw.polygon(
        surface,
        OUTLINE,
        [
            (x + HORSE_W - 12, y - body_h - 26),
            (x + HORSE_W - 3, y - body_h - 32),
            (x + HORSE_W - 1, y - body_h - 19),
        ],
    )
    pygame.draw.polygon(
        surface,
        mane,
        [
            (x + HORSE_W - 11, y - body_h - 24),
            (x + HORSE_W - 4, y - body_h - 29),
            (x + HORSE_W - 2, y - body_h - 19),
        ],
    )

    tail_base = (x + 2, y - body_h + 8)
    sway = math.sin(leg_phase) * 6
    tail_tip = (tail_base[0] - 18, tail_base[1] + 20 + sway)
    draw_outlined_line(surface, mane, tail_base, tail_tip, 7)

    offsets = [0, math.pi * 0.5, math.pi, math.pi * 1.5]
    leg_x_positions = [x + 6, x + 24, x + HORSE_W - 42, x + HORSE_W - 24]
    leg_h = 20
    for lx, off in zip(leg_x_positions, offsets):
        swing = math.sin(leg_phase + off) * 10
        ly = y - 10
        foot = (lx + swing * 0.3, ly + leg_h)
        draw_outlined_line(surface, mane, (lx, ly), foot, 6)
        pygame.draw.circle(surface, (250, 250, 245), foot, 3)
        pygame.draw.circle(surface, OUTLINE, foot, 3, 1)

    if jockey_colors:
        draw_jockey(surface, x, y, body_h, jockey_colors[0], jockey_colors[1])

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
        draw_horse(
            surface, self.x, self.y, PLAYER_COAT, PLAYER_MANE, self.leg_phase, moving=self.on_ground, jockey_colors=PLAYER_JOCKEY
        )


class Obstacle:
    KINDS = ["barrel", "cone", "puddle"]
    PAD = 8

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
            draw_outlined_rect(sprite, (222, 104, 52), local, border_radius=6)
            pygame.draw.rect(sprite, OUTLINE, (local.left, local.centery - 2, local.width, 4))
            cel_shine_ellipse(sprite, local, (255, 176, 130), scale=0.4)
        elif self.kind == "cone":
            pts = [(local.centerx, local.top), (local.left, local.bottom), (local.right, local.bottom)]
            draw_outlined_polygon(sprite, (255, 128, 40), pts)
            stripe = pygame.Rect(local.left + 3, local.bottom - 12, local.width - 6, 5)
            pygame.draw.rect(sprite, WHITE, stripe)
            pygame.draw.rect(sprite, OUTLINE, stripe, 1)
        else:
            draw_outlined_ellipse(sprite, (95, 205, 235), local)
            pygame.draw.ellipse(
                sprite, (210, 245, 255), (local.left + 6, local.top + 1, max(2, local.width * 0.4), max(2, local.height * 0.5))
            )

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
        pad = OUTLINE_W + 3
        size = r * 2 + pad * 2
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        draw_outlined_circle(sprite, (255, 214, 64), center, r)
        pygame.draw.circle(sprite, (255, 240, 150), (center[0] - 3, center[1] - 3), 3)
        sx, sy = center[0] + 5, center[1] - 6
        pygame.draw.line(sprite, WHITE, (sx - 3, sy), (sx + 3, sy), 2)
        pygame.draw.line(sprite, WHITE, (sx, sy - 3), (sx, sy + 3), 2)
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
    PAD = 6

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

        draw_outlined_rect(sprite, self.color, body_rect)

        win_lit = (250, 235, 190)
        rng = random.Random(int(self.x * 13 + self.w * 7 + self.h))
        for wy in range(body_rect.top + 14, body_rect.bottom - 10, 22):
            for wx in range(body_rect.left + 8, body_rect.right - 8, 18):
                if rng.random() < 0.22:
                    pygame.draw.rect(sprite, win_lit, (wx, wy, 6, 8))

        return sprite

    def update(self, speed):
        self.x -= speed * self.layer

    def draw(self, surface):
        top = GROUND_Y - 60 - self.h
        surface.blit(self.sprite, (self.x - self.PAD, top - self.PAD))


class Tree:
    def __init__(self, x, kind, scale):
        self.x = x
        self.kind = kind
        self.scale = scale
        self.sprite = self._build_sprite()

    def _build_sprite(self):
        if self.kind == "pine":
            w, h = int(44 * self.scale), int(94 * self.scale)
            pad = 6
            surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
            trunk = pygame.Rect(pad + w // 2 - 4, pad + h - 16, 8, 16)
            draw_outlined_rect(surf, (112, 80, 52), trunk)
            layers = 4
            base_green = (42, 118, 64)
            for i in range(layers):
                seg_h = (h - 18) // layers
                top_y = pad + i * seg_h * 0.72
                lw = w - i * (w // (layers + 2))
                cx = pad + w // 2
                pts = [(cx, top_y), (cx - lw // 2, top_y + seg_h), (cx + lw // 2, top_y + seg_h)]
                draw_outlined_polygon(surf, shade(base_green, 1.0 + 0.1 * i), pts)
            return surf

        w, h = int(66 * self.scale), int(64 * self.scale)
        pad = 6
        surf = pygame.Surface((w + pad * 2, h + 28 + pad * 2), pygame.SRCALPHA)
        trunk = pygame.Rect(pad + w // 2 - 4, pad + h - 4, 8, 26)
        draw_outlined_rect(surf, (112, 80, 52), trunk)
        blobs = [
            (w * 0.3, h * 0.48, h * 0.32),
            (w * 0.55, h * 0.28, h * 0.38),
            (w * 0.78, h * 0.5, h * 0.28),
            (w * 0.52, h * 0.62, h * 0.36),
        ]
        for bx, by, br in blobs:
            rect = pygame.Rect(int(pad + bx - br), int(pad + by - br), int(br * 2), int(br * 2))
            draw_outlined_ellipse(surf, (66, 158, 76), rect)
        rng = random.Random(int(self.x * 11 + 7))
        for _ in range(16):
            bx, by, br = blobs[rng.randrange(len(blobs))]
            dx = pad + bx + rng.uniform(-br * 0.6, br * 0.6)
            dy = pad + by + rng.uniform(-br * 0.6, br * 0.6)
            col = (92, 182, 96) if rng.random() < 0.5 else (48, 128, 58)
            pygame.draw.circle(surf, col, (int(dx), int(dy)), 3)
        return surf

    def update(self, speed):
        self.x -= speed * 0.55

    def draw(self, surface):
        surface.blit(self.sprite, (self.x, GROUND_Y - 55 - self.sprite.get_height()))


class Mountains:
    def __init__(self):
        self.sprite = self._build()

    def _build(self):
        h = 90
        w = WIDTH + 60
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        rng = random.Random(4242)
        pts = [(0, h)]
        x = 0
        peaks = []
        while x < w:
            x += rng.randint(70, 120)
            peak_h = rng.randint(28, h - 12)
            peaks.append((x, h - peak_h))
            pts.append((x, h - peak_h))
        pts.append((w, h))
        pygame.draw.polygon(surf, (150, 163, 196), pts)
        for px, py in peaks:
            pygame.draw.polygon(surf, (220, 226, 238), [(px - 9, py + 13), (px, py), (px + 9, py + 13)])
        return surf

    def draw(self, surface):
        surface.blit(self.sprite, (-30, GROUND_Y - 150))


def draw_fence(surface, scroll):
    post_w, gap = 6, 34
    for i in range(-1, WIDTH // gap + 2):
        px = i * gap + scroll
        base_y = seam_y(px)
        post = pygame.Rect(int(px), int(base_y - 24), post_w, 26)
        draw_outlined_rect(surface, (150, 120, 80), post)
    for off in (-20, -8):
        y0, y1 = seam_y(0) + off, seam_y(WIDTH) + off
        pts = [(0, y0), (WIDTH, y1), (WIDTH, y1 + 5), (0, y0 + 5)]
        pygame.draw.polygon(surface, (238, 232, 216), pts)
        pygame.draw.polygon(surface, OUTLINE, pts, 1)


class Cloud:
    def __init__(self, x, y, scale):
        self.x = x
        self.y = y
        self.scale = scale
        self.sprite = self._build_sprite()

    def _build_sprite(self):
        w, h = int(90 * self.scale), int(40 * self.scale)
        sprite = pygame.Surface((w, h + 10), pygame.SRCALPHA)
        circles = [
            (w * 0.28, h * 0.65, h * 0.5),
            (w * 0.52, h * 0.42, h * 0.6),
            (w * 0.78, h * 0.62, h * 0.45),
        ]
        for cx, cy, r in circles:
            pygame.draw.circle(sprite, OUTLINE, (int(cx), int(cy)), int(r) + OUTLINE_W)
        for cx, cy, r in circles:
            pygame.draw.circle(sprite, WHITE, (int(cx), int(cy)), int(r))
        return sprite

    def update(self, speed):
        self.x -= speed * 0.1

    def draw(self, surface):
        surface.blit(self.sprite, (self.x, self.y))


class Rival:
    def __init__(self, name, jersey_color, coat, mane, helmet, skill, lane_offset, phase_offset):
        self.name = name
        self.color = jersey_color
        self.coat = coat
        self.mane = mane
        self.helmet = helmet
        self.skill = skill
        self.distance = 0.0
        self.lane_offset = lane_offset
        self.leg_phase = phase_offset

    def update(self, speed):
        variance = random.uniform(-1.2, 1.4)
        self.distance += (speed * self.skill + variance) * 0.12
        if self.distance < 0:
            self.distance = 0
        self.leg_phase += 0.32 + speed * 0.028

    def screen_x(self, player_distance):
        pace_offset = (self.distance - player_distance) * RIVAL_X_SCALE
        pace_offset = max(-RIVAL_X_MAX_OFFSET, min(RIVAL_X_MAX_OFFSET, pace_offset))
        depth_shift = self.lane_offset * RIVAL_DEPTH_SHEAR
        return PLAYER_X + depth_shift + pace_offset

    def draw(self, surface, player_distance):
        x = self.screen_x(player_distance)
        y = GROUND_Y + self.lane_offset
        draw_horse(
            surface,
            x,
            y,
            self.coat,
            self.mane,
            self.leg_phase,
            moving=True,
            jockey_colors=(self.helmet, self.color),
            ground_ref_y=y,
        )


class Game:
    def __init__(self):
        self.sound = audio.SoundBank()
        pygame.init()
        self.sound.init()
        pygame.display.set_caption("City Gallop: Horse Race")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = load_korean_font(22)
        self.big_font = load_korean_font(46, bold=True)

        self.sky = vertical_gradient((WIDTH, HEIGHT), SKY_TOP, SKY_HORIZON)
        self.ground_surface = self._build_ground_surface()
        self.mountains = Mountains()

        self.reset()

    def _build_ground_surface(self):
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        draw_tilted_gradient(
            surf, lambda x: GROUND_Y - 60, seam_y, shade(GROUND_GRASS, 1.15), shade(GROUND_GRASS, 0.8)
        )
        draw_tilted_gradient(
            surf, seam_y, lambda x: HEIGHT, shade(ROAD, 1.25), shade(ROAD, 0.6)
        )
        return surf

    def reset(self):
        self.player = Player()
        self.obstacles = []
        self.coins = []
        self.buildings = []
        self.trees = []
        self.clouds = [
            Cloud(random.uniform(0, WIDTH), random.uniform(20, 130), random.uniform(0.7, 1.3)) for _ in range(4)
        ]
        self.rivals = [
            Rival(
                "적토마", RIVAL_COLORS[0], RIVAL_COATS[0], RIVAL_MANES[0], RIVAL_HELMETS[0],
                0.97, RIVAL_LANE_OFFSETS[0], 0.0,
            ),
            Rival(
                "백마", RIVAL_COLORS[1], RIVAL_COATS[1], RIVAL_MANES[1], RIVAL_HELMETS[1],
                1.0, RIVAL_LANE_OFFSETS[1], 1.4,
            ),
            Rival(
                "흑마", RIVAL_COLORS[2], RIVAL_COATS[2], RIVAL_MANES[2], RIVAL_HELMETS[2],
                1.03, RIVAL_LANE_OFFSETS[2], 2.6,
            ),
        ]
        self.speed = BASE_SPEED
        self.spawn_timer = 100
        self.coin_timer = 40
        self.time_elapsed = 0
        self.state = "START"
        self.score_coins = 0
        self.result_rank = None
        self.road_scroll = 0
        self.fence_scroll = 0

        x = 0
        while x < WIDTH + 220:
            b = self.make_building(x)
            self.buildings.append(b)
            x += b.w + random.randint(20, 60)

        x = 0
        while x < WIDTH + 200:
            t = self.make_tree(x)
            self.trees.append(t)
            x += t.sprite.get_width() + random.randint(20, 70)

    def make_building(self, x):
        h = random.randint(50, 140)
        w = random.randint(50, 100)
        layer = random.uniform(0.12, 0.2)
        color = random.choice(SKYLINE_COLORS)
        return Building(x, w, h, color, layer)

    def make_tree(self, x):
        kind = random.choice(["pine", "pine", "round"])
        scale = random.uniform(0.8, 1.35)
        return Tree(x, kind, scale)

    def spawn_obstacle(self):
        self.obstacles.append(Obstacle(WIDTH + 40))

    def spawn_coin(self):
        y = GROUND_Y - random.choice([30, 70, 110])
        self.coins.append(Coin(WIDTH + 40, y))

    def handle_start(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.state = "PLAYING"
            self.sound.play("select")

    def handle_playing_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP):
            if self.player.on_ground:
                self.player.jump()
                self.sound.play("jump")

    def handle_gameover_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.reset()
            self.sound.play("select")

    def update_playing(self):
        self.time_elapsed += 1
        self.speed = min(MAX_SPEED, BASE_SPEED + self.time_elapsed * SPEED_RAMP)
        self.road_scroll = (self.road_scroll - self.speed) % 40
        self.fence_scroll = (self.fence_scroll - self.speed) % 34

        prev_leg_phase = self.player.leg_phase
        was_on_ground = self.player.on_ground
        self.player.update(self.speed)
        if was_on_ground and self.player.on_ground:
            step_unit = math.pi / 2
            if int(self.player.leg_phase / step_unit) != int(prev_leg_phase / step_unit):
                self.sound.play("step", volume=0.5)

        for cl in self.clouds:
            cl.update(self.speed)
            if cl.x + cl.sprite.get_width() < -20:
                cl.x = WIDTH + random.uniform(0, 100)
                cl.y = random.uniform(20, 130)

        for b in self.buildings:
            b.update(self.speed)
        self.buildings = [b for b in self.buildings if b.x + b.w > -20]
        if not self.buildings or self.buildings[-1].x + self.buildings[-1].w < WIDTH:
            last_x = self.buildings[-1].x + self.buildings[-1].w if self.buildings else WIDTH
            self.buildings.append(self.make_building(last_x + random.randint(20, 60)))

        for t in self.trees:
            t.update(self.speed)
        self.trees = [t for t in self.trees if t.x + t.sprite.get_width() > -20]
        if not self.trees or self.trees[-1].x + self.trees[-1].sprite.get_width() < WIDTH:
            last_x = self.trees[-1].x + self.trees[-1].sprite.get_width() if self.trees else WIDTH
            self.trees.append(self.make_tree(last_x + random.randint(20, 70)))

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
                self.sound.play("coin")

        if self.player.distance >= FINISH_DISTANCE:
            self.trigger_finish()

    def trigger_gameover(self):
        self.state = "GAMEOVER"
        self.result_rank = self.compute_rank()
        self.sound.play("crash")

    def trigger_finish(self):
        self.state = "FINISH"
        self.result_rank = self.compute_rank()
        self.sound.play("finish")

    def compute_rank(self):
        ahead = sum(1 for rv in self.rivals if rv.distance > self.player.distance)
        return ahead + 1

    def draw_background(self):
        self.screen.blit(self.sky, (0, 0))
        self.mountains.draw(self.screen)
        for cl in self.clouds:
            cl.draw(self.screen)
        for b in self.buildings:
            b.draw(self.screen)
        for t in self.trees:
            t.draw(self.screen)

        self.screen.blit(self.ground_surface, (0, 0))
        for i in range(-1, WIDTH // 40 + 2):
            lx = i * 40 + self.road_scroll
            pygame.draw.rect(self.screen, ROAD_LINE, (lx, seam_y(lx) + 25, 22, 5))
        draw_fence(self.screen, self.fence_scroll)

    def draw_hud(self):
        bar_x, bar_y, bar_w, bar_h = 20, 14, WIDTH - 40, 96
        panel_rect = pygame.Rect(0, 0, bar_w, bar_h)
        s = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(s, (255, 255, 255, 225), panel_rect, border_radius=10)
        pygame.draw.rect(s, OUTLINE, panel_rect, width=3, border_radius=10)
        self.screen.blit(s, (bar_x, bar_y))

        entries = [("나", self.player.distance, PLAYER_COAT)]
        for rv in self.rivals:
            entries.append((rv.name, rv.distance, rv.color))

        row_h = bar_h // len(entries)
        for i, (name, dist, color) in enumerate(entries):
            y = bar_y + row_h // 2 + i * row_h
            pygame.draw.circle(self.screen, color, (bar_x + 12, y), 5)
            pygame.draw.circle(self.screen, OUTLINE, (bar_x + 12, y), 5, 1)
            track_x = bar_x + 30
            track_w = bar_w - 120
            pygame.draw.rect(self.screen, OUTLINE, (track_x, y - 3, track_w, 6), 1)
            fill = min(1.0, dist / FINISH_DISTANCE) * track_w
            pygame.draw.rect(self.screen, color, (track_x, y - 3, max(2, fill), 6))
            label = self.font.render(name, True, OUTLINE)
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
        for rv in reversed(self.rivals):
            rv.draw(self.screen, self.player.distance)
        self.player.draw(self.screen)
        self.screen.blit(pixelate(self.screen), (0, 0))
        self.draw_hud()

    def draw_center_text(self, lines, y_start=170):
        y = y_start
        for i, (text, font, color) in enumerate(lines):
            surf = font.render(text, True, color)
            rect = surf.get_rect(center=(WIDTH // 2, y))
            outline = font.render(text, True, WHITE)
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
                self.screen.blit(outline, rect.move(ox, oy))
            self.screen.blit(surf, rect)
            y += rect.height + 12

    def draw_start(self):
        self.draw_background()
        for rv in reversed(self.rivals):
            rv.draw(self.screen, self.player.distance)
        draw_horse(
            self.screen,
            PLAYER_X,
            GROUND_Y,
            PLAYER_COAT,
            PLAYER_MANE,
            pygame.time.get_ticks() * 0.01,
            moving=True,
            jockey_colors=PLAYER_JOCKEY,
        )
        self.screen.blit(pixelate(self.screen), (0, 0))
        self.draw_center_text(
            [
                ("City Gallop: Horse Race", self.big_font, DARK),
                ("도시를 질주하는 말 경주 게임", self.font, DARK),
                ("SPACE / ENTER 로 시작 - SPACE 또는 위쪽 화살표로 점프", self.font, DARK),
            ],
            y_start=130,
        )

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
