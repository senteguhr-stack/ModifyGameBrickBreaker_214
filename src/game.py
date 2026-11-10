import random
import pygame
from settings import *
from src.entities import Paddle, Ball, Brick, Particle, PowerUp
from src.save_manager import SaveManager
from src.audio_manager import AudioManager

class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 22, bold=True)
        self.small = pygame.font.SysFont("arial", 15)
        self.big = pygame.font.SysFont("arial", 66, bold=True)
        self.mid = pygame.font.SysFont("arial", 30, bold=True)
        self.save = SaveManager(DATA_DIR / "highscore.json")
        self.audio = AudioManager(SOUND_DIR, self.save.data)
        self.state = "menu"
        self.running = True
        self.score = 0
        self.lives = 3
        self.level = 1
        self.combo = 0
        self.combo_timer = 0
        self.particles = []
        self.powerups = []
        self.balls = []
        self.shake = 0
        self.flash = 0
        self.buttons = []
        self.normal_img = self.load_image(IMAGE_DIR / "ucup.png")
        self.damaged_img = self.load_image(IMAGE_DIR / "ucup_damaged.png")
        self.background_dots = [(random.randrange(WIDTH), random.randrange(HEIGHT), random.choice([1, 1, 2])) for _ in range(90)]
        self.paddle = Paddle()
        self.make_level()

    def load_image(self, path):
        try:
            return pygame.image.load(str(path)).convert()
        except (pygame.error, FileNotFoundError):
            image = pygame.Surface((180, 130))
            image.fill(PURPLE)
            pygame.draw.circle(image, CYAN, (90, 65), 30, 4)
            return image

    def make_level(self):
        self.paddle = Paddle()
        self.balls = [Ball(self.paddle)]
        self.bricks = []
        cols = 8 if self.level < 3 else 9
        rows = min(3 + self.level, 5)
        gap, bw, bh = 9, 112, 78
        total = cols * bw + (cols - 1) * gap
        start_x = (WIDTH - total) // 2
        for row in range(rows):
            for col in range(cols):
                if self.level >= 3 and (row + col) % 5 == 0:
                    continue
                hp = 1 if self.level == 1 else (2 if row < 2 or self.level >= 3 else 1)
                rect = (start_x + col * (bw + gap), 105 + row * (bh + gap), bw, bh)
                self.bricks.append(Brick(rect, self.normal_img, self.damaged_img, hp, special=(self.level >= 4 and (row + col) % 4 == 0)))
        self.boss = None
        if self.level >= 5:
            self.bricks.clear()
            self.boss = {"rect": pygame.Rect(WIDTH//2 - 170, 125, 340, 180), "hp": 24, "max": 24, "dir": 1, "flash": 0}
        self.combo = 0
        self.combo_timer = 0

    def start_game(self):
        self.score, self.lives, self.level = 0, 3, 1
        self.particles.clear()
        self.powerups.clear()
        self.make_level()
        self.state = "playing"

    def add_burst(self, pos, count=24, big=False):
        colors = [CYAN, PURPLE, MAGENTA, ORANGE, RED, WHITE]
        for _ in range(count):
            self.particles.append(Particle(pos, random.choice(colors)))
        if big:
            self.shake = 0.22
        self.flash = 0.08

    def hit_brick(self, brick, ball):
        destroyed = brick.hit()
        ball.vel.y *= -1
        # Play the user's uploaded impact sound on every brick hit.
        self.audio.play("hit")
        if destroyed:
            self.combo += 1
            self.combo_timer = 2.0
            multiplier = min(8, 1 + self.combo // 3)
            self.score += 100 * multiplier
            self.add_burst(brick.rect.center, 34 + brick.max_hp * 12, big=brick.max_hp > 1)
            self.audio.play("destroy")
            if random.random() < 0.18:
                self.powerups.append(PowerUp(*brick.rect.center))
        else:
            self.score += 25
            self.add_burst(ball.pos, 7)
        self.save.set_high_score(self.score)

    def update(self, dt):
        if self.state != "playing":
            for p in self.particles[:]:
                if not p.update(dt): self.particles.remove(p)
            return
        keys = pygame.key.get_pressed()
        self.paddle.update(dt, keys)
        for brick in self.bricks:
            brick.update(dt)
        if self.combo_timer > 0:
            self.combo_timer -= dt
        else:
            self.combo = 0

        for ball in self.balls[:]:
            lost = ball.update(dt, self.paddle)
            if lost:
                self.balls.remove(ball)
                continue
            if not ball.launched:
                continue
            for brick in self.bricks:
                if brick.alive and ball.rect.colliderect(brick.rect):
                    self.hit_brick(brick, ball)
                    break

            if self.boss and ball.rect.colliderect(self.boss["rect"]):
                self.boss["hp"] -= 1
                self.boss["flash"] = 0.12
                ball.vel.y *= -1
                self.score += 80
                self.add_burst(ball.pos, 12)
                if self.boss["hp"] <= 0:
                    self.add_burst(self.boss["rect"].center, 150, True)
                    self.boss = None
                    self.state = "victory"
                    self.audio.play("victory")
                    self.save.set_high_score(self.score)

        if not self.balls:
            self.lives -= 1
            self.audio.play("life")
            if self.lives <= 0:
                self.state = "gameover"
                self.audio.play("gameover")
            else:
                self.balls = [Ball(self.paddle)]

        if self.boss:
            b = self.boss
            b["rect"].x += int(150 * b["dir"] * dt)
            if b["rect"].left < 80 or b["rect"].right > WIDTH - 80: b["dir"] *= -1
            b["flash"] = max(0, b["flash"] - dt)
        elif self.bricks and all(not b.alive for b in self.bricks):
            self.level += 1
            if self.level > 5:
                self.state = "victory"
            else:
                self.make_level()

        for power in self.powerups[:]:
            if not power.update(dt):
                self.powerups.remove(power)
            elif power.rect.colliderect(self.paddle.rect):
                self.apply_power(power.kind)
                self.powerups.remove(power)
                self.audio.play("power")

        for p in self.particles[:]:
            if not p.update(dt): self.particles.remove(p)
        self.shake = max(0, self.shake - dt)
        self.flash = max(0, self.flash - dt)

    def apply_power(self, kind):
        if kind == "big":
            self.paddle.set_width(220); self.paddle.big_timer = 12
        elif kind == "multi":
            source = self.balls[0] if self.balls else Ball(self.paddle)
            for angle in (-0.55, 0.55):
                b = Ball(self.paddle); b.pos = source.pos.copy()
                b.launched = True; b.vel = source.vel.rotate(angle * 57.3)
                self.balls.append(b)
        elif kind == "slow":
            for b in self.balls: b.vel *= 0.72
        elif kind == "fire":
            for b in self.balls: b.fire_timer = 8
        elif kind == "life":
            self.lives = min(9, self.lives + 1)
        elif kind == "magnet":
            self.paddle.magnet_timer = 8

    def draw_background(self):
        self.screen.fill(BG)
        for x, y, r in self.background_dots:
            pygame.draw.circle(self.screen, (25, 55, 80), (x, y), r)
        pygame.draw.line(self.screen, (30, 35, 65), (20, 72), (WIDTH-20, 72), 1)

    def text(self, value, font, color, center):
        surf = font.render(str(value), True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def button(self, label, center, width=270):
        rect = pygame.Rect(0, 0, width, 48); rect.center = center
        mouse = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse)
        color = MAGENTA if hover else CYAN
        pygame.draw.rect(self.screen, (18, 20, 42), rect, border_radius=8)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=8)
        self.text(label, self.font, WHITE if hover else CYAN, rect.center)
        self.buttons.append((label, rect))

    def draw_menu(self):
        self.text("AMBATUBALL", self.big, CYAN, (WIDTH//2, 220))
        self.text(TAGLINE, self.small, WHITE, (WIDTH//2, 278))
        self.buttons = []
        for i, label in enumerate(["PLAY GAME", "SETTINGS", "HIGH SCORE", "EXIT"]):
            self.button(label, (WIDTH//2, 380 + i*62))
        self.text("NEON ARCADE EDITION  •  60 FPS", self.small, MUTED, (WIDTH//2, 690))

    def draw_hud(self):
        self.text(f"SCORE  {self.score:07d}", self.font, WHITE, (125, 35))
        self.text(f"LEVEL  {self.level}", self.font, CYAN, (WIDTH//2, 35))
        self.text(f"LIVES  {self.lives}", self.font, MAGENTA, (WIDTH-120, 35))
        if self.combo >= 2 and self.combo_timer > 0:
            self.text(f"COMBO x{min(8, 1+self.combo//3)}", self.mid, ORANGE, (WIDTH//2, 82))

    def draw_play(self):
        self.draw_hud()
        for brick in self.bricks: brick.draw(self.screen)
        if self.boss:
            r = self.boss["rect"]
            self.screen.blit(pygame.transform.smoothscale(self.normal_img, r.size), r)
            pygame.draw.rect(self.screen, MAGENTA, r, 4, border_radius=12)
            bar = pygame.Rect(WIDTH//2-170, 95, 340, 12)
            pygame.draw.rect(self.screen, (50, 25, 55), bar, border_radius=5)
            fill = bar.copy(); fill.width = int(bar.width * self.boss["hp"] / self.boss["max"])
            pygame.draw.rect(self.screen, RED, fill, border_radius=5)
            self.text("BOSS", self.small, WHITE, (WIDTH//2, 87))
        self.paddle.draw(self.screen)
        for ball in self.balls: ball.draw(self.screen)
        for power in self.powerups: power.draw(self.screen, self.font)

    def draw_overlay(self, title, subtitle, options):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); shade.fill((3, 4, 14, 205))
        self.screen.blit(shade, (0, 0))
        self.text(title, self.big, CYAN, (WIDTH//2, 245))
        self.text(subtitle, self.small, WHITE, (WIDTH//2, 305))
        self.buttons = []
        for i, label in enumerate(options):
            self.button(label, (WIDTH//2, 390 + i*62))

    def draw_settings(self):
        self.text("SETTINGS", self.big, CYAN, (WIDTH//2, 210))
        self.text(f"SFX VOLUME  {int(self.save.data['sfx_volume']*100)}%    [LEFT / RIGHT]", self.font, WHITE, (WIDTH//2, 330))
        self.text(f"MUSIC VOLUME  {int(self.save.data['music_volume']*100)}%    [UP / DOWN]", self.font, WHITE, (WIDTH//2, 390))
        self.text(f"MUTE: {'ON' if self.save.data['muted'] else 'OFF'}  [M]", self.font, MAGENTA, (WIDTH//2, 450))
        self.buttons = []
        self.button("BACK", (WIDTH//2, 560), 180)

    def draw(self):
        self.draw_background()
        self.buttons = []
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.draw_play()
        elif self.state == "pause":
            self.draw_play()
            self.draw_overlay("PAUSED", "GAME SUSPENDED", ["RESUME", "RESTART", "SETTINGS", "MAIN MENU"])
        elif self.state == "settings":
            self.draw_settings()
        elif self.state == "highscore":
            self.text("HIGH SCORE", self.big, CYAN, (WIDTH//2, 250))
            self.text(str(self.save.high_score), self.big, WHITE, (WIDTH//2, 360))
            self.buttons = []; self.button("BACK", (WIDTH//2, 500), 180)
        elif self.state == "gameover":
            self.draw_play()
            self.draw_overlay("GAME OVER", f"FINAL SCORE: {self.score}", ["PLAY AGAIN", "MAIN MENU"])
        elif self.state == "victory":
            self.draw_play()
            self.draw_overlay("VICTORY!", f"FINAL SCORE: {self.score}", ["PLAY AGAIN", "MAIN MENU"])
        for particle in self.particles:
            particle.draw(self.screen)
        if self.flash > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(45 * self.flash / 0.08)))
            self.screen.blit(flash, (0, 0))
        pygame.display.flip()

    def click(self, pos):
        for label, rect in self.buttons:
            if rect.collidepoint(pos):
                if self.state == "menu":
                    if label == "PLAY GAME": self.start_game()
                    elif label == "SETTINGS": self.state = "settings"
                    elif label == "HIGH SCORE": self.state = "highscore"
                    elif label == "EXIT": self.running = False
                elif self.state == "settings" or self.state == "highscore":
                    self.state = "menu"
                elif self.state == "pause":
                    if label == "RESUME": self.state = "playing"
                    elif label == "RESTART": self.start_game()
                    elif label == "SETTINGS": self.state = "settings"
                    elif label == "MAIN MENU": self.state = "menu"
                elif self.state in ("gameover", "victory"):
                    if label == "PLAY AGAIN": self.start_game()
                    elif label == "MAIN MENU": self.state = "menu"

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.click(event.pos)
            elif event.type == pygame.KEYDOWN:
                if self.state == "playing":
                    if event.key == pygame.K_SPACE:
                        for ball in self.balls: ball.launch()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "pause"
                elif self.state == "pause" and event.key == pygame.K_ESCAPE:
                    self.state = "playing"
                elif self.state == "settings":
                    if event.key == pygame.K_LEFT: self.audio.change_volume("sfx_volume", -0.05)
                    elif event.key == pygame.K_RIGHT: self.audio.change_volume("sfx_volume", 0.05)
                    elif event.key == pygame.K_DOWN: self.audio.change_volume("music_volume", -0.05)
                    elif event.key == pygame.K_UP: self.audio.change_volume("music_volume", 0.05)
                    elif event.key == pygame.K_m: self.audio.toggle_mute()
                    elif event.key in (pygame.K_ESCAPE, pygame.K_RETURN): self.state = "menu"
                elif self.state in ("gameover", "victory") and event.key == pygame.K_RETURN:
                    self.start_game()
                elif self.state in ("highscore",) and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    self.state = "menu"
                elif self.state == "menu" and event.key == pygame.K_RETURN:
                    self.start_game()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.033)
            self.events()
            self.update(dt)
            self.draw()
        self.save.save()
        pygame.quit()
