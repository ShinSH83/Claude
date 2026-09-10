import math
import random
import sys

import pygame

import audio

WIDTH, HEIGHT = 900, 500
FPS = 60

SKY_TOP = (120, 195, 245)
SKY_HORIZON = (255, 222, 190)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK = (30, 30, 40)
OUTLINE = (35, 26, 24)
OUTLINE_W = 4

# --- track geometry -----------------------------------------------------
SEGMENT_LENGTH = 200
HALF_ROAD_WIDTH = 800
MAX_X_CLAMP = HALF_ROAD_WIDTH * 1.6

NEAR_Z = 100
CAMERA_DEPTH = 60
ROAD_TOP_Y = 150
ROAD_BOTTOM_Y = HEIGHT
ROAD_ROWS = ROAD_BOTTOM_Y - ROAD_TOP_Y
MAX_VISIBLE_Z = NEAR_Z * ROAD_ROWS

ROAD_COLOR_A = (96, 92, 100)
ROAD_COLOR_B = (86, 82, 90)
RUMBLE_COLOR_A = (210, 60, 55)
RUMBLE_COLOR_B = (235, 235, 225)
GRASS_COLOR_A = (110, 185, 82)
GRASS_COLOR_B = (98, 170, 72)

TRACK_PLAN = [
    (20, 0.0),
    (14, 0.05),
    (10, 0.0),
    (16, -0.06),
    (10, 0.0),
    (10, 0.08),
    (18, 0.0),
    (10, -0.07),
]


def _expand_curves(plan):
    curves = []
    for count, curve in plan:
        curves.extend([curve] * count)
    return curves


def _build_offsets(curves):
    offsets = [0.0]
    for c in curves:
        offsets.append(offsets[-1] + c * SEGMENT_LENGTH)
    return offsets


TRACK_CURVES = _expand_curves(TRACK_PLAN)
NUM_SEGMENTS = len(TRACK_CURVES)
TRACK_LEN = NUM_SEGMENTS * SEGMENT_LENGTH
TRACK_OFFSETS = _build_offsets(TRACK_CURVES)

LAPS_TO_WIN = 3

# --- racer physics --------------------------------------------------------
PLAYER_MAX_SPEED = 9.5
PLAYER_ACCEL = 0.16
PLAYER_BRAKE = 0.32
PLAYER_FRICTION = 0.10
PLAYER_STEER_RATE = 9.0
OFFTRACK_PENALTY = 0.55
BOOST_MULT = 1.55
BOOST_DURATION = 120

JUMP_DURATION = 26
JUMP_HEIGHT_PX = 46

BUMP_Z_RANGE = 90
BUMP_X_RANGE = 130
BUMP_PUSH = 22
BUMP_SLOWDOWN = 0.85

ITEM_PICKUP_X = 140
ITEM_COUNT = 8

PLAYER_COAT = (216, 144, 82)
PLAYER_MANE = (58, 40, 30)
PLAYER_JOCKEY = ((225, 55, 55), (250, 205, 40))

AI_SPECS = [
    {"name": "적토마", "coat": (150, 72, 46), "mane": (62, 32, 20), "helmet": (255, 225, 70), "jersey": (90, 110, 235), "max_speed": 9.2},
    {"name": "백마", "coat": (232, 228, 218), "mane": (198, 192, 180), "helmet": (240, 245, 250), "jersey": (235, 90, 90), "max_speed": 9.6},
    {"name": "흑마", "coat": (58, 48, 44), "mane": (24, 20, 18), "helmet": (230, 60, 60), "jersey": (90, 195, 120), "max_speed": 9.9},
]

PLAYER_X = HALF_ROAD_WIDTH  # unused placeholder to keep naming close to old code (not used for screen pos anymore)

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


def draw_horse(surface, x, y, coat, mane, leg_phase, moving=False, jockey_colors=None, ground_ref_y=None):
    if ground_ref_y is None:
        ground_ref_y = y
    body_h = HORSE_H
    body_w = HORSE_W - 18

    pygame.draw.ellipse(surface, (70, 60, 40), (int(x) - 2, ground_ref_y - 6, HORSE_W, 10))

    if moving:
        for i, dx in enumerate((16, 28, 40)):
            ly = y - body_h + 6 + i * 9
            pygame.draw.line(surface, WHITE, (x - dx, ly), (x - dx - 14, ly), 2)

    light = shade(coat, 1.3)

    body_rect = pygame.Rect(int(x), int(y - body_h), body_w, body_h - 10)
    draw_outlined_ellipse(surface, coat, body_rect)
    cel_shine_ellipse(surface, body_rect, light)

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


HORSE_CANVAS_W, HORSE_CANVAS_H = 150, 190
HORSE_CANVAS_GROUND_Y = 150
HORSE_CANVAS_ANCHOR_X = 59


def render_racer_sprite(racer):
    temp = pygame.Surface((HORSE_CANVAS_W, HORSE_CANVAS_H), pygame.SRCALPHA)
    jump_offset = 0.0
    if racer.jump_timer > 0:
        t = 1 - racer.jump_timer / JUMP_DURATION
        jump_offset = 4 * JUMP_HEIGHT_PX * t * (1 - t)
    draw_horse(
        temp,
        20,
        HORSE_CANVAS_GROUND_Y - jump_offset,
        racer.coat,
        racer.mane,
        racer.leg_phase,
        moving=racer.speed > 0.4,
        jockey_colors=racer.jockey,
        ground_ref_y=HORSE_CANVAS_GROUND_Y,
    )
    return temp


class Item:
    _sprite = None
    RADIUS = 12

    def __init__(self, z, x):
        self.z = z
        self.x = x
        self.pulse_timer = 0
        if Item._sprite is None:
            Item._sprite = self._build_sprite()

    @classmethod
    def _build_sprite(cls):
        r = cls.RADIUS
        pad = OUTLINE_W + 3
        size = r * 2 + pad * 2
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        draw_outlined_circle(sprite, (255, 214, 64), center, r)
        pygame.draw.circle(sprite, (255, 240, 150), (center[0] - 4, center[1] - 4), 4)
        bolt = [(center[0] + 1, center[1] - 8), (center[0] - 5, center[1] + 1), (center[0], center[1] + 1),
                (center[0] - 2, center[1] + 8), (center[0] + 6, center[1] - 2), (center[0] + 1, center[1] - 2)]
        pygame.draw.polygon(sprite, (255, 255, 255), bolt)
        pygame.draw.polygon(sprite, (150, 100, 10), bolt, 1)
        return sprite


class Racer:
    def __init__(self, coat, mane, helmet, jersey, max_speed, x0, z0=0.0, name=None):
        self.coat = coat
        self.mane = mane
        self.jockey = (helmet, jersey)
        self.jersey = jersey
        self.name = name
        self.z = z0
        self.x = x0
        self.speed = 0.0
        self.max_speed = max_speed
        self.leg_phase = random.uniform(0, 6.28)
        self.boost_timer = 0
        self.jump_timer = 0
        self.target_x = x0
        self.retarget_timer = random.randint(10, 40)

    @property
    def lap(self):
        return int(self.z // TRACK_LEN)

    def physics_step(self, steer_input, accel_input):
        if accel_input > 0:
            self.speed += PLAYER_ACCEL
        elif accel_input < 0:
            self.speed -= PLAYER_BRAKE
        else:
            self.speed -= PLAYER_FRICTION

        top_speed = self.max_speed * (BOOST_MULT if self.boost_timer > 0 else 1.0)
        if abs(self.x) > HALF_ROAD_WIDTH:
            top_speed *= OFFTRACK_PENALTY

        self.speed = max(0.0, min(top_speed, self.speed))

        steer_rate = PLAYER_STEER_RATE * (0.5 + 0.5 * min(1.0, self.speed / self.max_speed))
        self.x += steer_input * steer_rate
        self.x = max(-MAX_X_CLAMP, min(MAX_X_CLAMP, self.x))

        self.z += self.speed
        self.leg_phase += 0.25 + self.speed * 0.035
        if self.boost_timer > 0:
            self.boost_timer -= 1
        if self.jump_timer > 0:
            self.jump_timer -= 1


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
        self.rank_font = load_korean_font(30, bold=True)

        self.sky = vertical_gradient((WIDTH, ROAD_TOP_Y + 20), SKY_TOP, SKY_HORIZON)

        self.reset()

    def reset(self):
        self.player = Racer(PLAYER_COAT, PLAYER_MANE, PLAYER_JOCKEY[0], PLAYER_JOCKEY[1], PLAYER_MAX_SPEED, x0=-120)
        self.ai_racers = []
        start_xs = [120, -260, 260]
        for i, spec in enumerate(AI_SPECS):
            self.ai_racers.append(
                Racer(spec["coat"], spec["mane"], spec["helmet"], spec["jersey"], spec["max_speed"], x0=start_xs[i], name=spec["name"])
            )
        self.items = self._build_items()
        self.state = "START"
        self.rank = 4
        self.time_elapsed = 0
        self.result_rank = None

    def _build_items(self):
        items = []
        spacing = TRACK_LEN / ITEM_COUNT
        for i in range(ITEM_COUNT):
            z = spacing * i + spacing * 0.5
            x = 380 if i % 2 == 0 else -380
            items.append(Item(z, x))
        return items

    def all_racers(self):
        return [self.player] + self.ai_racers

    def handle_start(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.state = "PLAYING"
            self.sound.play("select")

    def handle_playing_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.player.jump_timer <= 0:
                self.player.jump_timer = JUMP_DURATION
                self.sound.play("jump")

    def handle_finish_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            self.reset()
            self.sound.play("select")

    def update_playing(self, keys):
        self.time_elapsed += 1

        steer = 0
        if keys[pygame.K_LEFT]:
            steer -= 1
        if keys[pygame.K_RIGHT]:
            steer += 1
        accel = 0
        if keys[pygame.K_UP]:
            accel = 1
        elif keys[pygame.K_DOWN]:
            accel = -1
        prev_leg_phase = self.player.leg_phase
        self.player.physics_step(steer, accel)
        if self.player.speed > 0.5:
            step_unit = math.pi / 2
            if int(self.player.leg_phase / step_unit) != int(prev_leg_phase / step_unit):
                self.sound.play("step", volume=0.5)

        racers = self.all_racers()
        for ai in self.ai_racers:
            ai.retarget_timer -= 1
            if ai.retarget_timer <= 0:
                ai.retarget_timer = random.randint(35, 80)
                nearest, nearest_dist = None, 1e9
                for other in racers:
                    if other is ai:
                        continue
                    d = abs(other.z - ai.z)
                    if d < nearest_dist:
                        nearest, nearest_dist = other, d
                if nearest is not None and nearest_dist < 500 and random.random() < 0.4:
                    ai.target_x = max(-HALF_ROAD_WIDTH, min(HALF_ROAD_WIDTH, nearest.x + random.uniform(-60, 60)))
                else:
                    ai.target_x = random.uniform(-HALF_ROAD_WIDTH * 0.6, HALF_ROAD_WIDTH * 0.6)
            steer_ai = max(-1.0, min(1.0, (ai.target_x - ai.x) / 60))
            if random.random() < 0.003 and ai.jump_timer <= 0:
                ai.jump_timer = JUMP_DURATION
            ai.physics_step(steer_ai, 1)

        for i in range(len(racers)):
            for j in range(i + 1, len(racers)):
                a, b = racers[i], racers[j]
                if abs(a.z - b.z) < BUMP_Z_RANGE and abs(a.x - b.x) < BUMP_X_RANGE:
                    push = BUMP_PUSH if a.x < b.x else -BUMP_PUSH
                    a.x = max(-MAX_X_CLAMP, min(MAX_X_CLAMP, a.x - push))
                    b.x = max(-MAX_X_CLAMP, min(MAX_X_CLAMP, b.x + push))
                    a.speed *= BUMP_SLOWDOWN
                    b.speed *= BUMP_SLOWDOWN
                    if a is self.player or b is self.player:
                        self.sound.play("bump", volume=0.5)

        for item in self.items:
            for r in racers:
                if self._check_item_pickup(r, item):
                    r.boost_timer = BOOST_DURATION
                    if r is self.player:
                        self.sound.play("boost")

        ranking = sorted(racers, key=lambda r: -r.z)
        self.rank = ranking.index(self.player) + 1

        if self.player.z >= TRACK_LEN * LAPS_TO_WIN:
            self.trigger_finish()

    def _check_item_pickup(self, racer, item):
        if racer.speed <= 0:
            return False
        if abs(racer.x - item.x) > ITEM_PICKUP_X:
            return False
        k = round((racer.z - item.z) / TRACK_LEN)
        candidate = item.z + k * TRACK_LEN
        return (racer.z - racer.speed) < candidate <= racer.z

    def trigger_finish(self):
        self.state = "FINISH"
        self.result_rank = self.rank
        self.sound.play("finish")

    # --- rendering ---------------------------------------------------

    def world_to_screen(self, world_x, world_z, ref_z):
        rel_z = world_z - ref_z
        if rel_z <= NEAR_Z or rel_z > MAX_VISIBLE_Z:
            return None
        base_index = int((ref_z % TRACK_LEN) // SEGMENT_LENGTH) % NUM_SEGMENTS
        seg_index = int((world_z % TRACK_LEN) // SEGMENT_LENGTH) % NUM_SEGMENTS
        center_offset = TRACK_OFFSETS[seg_index] - TRACK_OFFSETS[base_index]
        scale = CAMERA_DEPTH / rel_z
        screen_x = WIDTH / 2 + (world_x + center_offset - self.player.x) * scale
        row = (NEAR_Z * ROAD_ROWS) / rel_z - 1
        screen_y = ROAD_TOP_Y + row
        return screen_x, screen_y, scale

    def draw_track_view(self):
        self.screen.blit(self.sky, (0, 0))
        pygame.draw.rect(self.screen, GRASS_COLOR_A, (0, ROAD_TOP_Y, WIDTH, ROAD_ROWS))

        player_z = self.player.z
        base_index = int((player_z % TRACK_LEN) // SEGMENT_LENGTH) % NUM_SEGMENTS
        base_offset = TRACK_OFFSETS[base_index]

        for row in range(ROAD_ROWS):
            z_ahead = (NEAR_Z * ROAD_ROWS) / (row + 1)
            world_z = player_z + z_ahead
            seg_index = int((world_z % TRACK_LEN) // SEGMENT_LENGTH) % NUM_SEGMENTS
            center_offset = TRACK_OFFSETS[seg_index] - base_offset
            scale = CAMERA_DEPTH / z_ahead
            half_w = HALF_ROAD_WIDTH * scale
            screen_cx = WIDTH / 2 + (center_offset - self.player.x) * scale
            y = ROAD_TOP_Y + row

            stripe = seg_index % 2 == 0
            road_col = ROAD_COLOR_A if stripe else ROAD_COLOR_B
            rumble_col = RUMBLE_COLOR_A if stripe else RUMBLE_COLOR_B
            grass_col = GRASS_COLOR_A if stripe else GRASS_COLOR_B

            left = screen_cx - half_w
            right = screen_cx + half_w
            rumble_w = max(1.0, half_w * 0.12)

            pygame.draw.rect(self.screen, grass_col, (0, y, WIDTH, 1))
            pygame.draw.rect(self.screen, road_col, (left, y, right - left, 1))
            pygame.draw.rect(self.screen, rumble_col, (left, y, rumble_w, 1))
            pygame.draw.rect(self.screen, rumble_col, (right - rumble_w, y, rumble_w, 1))
            if stripe:
                dash_w = max(1.0, half_w * 0.045)
                pygame.draw.rect(self.screen, WHITE, (screen_cx - dash_w / 2, y, dash_w, 1))

    def draw_billboards(self, extra_racers=None):
        billboards = []
        for item in self.items:
            proj = self.world_to_screen(item.x, item.z, self.player.z)
            if proj:
                billboards.append((proj[0] - self.player.z, proj, "item", item))

        racers = extra_racers if extra_racers is not None else self.all_racers()
        for r in racers:
            if r is self.player:
                continue
            proj = self.world_to_screen(r.x, r.z, self.player.z)
            if proj:
                rel_z = r.z - self.player.z
                billboards.append((rel_z, proj, "racer", r))

        billboards.sort(key=lambda b: -b[0])

        for rel_z, (screen_x, screen_y, scale), kind, obj in billboards:
            if kind == "item":
                s = max(0.15, min(3.0, scale * 10))
                sprite = Item._sprite
                w = max(2, int(sprite.get_width() * s))
                h = max(2, int(sprite.get_height() * s))
                scaled = pygame.transform.scale(sprite, (w, h))
                self.screen.blit(scaled, (screen_x - w / 2, screen_y - h / 2))
            else:
                s = max(0.06, min(2.2, scale * 1.7))
                sprite = render_racer_sprite(obj)
                w = max(2, int(HORSE_CANVAS_W * s))
                h = max(2, int(HORSE_CANVAS_H * s))
                scaled = pygame.transform.scale(sprite, (w, h))
                anchor_x = HORSE_CANVAS_ANCHOR_X / HORSE_CANVAS_W * w
                anchor_y = HORSE_CANVAS_GROUND_Y / HORSE_CANVAS_H * h
                self.screen.blit(scaled, (screen_x - anchor_x, screen_y - anchor_y))

    def draw_player(self):
        jump_offset = 0.0
        if self.player.jump_timer > 0:
            t = 1 - self.player.jump_timer / JUMP_DURATION
            jump_offset = 4 * JUMP_HEIGHT_PX * t * (1 - t) * 1.6
        px = WIDTH / 2 - HORSE_W * 1.35
        py = HEIGHT - 46 - jump_offset
        draw_horse(
            self.screen, px, py, self.player.coat, self.player.mane, self.player.leg_phase,
            moving=self.player.speed > 0.4, jockey_colors=self.player.jockey, ground_ref_y=HEIGHT - 46,
        )

    def draw_hud(self):
        panel = pygame.Rect(WIDTH - 150, 14, 136, 60)
        s = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (255, 255, 255, 225), (0, 0, panel.width, panel.height), border_radius=10)
        pygame.draw.rect(s, OUTLINE, (0, 0, panel.width, panel.height), width=3, border_radius=10)
        self.screen.blit(s, panel.topleft)

        rank_text = self.rank_font.render(f"{self.rank}위 / 4", True, OUTLINE)
        self.screen.blit(rank_text, rank_text.get_rect(center=(panel.centerx, panel.top + 22)))
        lap_num = min(self.player.lap + 1, LAPS_TO_WIN)
        lap_text = self.font.render(f"랩 {lap_num}/{LAPS_TO_WIN}", True, OUTLINE)
        self.screen.blit(lap_text, lap_text.get_rect(center=(panel.centerx, panel.top + 46)))

        if self.player.boost_timer > 0:
            boost_text = self.font.render("부스트!", True, (255, 140, 0))
            outline = self.font.render("부스트!", True, WHITE)
            pos = (20, 20)
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                self.screen.blit(outline, (pos[0] + ox, pos[1] + oy))
            self.screen.blit(boost_text, pos)

    def draw_playing(self):
        self.draw_track_view()
        self.draw_billboards()
        self.draw_player()
        self.draw_hud()

    def draw_center_text(self, lines, y_start=170):
        y = y_start
        for text, font, color in lines:
            surf = font.render(text, True, color)
            rect = surf.get_rect(center=(WIDTH // 2, y))
            outline = font.render(text, True, WHITE)
            for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, -2), (2, 2), (-2, 2), (2, -2)):
                self.screen.blit(outline, rect.move(ox, oy))
            self.screen.blit(surf, rect)
            y += rect.height + 12

    def draw_start(self):
        self.draw_track_view()
        self.draw_billboards()
        self.draw_player()
        self.draw_center_text(
            [
                ("City Gallop: Horse Race", self.big_font, DARK),
                ("3인칭 시점 말 경주 게임", self.font, DARK),
                ("방향키로 조종, SPACE로 점프 - SPACE/ENTER 로 시작", self.font, DARK),
            ],
            y_start=120,
        )

    def draw_finish(self):
        self.draw_track_view()
        self.draw_billboards()
        self.draw_player()
        self.draw_hud()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        rank_text = {1: "1위! 우승!", 2: "2위", 3: "3위", 4: "4위"}[self.result_rank]
        self.draw_center_text(
            [
                ("완주!", self.big_font, (255, 215, 0)),
                (rank_text, self.font, WHITE),
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
                elif self.state == "FINISH":
                    self.handle_finish_event(event)

            if self.state == "PLAYING":
                keys = pygame.key.get_pressed()
                self.update_playing(keys)

            if self.state == "START":
                self.draw_start()
            elif self.state == "PLAYING":
                self.draw_playing()
            elif self.state == "FINISH":
                self.draw_finish()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
