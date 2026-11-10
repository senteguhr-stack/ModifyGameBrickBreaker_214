import math
import random
import pygame
from settings import *

def cover_image(image, size):
    """Scale and center-crop an image so faces remain large inside a brick."""
    w, h = size
    iw, ih = image.get_size()
    scale = max(w / iw, h / ih)
    scaled = pygame.transform.smoothscale(image, (int(iw * scale), int(ih * scale)))
    x = (scaled.get_width() - w) // 2
    y = (scaled.get_height() - h) // 2
    return scaled.subsurface((x, y, w, h)).copy()

class Paddle:
    def __init__(self):
        self.base_width = 150
        self.width = self.base_width
        self.height = 17
        self.rect = pygame.Rect(WIDTH // 2 - self.width // 2, HEIGHT - 65, self.width, self.height)
        self.speed = 650
        self.big_timer = 0
        self.magnet_timer = 0

    def update(self, dt, keys):
        direction = int(keys[pygame.K_RIGHT] or keys[pygame.K_d]) - int(keys[pygame.K_LEFT] or keys[pygame.K_a])
        self.rect.x += int(direction * self.speed * dt)
        self.rect.clamp_ip(pygame.Rect(12, 0, WIDTH - 24, HEIGHT))

        if self.big_timer > 0:
            self.big_timer -= dt
            if self.big_timer <= 0:
                self.set_width(self.base_width)
        if self.magnet_timer > 0:
            self.magnet_timer -= dt

    def set_width(self, width):
        center = self.rect.centerx
        self.width = width
        self.rect.width = width
        self.rect.centerx = center
        self.rect.clamp_ip(pygame.Rect(12, 0, WIDTH - 24, HEIGHT))

    def draw(self, surface):
        glow = pygame.Surface((self.width + 34, 42), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*CYAN, 35), (0, 10, self.width + 34, 18), border_radius=12)
        surface.blit(glow, (self.rect.x - 17, self.rect.y - 12))
        pygame.draw.rect(surface, CYAN, self.rect, border_radius=8)
        pygame.draw.rect(surface, WHITE, self.rect.inflate(-12, -8), 1, border_radius=5)

class Ball:
    def __init__(self, paddle):
        self.radius = 9
        self.speed = 430
        self.pos = pygame.Vector2(paddle.rect.centerx, paddle.rect.top - self.radius - 2)
        self.vel = pygame.Vector2(0, 0)
        self.launched = False
        self.fire_timer = 0

    def launch(self):
        if not self.launched:
            self.launched = True
            self.vel = pygame.Vector2(random.choice([-0.45, 0.45]), -1).normalize() * self.speed

    def update(self, dt, paddle):
        if not self.launched:
            self.pos.x = paddle.rect.centerx
            self.pos.y = paddle.rect.top - self.radius - 2
            if paddle.magnet_timer > 0:
                return False
            return False

        self.pos += self.vel * dt
        if self.pos.x - self.radius <= 10:
            self.pos.x = 10 + self.radius
            self.vel.x = abs(self.vel.x)
        elif self.pos.x + self.radius >= WIDTH - 10:
            self.pos.x = WIDTH - 10 - self.radius
            self.vel.x = -abs(self.vel.x)
        if self.pos.y - self.radius <= 72:
            self.pos.y = 72 + self.radius
            self.vel.y = abs(self.vel.y)

        ball_rect = self.rect
        if self.vel.y > 0 and ball_rect.colliderect(paddle.rect):
            self.pos.y = paddle.rect.top - self.radius
            offset = (self.pos.x - paddle.rect.centerx) / max(1, paddle.rect.width / 2)
            self.vel = pygame.Vector2(offset * 0.85, -1).normalize() * self.speed
        return self.pos.y - self.radius > HEIGHT

    @property
    def rect(self):
        return pygame.Rect(int(self.pos.x - self.radius), int(self.pos.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def draw(self, surface):
        glow = pygame.Surface((38, 38), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*CYAN, 45), (19, 19), 18)
        surface.blit(glow, (int(self.pos.x - 19), int(self.pos.y - 19)))
        pygame.draw.circle(surface, WHITE, (int(self.pos.x), int(self.pos.y)), self.radius)
        pygame.draw.circle(surface, CYAN, (int(self.pos.x), int(self.pos.y)), self.radius, 2)

class Brick:
    def __init__(self, rect, normal, damaged, hp=2, special=False):
        self.rect = pygame.Rect(rect)
        self.normal = cover_image(normal, self.rect.size)
        self.damaged = cover_image(damaged, self.rect.size)
        self.hp = hp
        self.max_hp = hp
        self.special = special
        self.flash = 0
        self.alive = True

    def hit(self):
        self.hp -= 1
        self.flash = 0.14
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def update(self, dt):
        self.flash = max(0, self.flash - dt)

    def draw(self, surface):
        if not self.alive:
            return
        image = self.normal if self.hp == self.max_hp else self.damaged
        surface.blit(image, self.rect)
        color = MAGENTA if self.special else CYAN
        if self.flash:
            color = WHITE
            overlay = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            overlay.fill((255, 255, 255, int(100 * self.flash / 0.14)))
            surface.blit(overlay, self.rect)
        pygame.draw.rect(surface, color, self.rect, 2, border_radius=5)
        if self.max_hp > 1:
            pygame.draw.circle(surface, ORANGE if self.hp == 1 else WHITE,
                               (self.rect.right - 8, self.rect.top + 8), 4)

class Particle:
    def __init__(self, pos, color, velocity=None, life=None, size=None):
        self.pos = pygame.Vector2(pos)
        angle = random.random() * math.tau
        speed = random.uniform(70, 310)
        self.vel = velocity or pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
        self.life = life or random.uniform(0.35, 0.8)
        self.max_life = self.life
        self.color = color
        self.size = size or random.randint(2, 5)

    def update(self, dt):
        self.life -= dt
        self.pos += self.vel * dt
        self.vel *= 0.985
        return self.life > 0

    def draw(self, surface):
        alpha = max(0, min(255, int(255 * self.life / self.max_life)))
        r = max(1, int(self.size * self.life / self.max_life))
        pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), r)

class PowerUp:
    TYPES = ["big", "multi", "slow", "fire", "life", "magnet"]
    COLORS = {"big": CYAN, "multi": PURPLE, "slow": GREEN, "fire": ORANGE, "life": RED, "magnet": MAGENTA}
    LABELS = {"big": "B", "multi": "M", "slow": "S", "fire": "F", "life": "+", "magnet": "G"}

    def __init__(self, x, y):
        self.kind = random.choice(self.TYPES)
        self.rect = pygame.Rect(x - 13, y - 13, 26, 26)
        self.speed = 190

    def update(self, dt):
        self.rect.y += int(self.speed * dt)
        return self.rect.top <= HEIGHT

    def draw(self, surface, font):
        color = self.COLORS[self.kind]
        pygame.draw.circle(surface, color, self.rect.center, 14, 2)
        label = font.render(self.LABELS[self.kind], True, WHITE)
        surface.blit(label, label.get_rect(center=self.rect.center))
