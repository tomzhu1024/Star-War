import math
import random
from sys import exit

import pygame
import os
from pygame.locals import *


class Player(pygame.sprite.Sprite):
    def __init__(self, normal_img, explosion_img):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((40, 40), SRCALPHA)
        self.image.blit(normal_img, (0, 0))
        self.explosion_img = explosion_img
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.is_alive = True
        self.dead_ani_last_update = 0
        self.dead_ani_frame = 0
        self.is_running = True

    def update(self, mouse_pos, current_time):
        if self.is_alive:
            self.rect.centerx, self.rect.centery = mouse_pos
        else:
            if current_time - self.dead_ani_last_update > 100:  # Aniamtion frame interval
                self.image.blit(self.explosion_img, (0, 0), area=(self.dead_ani_frame * 40, 0, 40, 40))
                self.dead_ani_last_update = current_time
                self.dead_ani_frame += 1
                if self.dead_ani_frame == 6:
                    self.is_running = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def set_dead(self):
        self.is_alive = False


class Enemy(pygame.sprite.Sprite):
    def __init__(self, normal_img, explosion_img, speed, health, award):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((40, 40), SRCALPHA)
        self.image.blit(normal_img, (0, 0))
        self.explosion_img = explosion_img
        self.rect = pygame.Rect(0, 0, 40, 40)
        self.born_time = pygame.time.get_ticks()
        self.rect.centerx = random.randint(30, 290)
        self.rect.centery = -20
        self.speed = speed
        self.is_alive = True
        self.dead_ani_last_update = 0
        self.dead_ani_frame = 0
        self.health = health
        self.award = award

    def update(self, current_time):
        if self.is_alive:
            self.rect.centery = -20 + self.speed * (current_time - self.born_time)
        else:
            if current_time - self.dead_ani_last_update > 100:  # Aniamtion frame interval
                self.image.blit(self.explosion_img, (0, 0), area=(self.dead_ani_frame * 40, 0, 40, 40))
                self.dead_ani_last_update = current_time
                self.dead_ani_frame += 1
                if self.dead_ani_frame == 6:
                    self.kill()

    def set_dead(self):
        self.is_alive = False


class Fireball(pygame.sprite.Sprite):
    def __init__(self, img, born_pos, speed):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((13, 13), SRCALPHA)
        self.image.blit(img, (0, 0))
        self.rect = pygame.Rect(0, 0, 13, 13)
        self.born_time = pygame.time.get_ticks()
        self.born_pos = born_pos
        self.speed = speed

    def update(self, current_time):
        self.rect.centerx = self.born_pos[0]
        self.rect.centery = self.born_pos[1] - self.speed * (current_time - self.born_time)
        if self.rect.y < -13:
            self.kill()


def update_diff(score):
    global enemy_speed, enemy_interval, enemy_max, fire_interval
    enemy_speed = 0.08 + 0.16 * (1 / (-score / 400 - 1) + 1)
    enemy_interval = 3000 - 2500 * (1 / (-score / 600 - 1) + 1)
    enemy_max = int(2 * math.log(score, 30)) + 3
    fire_interval = max(400 - int(200 * score / 1000), 200)


def random_scale_factor():
    if random.randint(0, 1) == 0:
        return (random.random() * random.random() + 1)
    else:
        return (1 - random.random() * random.random() * 0.5)


if __name__ == '__main__':
    pygame.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode((320, 480), 0, 32)
    pygame.time.delay(1000)
    pygame.display.set_caption("Star War")

    try:
        background_surf = pygame.image.load(os.path.join("resources","background.jpg")).convert()
        logo_surf = pygame.image.load(os.path.join("resources","logo.png")).convert_alpha()
        player_surf = pygame.image.load(os.path.join("resources","player.png")).convert_alpha()
        enemy_surfs = []
        for i in range(5):
            enemy_surfs.append(pygame.image.load(os.path.join("resources","enemy%s.png"%i)).convert_alpha())
        explosion_surf = pygame.image.load(os.path.join("resources","explosion.png")).convert_alpha()
        fireball_surf = pygame.image.load(os.path.join("resources","fireball.png")).convert_alpha()
        gameover_surf = pygame.image.load(os.path.join("resources","gameover.png")).convert_alpha()

        score_sounds = []
        for i in range(3):
            score_sounds.append(pygame.mixer.Sound(os.path.join("resources","score%s.wav"%i)))
            score_sounds[i].set_volume(0.35)
        dead_sound = pygame.mixer.Sound(os.path.join("resources","dead.wav"))
        dead_sound.set_volume(0.15)
        click_sound = pygame.mixer.Sound(os.path.join("resources","click.wav"))
        my_font = pygame.font.Font(os.path.join("resources","consola.ttf"), 16)
        pygame.mixer.music.load(os.path.join("resources","bgm.mp3"))
        pygame.mixer.music.set_volume(0.15)
        pygame.mixer.music.play(-1)
    except pygame.error as err:
        print("Resources files missing: %s" % str(err))
        exit(-1)

    STATUS_HOME = 0
    STATUS_GAME = 1
    STATUS_DEAD = 2
    game_status = STATUS_HOME

    home_hint = my_font.render("Press any key to start.", False, (255, 255, 255))
    dead_hint = my_font.render("Press any key to restart.", False, (255, 255, 255))
    hh_last_blink = pygame.time.get_ticks()
    hh_visible = True

    while True:
        # Event handler
        event = pygame.event.poll()
        if event.type == QUIT:
            pygame.quit()
            exit()
        elif game_status == STATUS_HOME and (event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN):
            click_sound.play()
            game_status = STATUS_GAME
            # Game resources initiation
            score = 0
            score_hint = my_font.render("Score: %s" % score, False, (255, 255, 255))
            last_enemy_born_time = 0
            enemys = pygame.sprite.Group()
            enemys_dying = pygame.sprite.Group()
            enemy_speed = 0.08
            enemy_interval = 3000
            enemy_max = 3
            fire_interval = 400
            fireballs = pygame.sprite.Group()
            last_fireball_born_time = 0
            fireball_speed = 0.5
            player = Player(player_surf, explosion_surf)
        elif game_status == STATUS_DEAD and (event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN):
            click_sound.play()
            game_status = STATUS_HOME
            hh_visible = True
            hh_last_blink = pygame.time.get_ticks()
        # Draw
        if game_status == STATUS_HOME:
            if pygame.time.get_ticks() - hh_last_blink > 750:  # Hint blinking speed
                hh_visible = not hh_visible
                hh_last_blink = pygame.time.get_ticks()
            screen.blit(background_surf, (0, 0))
            screen.blit(logo_surf, (30, 60))
            if hh_visible:
                screen.blit(home_hint, (55, 380))
        elif game_status == STATUS_DEAD:
            if pygame.time.get_ticks() - hh_last_blink > 750:  # Hint blinking speed
                hh_visible = not hh_visible
                hh_last_blink = pygame.time.get_ticks()
            screen.blit(background_surf, (0, 0))
            screen.blit(gameover_surf, (20, 100))
            screen.blit(score_hint, (5, 5))
            if hh_visible:
                screen.blit(dead_hint, (45, 380))
        elif game_status == STATUS_GAME:
            current_time = pygame.time.get_ticks()
            mouse_pos = pygame.mouse.get_pos()
            screen.blit(background_surf, (0, 0))

            for obj in enemys.sprites():
                if obj.rect.y > 20 and pygame.sprite.spritecollide(obj, fireballs, True):
                    obj.health -= 100
                    if obj.health <= 0:
                        obj.set_dead()
                        enemys.remove(obj)
                        enemys_dying.add(obj)
                        score += obj.award
                        update_diff(score)
                        enemy_interval *= random_scale_factor()
                        score_sounds[random.randint(0, 2)].play()
            if current_time - last_enemy_born_time > enemy_interval:
                for i in range(random.randint(math.ceil(enemy_max // 2), enemy_max)):
                    seed = random.random()
                    if seed < 0.35:
                        enemys.add(Enemy(enemy_surfs[0], explosion_surf, enemy_speed * random_scale_factor(), 100, 10))
                    elif seed < 0.6:
                        enemys.add(Enemy(enemy_surfs[1], explosion_surf, enemy_speed * random_scale_factor(), 200, 20))
                    elif seed < 0.8:
                        enemys.add(Enemy(enemy_surfs[2], explosion_surf, enemy_speed * random_scale_factor(), 400, 40))
                    elif seed < 0.95:
                        enemys.add(Enemy(enemy_surfs[3], explosion_surf, enemy_speed * random_scale_factor(), 600, 50))
                    else:
                        enemys.add(
                            Enemy(enemy_surfs[4], explosion_surf, enemy_speed * random_scale_factor(), 1200, 100))
                last_enemy_born_time = current_time
                enemy_interval *= random_scale_factor()
            enemys.update(current_time)
            enemys.draw(screen)
            enemys_dying.update(current_time)
            enemys_dying.draw(screen)

            if current_time - last_fireball_born_time > fire_interval:
                fireballs.add(Fireball(fireball_surf, (mouse_pos[0], mouse_pos[1] - 15), fireball_speed))
                last_fireball_born_time = current_time
            fireballs.update(current_time)
            fireballs.draw(screen)

            for enemy in enemys.sprites():
                if pygame.sprite.collide_circle_ratio(0.7)(player, enemy):
                    player.set_dead()
                    dead_sound.play()
                    break
            player.update(mouse_pos, current_time)
            player.draw(screen)

            score_hint = my_font.render("Score: %s" % score, False, (255, 255, 255))
            screen.blit(score_hint, (5, 5))

            if not player.is_running:
                game_status = STATUS_DEAD
        # Update display
        pygame.display.update()
