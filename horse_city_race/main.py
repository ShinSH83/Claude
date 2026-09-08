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
SPEED_RAMP = 0.0009

FINISH_DISTANCE = 2200

SKY = (135, 206, 235)
SKY_EVENING = (255, 178, 140)
ROAD = (70, 70, 78)
ROAD_LINE = (230, 230, 230)
GROUND_DIRT = (90, 130, 70)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK = (30, 30, 40)

RIVAL_COLORS = [(90, 90, 200), (200, 90, 90), (90, 170, 90)]

PLAYER_X = 140
HORSE_W, HORSE_H = 78, 52


def draw_horse(surface, x, y, color, leg_phase, ducking=False):
    body_h = HORSE_H - 14 if ducking else HORSE_H
    body_rect = pygame.Rect(int(x), int(y - body_h), HORSE_W - 18, body_h - 10)
    pygame.draw.ellipse(surface, color, body_rect)

    neck_top = (x + HORSE_W - 30, y - body_h - 18)
    pygame.draw.polygon(
        surface,
        color,
        [
            (x + HORSE_W - 34, y - body_h + 6),
            neck_top,
            (x + HORSE_W - 4, y - body_h + 2),
        ],
    )
    pygame.draw.circle(surface, color, (int(x + HORSE_W - 6), int(y - body_h - 16)), 11)
    pygame.draw.polygon(
        surface,
        (60, 40, 20),
        [
            (x + HORSE_W - 12, y - body_h - 24),
            (x + HORSE_W - 4, y - body_h - 30),
            (x + HORSE_W - 2, y - body_h - 18),
        ],
    )

    tail_base = (x + 2, y - body_h + 8)
    sway = math.sin(leg_phase) * 6
    pygame.draw.line(surface, (60, 40, 20), tail_base, (tail_base[0] - 16, tail_base[1] + 18 + sway), 5)

    leg_w, leg_h = 8, 20
    offsets = [0, math.pi * 0.5, math.pi, math.pi * 1.5]
    leg_x_positions = [x + 6, x + 24, x + HORSE_W - 42, x + HORSE_W - 24]
    for lx, off in zip(leg_x_positions, offsets):
        swing = math.sin(leg_phase + off) * 10
        ly = y - 10
        pygame.draw.line(surface, (50, 35, 20), (lx, ly), (lx + swing * 0.3, ly + leg_h), 6)

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

    def __init__(self, x):
        self.kind = random.choice(self.KINDS)
        self.x = x
        if self.kind == "barrel":
            self.w, self.h = 32, 40
        elif self.kind == "cone":
            self.w, self.h = 24, 34
        else:
            self.w, self.h = 60, 10

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
        if self.kind == "barrel":
            pygame.draw.rect(surface, (150, 90, 40), r, border_radius=6)
            pygame.draw.rect(surface, (100, 60, 25), r, width=3, border_radius=6)
        elif self.kind == "cone":
            pygame.draw.polygon(
                surface,
                (230, 110, 30),
                [(r.centerx, r.top), (r.left, r.bottom), (r.right, r.bottom)],
            )
            pygame.draw.rect(surface, WHITE, (r.left, r.bottom - 8, r.width, 5))
        else:
            pygame.draw.ellipse(surface, (70, 110, 170), r)


class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.radius = 10

    def update(self, speed):
        self.x -= speed

    def offscreen(self):
        return self.x < -30

    def rect(self):
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius), self.radius * 2, self.radius * 2)

    def draw(self, surface, t):
        bob = math.sin(t * 0.15 + self.x * 0.05) * 4
        pygame.draw.circle(surface, (255, 210, 60), (int(self.x), int(self.y + bob)), self.radius)
        pygame.draw.circle(surface, (200, 150, 20), (int(self.x), int(self.y + bob)), self.radius, 2)


class Building:
    def __init__(self, x, w, h, color, layer):
        self.x = x
        self.w = w
        self.h = h
        self.color = color
        self.layer = layer

    def update(self, speed):
        self.x -= speed * self.layer

    def draw(self, surface):
        top = GROUND_Y - 60 - self.h
        pygame.draw.rect(surface, self.color, (self.x, top, self.w, self.h + 80))
        win_color = (255, 240, 180)
        for wy in range(int(top) + 10, GROUND_Y - 60, 18):
            for wx in range(int(self.x) + 6, int(self.x + self.w) - 6, 14):
                if (wx + wy) % 37 < 20:
                    pygame.draw.rect(surface, win_color, (wx, wy, 6, 8))


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
        self.font = pygame.font.SysFont("malgungothic,arial", 22)
        self.big_font = pygame.font.SysFont("malgungothic,arial", 46, bold=True)
        self.reset()

    def reset(self):
        self.player = Player()
        self.obstacles = []
        self.coins = []
        self.buildings = []
        self.rivals = [
            Rival("적토마", RIVAL_COLORS[0], 0.97),
            Rival("백마", RIVAL_COLORS[1], 1.0),
            Rival("흑마", RIVAL_COLORS[2], 1.03),
        ]
        self.speed = BASE_SPEED
        self.spawn_timer = 60
        self.coin_timer = 40
        self.time_elapsed = 0
        self.state = "START"
        self.score_coins = 0
        self.result_rank = None
        self.road_scroll = 0

        x = 0
        while x < WIDTH + 200:
            h = random.randint(60, 200)
            w = random.randint(60, 120)
            layer = random.choice([0.3, 0.5])
            color = random.choice([(90, 90, 110), (70, 75, 95), (110, 100, 120)])
            self.buildings.append(Building(x, w, h, color, layer))
            x += w + random.randint(10, 40)

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
        self.speed = min(MAX_SPEED, BASE_SPEED + self.time_elapsed * SPEED_RAMP * FPS)
        self.road_scroll = (self.road_scroll - self.speed) % 40

        self.player.update(self.speed)

        for b in self.buildings:
            b.update(self.speed)
        self.buildings = [b for b in self.buildings if b.x + b.w > -20]
        if not self.buildings or self.buildings[-1].x + self.buildings[-1].w < WIDTH:
            last_x = self.buildings[-1].x + self.buildings[-1].w if self.buildings else WIDTH
            h = random.randint(60, 200)
            w = random.randint(60, 120)
            layer = random.choice([0.3, 0.5])
            color = random.choice([(90, 90, 110), (70, 75, 95), (110, 100, 120)])
            self.buildings.append(Building(last_x + random.randint(10, 40), w, h, color, layer))

        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            self.spawn_timer = max(35, int(75 - self.speed * 3)) + random.randint(-10, 15)

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

    def draw_background(self):
        self.screen.fill(SKY)
        for b in self.buildings:
            b.draw(self.screen)
        pygame.draw.rect(self.screen, GROUND_DIRT, (0, GROUND_Y - 60, WIDTH, 60))
        pygame.draw.rect(self.screen, ROAD, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        for i in range(-1, WIDTH // 40 + 2):
            lx = i * 40 + self.road_scroll
            pygame.draw.rect(self.screen, ROAD_LINE, (lx, GROUND_Y + 25, 22, 5))

    def draw_hud(self):
        bar_x, bar_y, bar_w = 20, 16, WIDTH - 40
        pygame.draw.rect(self.screen, (0, 0, 0, 80), (bar_x, bar_y, bar_w, 70), border_radius=8)
        s = pygame.Surface((bar_w, 70), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, 110), (0, 0, bar_w, 70), border_radius=8)
        self.screen.blit(s, (bar_x, bar_y))

        entries = [("나", self.player.distance, (150, 100, 55))]
        for rv in self.rivals:
            entries.append((rv.name, rv.distance, rv.color))

        for i, (name, dist, color) in enumerate(entries):
            y = bar_y + 6 + i * 15
            pygame.draw.circle(self.screen, color, (bar_x + 12, y + 6), 5)
            track_x = bar_x + 30
            track_w = bar_w - 120
            pygame.draw.rect(self.screen, (255, 255, 255, 60), (track_x, y + 2, track_w, 6), 1)
            fill = min(1.0, dist / FINISH_DISTANCE) * track_w
            pygame.draw.rect(self.screen, color, (track_x, y + 2, max(2, fill), 6))
            label = self.font.render(name, True, WHITE)
            self.screen.blit(label, (bar_x + 30 + track_w + 10, y - 4))

        dist_text = self.font.render(
            f"거리: {int(self.player.distance)} / {FINISH_DISTANCE} m   코인: {self.score_coins}", True, BLACK
        )
        self.screen.blit(dist_text, (20, HEIGHT - 30))

    def draw_playing(self):
        self.draw_background()
        for b_ in self.obstacles:
            b_.draw(self.screen)
        for c in self.coins:
            c.draw(self.screen, self.time_elapsed)
        self.player.draw(self.screen)
        self.draw_hud()

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
