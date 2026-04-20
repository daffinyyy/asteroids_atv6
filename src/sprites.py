# ASTEROIDE SINGLEPLAYER v1.0
# This file defines the interactive game entities and their local behaviors.

import math
from random import uniform

import pygame as pg

import config as C
from utils import Vec, angle_to_vec, draw_circle, draw_poly, wrap_pos


class Bullet(pg.sprite.Sprite):
    # Initialize a player bullet with position, velocity, and lifetime.
    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        # Move the bullet, wrap it on screen, and expire it over time.
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Draw the bullet on the target surface.
        draw_circle(surf, self.pos, self.r)


class UfoBullet(pg.sprite.Sprite):
    # Initialize a UFO bullet with position, velocity, and lifetime.
    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.UFO_BULLET_TTL
        self.r = C.BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        # Move the UFO bullet, wrap it on screen, and expire it over time.
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Draw the UFO bullet on the target surface.
        draw_circle(surf, self.pos, self.r)


class Asteroid(pg.sprite.Sprite):
    # Initialize an asteroid with its position, velocity, and size profile.
    def __init__(self, pos: Vec, vel: Vec, size: str):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.size = size
        self.r = C.AST_SIZES[size]["r"]
        self.poly = self._make_poly()
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def _make_poly(self):
        # Build an irregular polygon outline based on the asteroid size.
        steps = 12 if self.size == "L" else 10 if self.size == "M" else 8
        pts = []
        for i in range(steps):
            ang = i * (360 / steps)
            jitter = uniform(0.75, 1.2)
            r = self.r * jitter
            v = Vec(math.cos(math.radians(ang)),
                    math.sin(math.radians(ang)))
            pts.append(v * r)
        return pts

    def update(self, dt: float):
        # Move the asteroid and wrap it across the screen.
        if getattr(self, "frozen", False):
            return
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        pts = [(self.pos + p) for p in self.poly]
        if getattr(self, "frozen", False):
            pg.draw.polygon(surf, C.ICY_BLUE, pts, width=0)
        pg.draw.polygon(surf, C.WHITE, pts, width=1)


class PowerAsteroid(Asteroid):

    def __init__(self, pos: Vec, vel: Vec):
        super().__init__(pos, vel, "S")
        self.pulse_timer = 0.0

    def update(self, dt: float):
        if getattr(self, "frozen", False):
            return
        super().update(dt)
        self.pulse_timer += dt

    def draw(self, surf: pg.Surface):
        glow_r = int(self.r + 6 + 3 * math.sin(self.pulse_timer * 4))
        glow_surf = pg.Surface((glow_r * 2, glow_r * 2), pg.SRCALPHA)
        pg.draw.circle(
            glow_surf,
            (*C.LIFE_COLOR, 60),
            (glow_r, glow_r),
            glow_r,
        )
        surf.blit(
            glow_surf,
            (self.pos.x - glow_r, self.pos.y - glow_r),
        )
        pts = [(self.pos + p) for p in self.poly]
        if getattr(self, "frozen", False):
            pg.draw.polygon(surf, C.ICY_BLUE, pts, width=0)
        pg.draw.polygon(surf, C.LIFE_COLOR, pts, width=2)

class ClockItem(pg.sprite.Sprite):
    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.r = C.CLOCK_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.ttl = 15.0  # disappears after 15 seconds

    def update(self, dt: float):
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        pg.draw.circle(surf, C.CLOCK_COLOR, self.pos, self.r, width=2)
        pg.draw.line(surf, C.CLOCK_COLOR, self.pos, self.pos + Vec(0, -self.r * 0.8), 2)
        pg.draw.line(surf, C.CLOCK_COLOR, self.pos, self.pos + Vec(self.r * 0.6, 0), 2)


class LifeItem(pg.sprite.Sprite):
    # power-up de vida extra — aparece ao destruir o asteroide especial
    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.r = C.LIFE_ITEM_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.ttl = C.LIFE_ITEM_TTL
        self.pulse_timer = 0.0

    def update(self, dt: float):
        self.ttl -= dt
        self.pulse_timer += dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # desenha um coracao simples pulsando
        scale = 1.0 + 0.15 * math.sin(self.pulse_timer * 4)
        r = int(self.r * scale)
        cx, cy = int(self.pos.x), int(self.pos.y)
        # dois circulos em cima + triangulo embaixo = coracao
        pg.draw.circle(surf, C.LIFE_COLOR, (cx - r // 3, cy - r // 4), r // 2)
        pg.draw.circle(surf, C.LIFE_COLOR, (cx + r // 3, cy - r // 4), r // 2)
        pg.draw.polygon(surf, C.LIFE_COLOR, [
            (cx - r + 2, cy - r // 6),
            (cx + r - 2, cy - r // 6),
            (cx, cy + r),
        ])


class Ship(pg.sprite.Sprite):
    # Initialize the player ship and its gameplay state.
    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.angle = -90.0
        self.cool = 0.0
        self.invuln = 0.0
        self.alive = True
        self.r = C.SHIP_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        # self.is_dashing = False
        # self.dash_timer = 0.0
        # self.cooldown_timer = 0.0
        # self._pre_dash_vel = None
        self.has_spread_shot = False
        self.shield_active = False
        self.shield_timer = 0.0      # tempo restante de duração
        self.shield_cooldown = 0.0   # tempo restante de cooldown

    def activate_shield(self):
        # Ativa o shield se não estiver em cooldown e não estiver já ativo.
        if self.shield_active or self.shield_cooldown > 0:
            return
        self.shield_active = True
        self.shield_timer = C.SHIELD_DURATION
        self.shield_cooldown = C.SHIELD_COOLDOWN
        
        # cooldown do tiro espalhado (habilidade do shift direito)
        self.spread_cool = 0.0

    def control(self, keys: pg.key.ScancodeWrapper, dt: float):
        # Apply rotation, thrust, and friction from the current input state.
        # slow = getattr(self, "slow_factor", 1) #efeito do parasita

        if keys[pg.K_LEFT]:
            self.angle -= C.SHIP_TURN_SPEED * dt
        if keys[pg.K_RIGHT]:
            self.angle += C.SHIP_TURN_SPEED * dt
        # if self.is_dashing:
        #     return
        if keys[pg.K_UP]:
            self.vel += angle_to_vec(self.angle) * C.SHIP_THRUST * dt
        self.vel *= C.SHIP_FRICTION

        #modificações de velocidade por causa do parasita 
        #     self.vel += angle_to_vec(self.angle) * (C.SHIP_THRUST / slow) * dt
        # friction = C.SHIP_FRICTION - (slow - 1) * 0.02
        # friction = max(0.90, friction)  # evita travar demais
        # self.vel *= friction    #antiga velocidade

    def fire(self):
        if self.cool > 0:
            return None
        self.cool = C.SHIP_FIRE_RATE

        dirv = angle_to_vec(self.angle)
        pos = self.pos + dirv * (self.r + 6)
        vel = self.vel + dirv * C.SHIP_BULLET_SPEED
        return Bullet(pos, vel)

    def spread_fire(self):
        # dispara tiros em todas as direções (habilidade com cooldown)
        if self.spread_cool > 0:
            return None
        self.spread_cool = C.SPREAD_COOLDOWN
        bullets = []
        for i in range(C.SPREAD_BULLET_COUNT):
            angle = (360 / C.SPREAD_BULLET_COUNT) * i
            rad = math.radians(angle)
            direction = Vec(math.cos(rad), math.sin(rad))
            spawn_pos = self.pos + direction * (self.r + 6)
            vel = direction * C.SHIP_BULLET_SPEED
            bullets.append(Bullet(spawn_pos, vel))
        return bullets

    def hyperspace(self):
        # Teleport the ship to a random location and reset its momentum.
        self.pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
        self.vel.xy = (0, 0)
        self.invuln = 1.0

    # def dash(self):
    #     # Apply a forward impulse with temporary invulnerability.
    #     if self.is_dashing or self.cooldown_timer > 0:
    #         return
    #     self._pre_dash_vel = Vec(self.vel)
    #     self.vel = angle_to_vec(self.angle) * C.DASH_FORCE * C.SHIP_THRUST
    #     self.is_dashing = True
    #     self.dash_timer = C.DASH_DURATION
    #     self.invuln = max(self.invuln, C.DASH_DURATION)
    #     self.cooldown_timer = C.DASH_COOLDOWN

    # @property
    # def is_invulnerable(self):
    #     return self.invuln > 0

    def update(self, dt: float):
        # Advance cooldowns, move the ship, and wrap it on screen.
        if self.cool > 0:
            self.cool -= dt
        if self.invuln > 0:
            self.invuln -= dt
        if self.shield_active:
            self.shield_timer -= dt
            if self.shield_timer <= 0:
                self.shield_active = False
                self.shield_timer = 0.0
        elif self.shield_cooldown > 0:
            self.shield_cooldown -= dt
            if self.shield_cooldown < 0:
                self.shield_cooldown = 0.0
            
        # reduz cooldown do spread shot
        if self.spread_cool > 0:
            self.spread_cool -= dt
            if self.spread_cool < 0:
                self.spread_cool = 0
                
        # if self.cooldown_timer > 0:
        #     self.cooldown_timer -= dt
        #     if self.cooldown_timer < 0:
        #         self.cooldown_timer = 0.0
        # if self.is_dashing:
        #     self.dash_timer -= dt
        #     if self.dash_timer <= 0:
        #         self.dash_timer = 0.0
        #         self.is_dashing = False
        #         self.vel = Vec(self._pre_dash_vel)
        #         self._pre_dash_vel = None
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        # Draw the ship and its temporary invulnerability indicator.
        dirv = angle_to_vec(self.angle)
        left = angle_to_vec(self.angle + 140)
        right = angle_to_vec(self.angle - 140)
        p1 = self.pos + dirv * self.r
        p2 = self.pos + left * self.r * 0.9
        p3 = self.pos + right * self.r * 0.9
        draw_poly(surf, [p1, p2, p3])
        # if self.is_dashing:
        #     draw_circle(surf, self.pos, self.r + 6)
        # elif self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
        #     draw_circle(surf, self.pos, self.r + 6)
        if self.invuln > 0 and int(self.invuln * 10) % 2 == 0:
            draw_circle(surf, self.pos, self.r + 6)
        if self.shield_active:
            shield_r = self.r + C.SHIELD_RADIUS_OFFSET
            pulse = int(self.shield_timer * 8) % 2  # pisca levemente ao final
            alpha = 200 if self.shield_timer > 0.5 or pulse == 0 else 80
            shield_surf = pg.Surface((shield_r * 2 + 4, shield_r * 2 + 4), pg.SRCALPHA)
            pg.draw.circle(
                shield_surf,
                (*C.SHIELD_COLOR, alpha),
                (shield_r + 2, shield_r + 2),
                shield_r,
                3,
            )
            surf.blit(shield_surf, (self.pos.x - shield_r - 2, self.pos.y - shield_r - 2))


class UFO(pg.sprite.Sprite):
    # Initialize a UFO enemy with its size profile and movement state.
    def __init__(self, pos: Vec, small: bool):
        super().__init__()
        self.pos = Vec(pos)
        self.small = small
        profile = C.UFO_SMALL if small else C.UFO_BIG
        self.r = profile["r"]
        self.aim = profile["aim"]
        self.speed = C.UFO_SPEED
        self.cool = C.UFO_FIRE_EVERY
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)
        self.dir = Vec(1, 0) if uniform(0, 1) < 0.5 else Vec(-1, 0)

    def update(self, dt: float):
        # Move the UFO, advance its fire cooldown, and remove it off screen.
        self.pos += self.dir * self.speed * dt
        self.cool -= dt
        if self.pos.x < -self.r * 2 or self.pos.x > C.WIDTH + self.r * 2:
            self.kill()
        self.rect.center = self.pos

    def fire_at(self, target_pos: Vec) -> UfoBullet | None:
        # Fire a bullet toward the ship with accuracy based on the UFO type.
        if self.cool > 0:
            return None
        aim_vec = Vec(target_pos) - self.pos
        if aim_vec.length_squared() == 0:
            aim_vec = self.dir.normalize()
        else:
            aim_vec = aim_vec.normalize()
        max_error = (1.0 - self.aim) * 60.0
        shot_dir = aim_vec.rotate(uniform(-max_error, max_error))
        self.cool = C.UFO_FIRE_EVERY
        spawn_pos = self.pos + shot_dir * (self.r + 6)
        vel = shot_dir * C.UFO_BULLET_SPEED
        return UfoBullet(spawn_pos, vel)

    def draw(self, surf: pg.Surface):
        # Draw the UFO body on the target surface.
        w, h = self.r * 2, self.r
        rect = pg.Rect(0, 0, w, h)
        rect.center = self.pos
        pg.draw.ellipse(surf, C.WHITE, rect, width=1)
        cup = pg.Rect(0, 0, w * 0.5, h * 0.7)
        cup.center = (self.pos.x, self.pos.y - h * 0.3)
        pg.draw.ellipse(surf, C.WHITE, cup, width=1)


class BlackHole(pg.sprite.Sprite):
    def __init__(self, pos: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.r = C.BLACK_HOLE_RADIUS  #raio que mata
        self.visual_r = C.BLACK_HOLE_VISUAL_RADIUS  #raio visual
        self.strength = C.BLACK_HOLE_STRENGTH
        self.rect = pg.Rect(0, 0, self.visual_r * 2, self.visual_r * 2)

    def update(self, dt: float):
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        pg.draw.circle(surf, C.PURPLE, self.pos, self.visual_r) #aura
        pg.draw.circle(surf, C.VIOLET, self.pos, self.visual_r - 4, 2) #anel
        pg.draw.circle(surf, C.BLACK, self.pos, self.r) #centro

# class Parasite(pg.sprite.Sprite):
#     def __init__(self, pos: Vec):
#         super().__init__()
#         self.pos = Vec(pos)
#         self.vel = Vec(0, 0)
#         self.r = C.PARASITE_RADIUS
#         self.speed = C.PARASITE_SPEED
#         self.attached = False
#         self.offset = Vec(0, 0)  # posição relativa quando grudar
#         self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

#     def update(self, dt: float, ship=None):
#         if self.attached:
#             self.pos = ship.pos + self.offset
#         else:
#             dir_vec = ship.pos - self.pos
#             if dir_vec.length() > 1:
#                 dir_vec = dir_vec.normalize()
#                 self.vel = dir_vec * self.speed

#             self.pos += self.vel * dt

#         if not self.attached:
#             self.pos = wrap_pos(self.pos)
#         self.rect.center = self.pos

#     def attach(self, ship):
#         self.attached = True
#         self.offset = self.pos - ship.pos

#     def draw(self, surf: pg.Surface):
#         color = C.GREEN if not self.attached else C.DARKER_GREEN
#         pts = []
#         for i in range(8):
#             ang = i * (360 / 8)
#             jitter = uniform(0.7, 1.3)
#             r = self.r * jitter
#             v = Vec(math.cos(math.radians(ang)), math.sin(math.radians(ang)))
#             pts.append(self.pos + v * r)

#         pg.draw.polygon(surf, color, pts)


class BossBullet(pg.sprite.Sprite):

    def __init__(self, pos: Vec, vel: Vec):
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = C.BOSS_BULLET_TTL
        self.r = C.BOSS_BULLET_RADIUS
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    def update(self, dt: float):
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self.rect.center = self.pos

    def draw(self, surf: pg.Surface):
        pg.draw.circle(surf, C.BOSS_BULLET_COLOR, self.pos, self.r)


# class Boss(pg.sprite.Sprite):

#     def __init__(self):
#         super().__init__()
#         self.max_hp = C.BOSS_HP
#         self.hp = C.BOSS_HP
#         self.r = C.BOSS_RADIUS
#         self.speed = C.BOSS_SPEED
#         self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

#         self.waypoints = [
#             Vec(80, 60),
#             Vec(C.WIDTH - 80, 60),
#             Vec(C.WIDTH - 80, C.HEIGHT - 60),
#             Vec(80, C.HEIGHT - 60),
#         ]
#         self.wp_index = 0
#         self.pos = Vec(self.waypoints[0])

#         self.fire_cool = 0.0
#         self.barrage_cool = 6.0
#         self.asteroid_cool = C.BOSS_ASTEROID_INTERVAL
#         self.dash_cool = 8.0
#         self.is_dashing = False
#         self.dash_timer = 0.0
#         self.dash_vel = Vec(0, 0)

#         self.rot_angle = 0.0
#         self.pulse_timer = 0.0

#     @property
#     def phase(self):
#         ratio = self.hp / self.max_hp
#         if ratio > 0.6:
#             return 1
#         elif ratio > 0.3:
#             return 2
#         return 3

#     @property
#     def fire_rate(self):
#         if self.phase == 1:
#             return C.BOSS_FIRE_RATE_P1
#         elif self.phase == 2:
#             return C.BOSS_FIRE_RATE_P2
#         return C.BOSS_FIRE_RATE_P3

#     def take_damage(self, amount):
#         self.hp -= amount
#         if self.hp <= 0:
#             self.hp = 0
#             self.kill()

#     def update(self, dt: float):
#         self.rot_angle += 30 * dt
#         self.pulse_timer += dt
#         self.fire_cool -= dt
#         self.barrage_cool -= dt
#         self.asteroid_cool -= dt
#         self.dash_cool -= dt

#         if self.is_dashing:
#             self.dash_timer -= dt
#             self.pos += self.dash_vel * dt
#             self.pos.x = max(self.r, min(C.WIDTH - self.r, self.pos.x))
#             self.pos.y = max(self.r, min(C.HEIGHT - self.r, self.pos.y))
#             if self.dash_timer <= 0:
#                 self.is_dashing = False
#         else:
#             target = self.waypoints[self.wp_index]
#             direction = target - self.pos
#             dist = direction.length()
#             if dist < 5:
#                 self.wp_index = (self.wp_index + 1) % len(self.waypoints)
#             else:
#                 move = direction.normalize() * self.speed * dt
#                 self.pos += move

#         speed_mult = 1 + (3 - self.phase) * 0.3
#         self.speed = C.BOSS_SPEED * speed_mult

#         self.rect.center = self.pos

#     def try_fire(self, ship_pos: Vec):
#         if self.fire_cool > 0:
#             return None
#         self.fire_cool = self.fire_rate
#         aim = Vec(ship_pos) - self.pos
#         if aim.length_squared() == 0:
#             return None
#         aim = aim.normalize()
#         spread = uniform(-5, 5)
#         aim = aim.rotate(spread)
#         vel = aim * C.BOSS_BULLET_SPEED
#         return BossBullet(self.pos + aim * (self.r + 8), vel)

#     def try_barrage(self):
#         if self.barrage_cool > 0 or self.phase == 1:
#             return []
#         self.barrage_cool = 5.0 if self.phase == 2 else 3.0
#         bullets = []
#         for i in range(C.BOSS_BARRAGE_COUNT):
#             angle = (360 / C.BOSS_BARRAGE_COUNT) * i
#             rad = math.radians(angle)
#             direction = Vec(math.cos(rad), math.sin(rad))
#             vel = direction * C.BOSS_BULLET_SPEED * 0.8
#             bullets.append(
#                 BossBullet(self.pos + direction * (self.r + 8), vel)
#             )
#         return bullets

#     def try_dash(self, ship_pos: Vec):
#         if self.dash_cool > 0 or self.phase == 1:
#             return
#         self.dash_cool = 6.0 if self.phase == 2 else 4.0
#         aim = Vec(ship_pos) - self.pos
#         if aim.length_squared() > 0:
#             self.dash_vel = aim.normalize() * C.BOSS_DASH_SPEED
#             self.is_dashing = True
#             self.dash_timer = C.BOSS_DASH_DURATION

#     def draw(self, surf: pg.Surface):
#         pulse = 1.0 + 0.08 * math.sin(self.pulse_timer * 3)
#         r = self.r * pulse

#         aura_r = int(r + 12 + 4 * math.sin(self.pulse_timer * 2))
#         aura_surf = pg.Surface((aura_r * 2, aura_r * 2), pg.SRCALPHA)
#         pg.draw.circle(
#             aura_surf, (220, 30, 30, 40), (aura_r, aura_r), aura_r
#         )
#         surf.blit(aura_surf, (self.pos.x - aura_r, self.pos.y - aura_r))

#         pts = []
#         for i in range(8):
#             angle = math.radians(self.rot_angle + i * 45)
#             jitter = 1.0 + 0.05 * math.sin(self.pulse_timer * 5 + i)
#             px = self.pos.x + math.cos(angle) * r * jitter
#             py = self.pos.y + math.sin(angle) * r * jitter
#             pts.append((px, py))

#         if self.phase == 1:
#             color = C.RED
#         elif self.phase == 2:
#             color = C.ORANGE
#         else:
#             color = C.DARK_RED

#         pg.draw.polygon(surf, color, pts)
#         pg.draw.polygon(surf, C.WHITE, pts, width=2)

#         eye_dir = Vec(0, 0)
#         if hasattr(self, '_eye_target'):
#             eye_dir = Vec(self._eye_target) - self.pos
#             if eye_dir.length_squared() > 0:
#                 eye_dir = eye_dir.normalize() * 6
#         eye_pos = (int(self.pos.x + eye_dir.x), int(self.pos.y + eye_dir.y))
#         pg.draw.circle(surf, C.WHITE, eye_pos, 6)
#         pg.draw.circle(surf, C.BLACK, eye_pos, 3)

#     def draw_hp_bar(self, surf: pg.Surface):
#         bar_w = 300
#         bar_h = 12
#         x = (C.WIDTH - bar_w) // 2
#         y = 20
#         ratio = self.hp / self.max_hp
#         pg.draw.rect(surf, C.DARK_RED, (x, y, bar_w, bar_h))
#         pg.draw.rect(surf, C.RED, (x, y, int(bar_w * ratio), bar_h))
#         pg.draw.rect(surf, C.WHITE, (x, y, bar_w, bar_h), 1)