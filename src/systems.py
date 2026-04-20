
# ASTEROIDE SINGLEPLAYER v1.0
# This file coordinates world state, spawning, collisions, scoring, and progression.

import math
from random import uniform

import pygame as pg

import config as C
from sprites import (
    Asteroid, BossBullet, PowerAsteroid, Ship, UFO, BlackHole, ClockItem, LifeItem
)
from utils import Vec, rand_edge_pos, rand_unit_vec


class World:
    # Initialize the world state, entity groups, timers, and player progress.
    def __init__(self):
        self.ship = Ship(Vec(C.WIDTH / 2, C.HEIGHT / 2))
        self.bullets = pg.sprite.Group()
        self.ufo_bullets = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.ufos = pg.sprite.Group()
        # self.parasites = pg.sprite.Group()
        # self.parasite_timer = uniform(C.PARASITE_TIMER_MIN, C.PARASITE_TIMER_MAX)
        self.black_hole = None
        self.bh_timer = uniform(C.BH_TIMER_MIN, C.BH_TIMER_MAX)
        self.bh_duration = 0
        self.all_sprites = pg.sprite.Group(self.ship)
        self.score = 0
        self.lives = C.START_LIVES
        self.wave = 0
        self.wave_cool = C.WAVE_DELAY
        self.safe = C.SAFE_SPAWN_TIME
        self.ufo_timer = C.UFO_SPAWN_EVERY
        self.game_over = False  # Sinaliza fim de jogo para a cena principal
        # self.boss = None
        # self.boss_active = False
        # self.boss_warning = 0.0
        # self.boss_bullets = pg.sprite.Group()
        self.boss_defeated_timer = 0.0
        self.power_asteroids = pg.sprite.Group()
        self.spread_boss_timer = C.SPREAD_BOSS_INTERVAL
        self.clock_items = pg.sprite.Group()
        self.life_items = pg.sprite.Group()
        self.freeze_timer = 0.0



    def start_wave(self):
        # Spawn a new asteroid wave with difficulty based on the current round.
        self.wave += 1
        count = 3 + self.wave
        for _ in range(count):
            pos = rand_edge_pos()
            while (pos - self.ship.pos).length() < 150:
                pos = rand_edge_pos()
            ang = uniform(0, math.tau)
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
            vel = Vec(math.cos(ang), math.sin(ang)) * speed
            self.spawn_asteroid(pos, vel, "L")

        if uniform(0, 1) < C.SPREAD_ASTEROID_CHANCE:
            self.spawn_power_asteroid()

    def spawn_asteroid(self, pos: Vec, vel: Vec, size: str):
        a = Asteroid(pos, vel, size)
        a.frozen = self.freeze_timer > 0
        self.asteroids.add(a)
        self.all_sprites.add(a)

    def spawn_power_asteroid(self):
        pos = rand_edge_pos()
        while (pos - self.ship.pos).length() < 150:
            pos = rand_edge_pos()
        ang = uniform(0, math.tau)
        speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX)
        vel = Vec(math.cos(ang), math.sin(ang)) * speed
        pa = PowerAsteroid(pos, vel)
        pa.frozen = self.freeze_timer > 0
        self.power_asteroids.add(pa)
        self.asteroids.add(pa)
        self.all_sprites.add(pa)

    def spawn_ufo(self):
        # Spawn a single UFO at a screen edge and send it across the playfield.
        if self.ufos:
            return
        small = uniform(0, 1) < 0.5
        y = uniform(0, C.HEIGHT)
        x = 0 if uniform(0, 1) < 0.5 else C.WIDTH
        ufo = UFO(Vec(x, y), small)
        ufo.dir.xy = (1, 0) if x == 0 else (-1, 0)
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    def ufo_try_fire(self):
        # Let every active UFO attempt to fire at the ship.
        for ufo in self.ufos:
            bullet = ufo.fire_at(self.ship.pos)
            if bullet:
                self.ufo_bullets.add(bullet)
                self.all_sprites.add(bullet)

    def spawn_black_hole(self):
        pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))

        while (pos - self.ship.pos).length() < 200:
            pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))

        bh = BlackHole(pos)
        self.black_hole = bh
        self.all_sprites.add(bh)
        self.bh_duration = uniform(C.BH_DURATION_MIN, C.BH_DURATION_MAX)

    # def spawn_parasite(self):
    #     pos = rand_edge_pos()
    #     p = Parasite(pos)
    #     self.parasites.add(p)
    #     self.all_sprites.add(p)

    def try_fire(self):
        if len(self.bullets) >= C.MAX_BULLETS:
            return
        b = self.ship.fire()
        if b:
            self.bullets.add(b)
            self.all_sprites.add(b)

    def try_spread(self):
        # ativa o tiro espalhado (shift direito, com cooldown)
        result = self.ship.spread_fire()
        if result is None:
            return
        for b in result:
            self.bullets.add(b)
            self.all_sprites.add(b)

    def hyperspace(self):
        # Trigger the ship hyperspace action and apply its score penalty.
        self.ship.hyperspace()
        self.score = max(0, self.score - C.HYPERSPACE_COST)


    def update(self, dt: float, keys):
        # Update the world simulation, timers, enemy behavior, and progression.
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            if self.freeze_timer <= 0:
                self.freeze_timer = 0
                for a in self.asteroids:
                    a.frozen = False

        self.ship.control(keys, dt)
        self.all_sprites.update(dt)

        #update antigo dos parasitas
        # for spr in self.all_sprites:
        #     if not isinstance(spr, Parasite):   #atualiza tudo menos parasite
        #         spr.update(dt)
        
        #spawn do buraco negro
        if self.black_hole:
            self.bh_duration -= dt
            if self.bh_duration <= 0:
                self.black_hole.kill()
                self.black_hole = None
                self.bh_timer = uniform(10, 20)
        else:
            self.bh_timer -= dt
            if self.bh_timer <= 0:
                self.spawn_black_hole()

        #update do buraco negro quando tinha boss 
        # if not self.boss_active:
        #     if self.black_hole:
        #         self.bh_duration -= dt
        #         if self.bh_duration <= 0:
        #             self.black_hole.kill()
        #             self.black_hole = None
        #             self.bh_timer = uniform(10, 20)
        #     else:
        #         self.bh_timer -= dt
        #         if self.bh_timer <= 0:
        #             self.spawn_black_hole()


        #efeito de gravidade do buraco negro
        if self.black_hole:
            dir_vec = self.black_hole.pos - self.ship.pos
            dist = dir_vec.length()

            if dist > 0:
                dir_vec = dir_vec.normalize()
                force = self.black_hole.strength / (dist + 1) #diminui com a distancia
                self.ship.vel += dir_vec * force * dt * 50

        # spawn de parasite
        # if not self.boss_active:
        #     self.parasite_timer -= dt
        #     if self.parasite_timer <= 0:
        #         self.spawn_parasite()
        #         self.parasite_timer = uniform(C.PARASITE_TIMER_MIN, C.PARASITE_TIMER_MAX)

        if self.safe > 0:
            self.safe -= dt
            self.ship.invuln = 0.5

        # if not self.boss_active:
        if self.ufos:
            self.ufo_try_fire()
        else:
            self.ufo_timer -= dt
        if not self.ufos and self.ufo_timer <= 0:
            self.spawn_ufo()
            self.ufo_timer = C.UFO_SPAWN_EVERY

 
        # for p in self.parasites:
        #     p.update(dt, self.ship)
        # attached_count = sum(1 for p in self.parasites if p.attached)
        # self.ship.slow_factor = min(2.5, 1 + attached_count * 0.1)

        self.handle_collisions()

        if self.boss_defeated_timer > 0:
            self.boss_defeated_timer -= dt
            if self.boss_defeated_timer <= 0:
                self.start_wave()
            return

        if self.freeze_timer <= 0:
            if not self.asteroids and self.wave_cool <= 0:
            # if self.boss_active:
            #     self.update_boss(dt)
            # elif self.boss_warning > 0:
            #     self.boss_warning -= dt
            #     if self.boss_warning <= 0:
            #         self.spawn_boss()
            # elif not self.asteroids and self.wave_cool <= 0:
            #     if self.wave == 0:
                self.start_wave()
            #     else:    
            #         self.boss_warning = C.BOSS_WARNING_TIME
                self.wave_cool = C.WAVE_DELAY
            elif not self.asteroids:
                self.wave_cool -= dt

    # def spawn_boss(self):
    #     if self.black_hole:
    #         self.black_hole.kill()
    #         self.black_hole = None
    #     for ufo in list(self.ufos):
    #         ufo.kill()
    #     for p in list(self.parasites):
    #         p.kill()

    #     self.boss = Boss()
    #     self.boss_active = True
    #     self.all_sprites.add(self.boss)

    # def update_boss(self, dt):
    #     if not self.boss or not self.boss.alive():
    #         self.boss_active = False
    #         self.boss = None
    #         for b in list(self.boss_bullets):
    #             b.kill()
    #         self.boss_bullets.empty()
    #         self.boss_defeated_timer = 2.0
    #         return

    #     self.boss._eye_target = self.ship.pos
    #     self.boss.update(dt)

    #     for b in list(self.boss_bullets):
    #         b.update(dt)

    #     bullet = self.boss.try_fire(self.ship.pos)
    #     if bullet:
    #         self.boss_bullets.add(bullet)
    #         self.all_sprites.add(bullet)

    #     barrage = self.boss.try_barrage()
    #     for b in barrage:
    #         self.boss_bullets.add(b)
    #         self.all_sprites.add(b)

    #     self.boss.try_dash(self.ship.pos)

    #     if self.boss.asteroid_cool <= 0:
    #         self.boss.asteroid_cool = C.BOSS_ASTEROID_INTERVAL
    #         aim = Vec(self.ship.pos) - self.boss.pos
    #         if aim.length_squared() > 0:
    #             aim = aim.normalize()
    #         vel = aim * uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.5
    #         self.spawn_asteroid(Vec(self.boss.pos), vel, "M")

    #     self.spread_boss_timer -= dt
    #     if self.spread_boss_timer <= 0:
    #         self.spread_boss_timer = C.SPREAD_BOSS_INTERVAL
    #         self.spawn_power_asteroid()

    def handle_collisions(self):
        # Resolve collisions between bullets, asteroids, UFOs, and the ship.
        hits = pg.sprite.groupcollide(
            self.asteroids,
            self.bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, _ in hits.items():
            if isinstance(ast, PowerAsteroid):
                # asteroide especial dropa item de vida extra
                self.score += C.AST_SIZES[ast.size]["score"]
                life = LifeItem(Vec(ast.pos))
                self.life_items.add(life)
                self.all_sprites.add(life)
                ast.kill()
            else:
                self.split_asteroid(ast)

        ufo_hits = pg.sprite.groupcollide(
            self.asteroids,
            self.ufo_bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )
        for ast, _ in ufo_hits.items():
            self.split_asteroid(ast)

        for item in list(self.clock_items):
            if (item.pos - self.ship.pos).length() < (item.r + self.ship.r):
                item.kill()
                self.freeze_timer = C.FREEZE_DURATION
                for a in self.asteroids:
                    a.frozen = True

        # coleta de vida extra
        for item in list(self.life_items):
            if (item.pos - self.ship.pos).length() < (item.r + self.ship.r):
                item.kill()
                self.lives += 1

        # parasite_hits = pg.sprite.groupcollide(
        #     self.parasites,
        #     self.bullets,
        #     True,
        #     True, 
        #     collided=lambda p, b: (not p.attached) and (p.pos - b.pos).length() < p.r,
        # )
        # for p in parasite_hits:
        #     self.score += C.PARASITE_SCORE

        if self.ship.invuln <= 0 and self.safe <= 0:
            for ast in self.asteroids:
                if (ast.pos - self.ship.pos).length() < (ast.r + self.ship.r):
                    self.ship_die()
                    break
            for ufo in self.ufos:
                if (ufo.pos - self.ship.pos).length() < (ufo.r + self.ship.r):
                    self.ship_die()
                    break
            for bullet in self.ufo_bullets:
                if (bullet.pos - self.ship.pos).length() < (bullet.r + self.ship.r):
                    bullet.kill()
                    self.ship_die()
                    break

        for ufo in list(self.ufos):
            for b in list(self.bullets):
                if (ufo.pos - b.pos).length() < (ufo.r + b.r):
                    score = (C.UFO_SMALL["score"] if ufo.small
                             else C.UFO_BIG["score"])
                    self.score += score
                    ufo.kill()
                    b.kill()
        
        # for p in self.parasites:
        #     if not p.attached:
        #         if (p.pos - self.ship.pos).length() < (p.r + self.ship.r):
        #             p.attach(self.ship)

        # if self.boss and self.boss.alive():
        #     for b in list(self.bullets):
        #         if (self.boss.pos - b.pos).length() < self.boss.r:
        #             b.kill()
        #             self.boss.take_damage(C.BOSS_DAMAGE_PER_HIT)
        #             if self.boss.hp <= 0:
        #                 self.score += C.BOSS_SCORE
        #                 break

        #     if self.ship.invuln <= 0 and self.safe <= 0:
        #         if (self.boss.pos - self.ship.pos).length() < self.boss.r + self.ship.r:
        #             self.ship_die()
        #         for bb in list(self.boss_bullets):
        #             if (bb.pos - self.ship.pos).length() < bb.r + self.ship.r:
        #                 bb.kill()
        #                 self.ship_die()
        #                 break


        if self.black_hole:
            dist = (self.black_hole.pos - self.ship.pos).length()
            if dist < self.black_hole.r + self.ship.r:
                self.lives = 0
                self.game_over = True
                return

    def split_asteroid(self, ast: Asteroid):
        # Destroy an asteroid, award score, and spawn its smaller fragments.
        self.score += C.AST_SIZES[ast.size]["score"]
        split = C.AST_SIZES[ast.size]["split"]
        pos = Vec(ast.pos)

        if not isinstance(ast, PowerAsteroid) and uniform(0, 1) < C.FREEZE_ITEM_CHANCE:
            item = ClockItem(pos)
            self.clock_items.add(item)
            self.all_sprites.add(item)

        ast.kill()
        for s in split:
            dirv = rand_unit_vec()
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * 1.2
            self.spawn_asteroid(pos, dirv * speed, s)

    def ship_die(self):
        # Remove uma vida; sinaliza game over ou reposiciona a nave.
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True  # Game.run() detecta e muda de cena
            return
        self.ship.pos.xy = (C.WIDTH / 2, C.HEIGHT / 2)
        self.ship.vel.xy = (0, 0)
        self.ship.angle = -90
        self.ship.invuln = C.SAFE_SPAWN_TIME
        # self.ship.is_dashing = False
        # self.ship.dash_timer = 0.0
        # self.ship.cooldown_timer = 0.0
        # self.ship._pre_dash_vel = None
        self.safe = C.SAFE_SPAWN_TIME

    def draw(self, surf: pg.Surface, font: pg.font.Font):
        # Draw all world entities and the current HUD information.
        for spr in self.all_sprites:
            spr.draw(surf)

        pg.draw.line(surf, (60, 60, 60), (0, 50), (C.WIDTH, 50), width=1)
        txt = f"SCORE {self.score:06d}   LIVES {self.lives}   WAVE {self.wave}"
        label = font.render(txt, True, C.WHITE)
        surf.blit(label, (10, 10))

        # dash 
        # if self.ship.cooldown_timer > 0:
        #     dl = font.render(f"DASH {self.ship.cooldown_timer:.1f}s", True, C.GRAY)
        # elif self.ship.is_dashing:
        #     dl = font.render("DASH!", True, C.WHITE)
        # else:
        #     dl = font.render("DASH OK", True, C.WHITE)
        # surf.blit(dl, (C.WIDTH - 130, 10))

        # mostra o estado do spread shot no HUD
        if self.ship.spread_cool > 0:
            sl = font.render(f"SPREAD {self.ship.spread_cool:.1f}s", True, C.GRAY)
        else:
            sl = font.render("SPREAD OK", True, C.SPREAD_COLOR)
        surf.blit(sl, (C.WIDTH - 180, 10))

        if self.freeze_timer > 0:
            fl = font.render(f"FREEZE: {self.freeze_timer:.1f}s", True, C.ICY_BLUE)
            surf.blit(fl, (C.WIDTH // 2 - fl.get_width() // 2, 10))

        # if self.boss and self.boss.alive():
        #     self.boss.draw_hp_bar(surf)

        # if self.boss_warning > 0 and not self.boss_active:
        #     warn = font.render("!! BOSS INCOMING !!", True, C.RED)
        #     rect = warn.get_rect(center=(C.WIDTH // 2, C.HEIGHT // 2))
        #     surf.blit(warn, rect)

        # if self.boss_defeated_timer > 0:
        #     msg = font.render("BOSS DEFEATED!", True, C.ORANGE)
        #     rect = msg.get_rect(center=(C.WIDTH // 2, C.HEIGHT // 2))
        #     surf.blit(msg, rect)

