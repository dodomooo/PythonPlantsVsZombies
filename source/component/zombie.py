__author__ = 'marble_xu'

import pygame as pg
from .. import tool
from .. import constants as c

class Zombie(pg.sprite.Sprite):
    _FRAME_CACHE = {}

    def __init__(self, x, y, name, health, head_group=None, damage=1):
        pg.sprite.Sprite.__init__(self)

        self.name = name
        self.frames = []
        self.frame_index = 0
        self.loadImages()
        self.frame_num = len(self.frames)

        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y

        self.health = health
        self.damage = damage
        self.dead = False
        self.losHead = False
        self.helmet = False
        self.head_group = head_group
        self.scored = False  # 是否已计分

        self.walk_timer = 0
        self.animate_timer = 0
        self.attack_timer = 0
        self.state = c.WALK
        self.animate_interval = 150
        self.ice_slow_ratio = 1
        self.ice_slow_timer = 0
        self.hit_timer = 0
        self.speed = c.scale(1)
        self.freeze_timer = 0
        self.is_hypno = False # the zombie is hypo and attack other zombies when it ate a HypnoShroom
        self._flip_cache = {}
        self._last_alpha = None
        self._last_image = None

        # 碰撞矩形：缩小碰撞区域，避免击中图片前面的空白
        # 必须在 is_hypno 初始化之后设置
        self.hitbox = self.rect.copy()
        self.hitbox_offset_x = c.scale(55)  # 向右偏移，跳过前面的空白
        self.hitbox_width_ratio = 0.6  # 碰撞区域宽度为原始宽度的 60%
        self.updateHitbox()
    
    def loadFrames(self, frames, name, image_x, colorkey=c.BLACK, scale=1):
        frame_list = tool.GFX[name]

        for frame in frame_list:
            rect = frame.get_rect()
            actual_w, actual_h = rect.w, rect.h

            # 检测是否为高清图片
            is_hd = (actual_w > c.HD_ZOMBIE_WIDTH_THRESHOLD or
                     actual_h > c.HD_ZOMBIE_HEIGHT_THRESHOLD)

            if is_hd:
                # 计算高清图的像素比例，按比例缩放裁剪参数
                hd_ratio = actual_w / c.BASE_ZOMBIE_REF_WIDTH
                scaled_x = int(image_x * hd_ratio)
                crop_width = actual_w - scaled_x

                # 目标尺寸与低清图一致：(原始宽度 - image_x) × 原始高度 × ASSET_SCALE
                target_width = int((c.BASE_ZOMBIE_REF_WIDTH - image_x) * c.ASSET_SCALE)
                target_height = int(c.BASE_ZOMBIE_REF_HEIGHT * c.ASSET_SCALE)

                # 裁剪并缩放到目标尺寸
                frames.append(tool.get_image_fit(
                    frame, scaled_x, 0, crop_width, actual_h, colorkey,
                    target_width=target_width, target_height=target_height
                ))
            else:
                # 低清图使用原有逻辑
                width = actual_w - image_x
                frames.append(tool.get_image(frame, image_x, 0, width, actual_h, colorkey))

    def update(self, game_info):
        self.current_time = game_info[c.CURRENT_TIME]
        self.handleState()
        self.updateIceSlow()
        self.animation()
        self.updateHitbox()

    def handleState(self):
        if self.state == c.WALK:
            self.walking()
        elif self.state == c.ATTACK:
            self.attacking()
        elif self.state == c.DIE:
            self.dying()
        elif self.state == c.FREEZE:
            self.freezing()

    def walking(self):
        if self.health <= 0:
            self.setDie()
        elif self.health <= c.LOSTHEAD_HEALTH and not self.losHead:
            self.changeFrames(self.losthead_walk_frames)
            self.setLostHead()
        elif self.health <= c.NORMAL_HEALTH and self.helmet:
            self.changeFrames(self.walk_frames)
            self.helmet = False
            if self.name == c.NEWSPAPER_ZOMBIE:
                self.speed = c.scale(2)

        if (self.current_time - self.walk_timer) > (c.ZOMBIE_WALK_INTERVAL * self.getTimeRatio()):
            self.walk_timer = self.current_time
            if self.is_hypno:
                self.rect.x += self.speed
            else:
                self.rect.x -= self.speed
    
    def attacking(self):
        if self.health <= 0:
            self.setDie()
        elif self.health <= c.LOSTHEAD_HEALTH and not self.losHead:
            self.changeFrames(self.losthead_attack_frames)
            self.setLostHead()
        elif self.health <= c.NORMAL_HEALTH and self.helmet:
            self.changeFrames(self.attack_frames)
            self.helmet = False
        if (self.current_time - self.attack_timer) > (c.ATTACK_INTERVAL * self.getTimeRatio()):
            if self.prey.health > 0:
                if self.prey_is_plant:
                    self.prey.setDamage(self.damage, self)
                else:
                    self.prey.setDamage(self.damage)
            self.attack_timer = self.current_time

        if self.prey.health <= 0:
            self.prey = None
            self.setWalk()
    
    def dying(self):
        pass

    def freezing(self):
        if self.health <= 0:
            self.setDie()
        elif self.health <= c.LOSTHEAD_HEALTH and not self.losHead:
            if self.old_state == c.WALK:
                self.changeFrames(self.losthead_walk_frames)
            else:
                self.changeFrames(self.losthead_attack_frames)
            self.setLostHead()
        if (self.current_time - self.freeze_timer) > c.FREEZE_TIME:
            self.setWalk()

    def setLostHead(self):
        self.losHead = True
        if self.head_group is not None:
            self.head_group.add(ZombieHead(self.rect.centerx, self.rect.bottom))

    def changeFrames(self, frames):
        '''change image frames and modify rect position'''
        self.frames = self._get_frames(frames)
        self.frame_num = len(self.frames)
        self.frame_index = 0
        
        bottom = self.rect.bottom
        centerx = self.rect.centerx
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.bottom = bottom
        self.rect.centerx = centerx

    def animation(self):
        if self.state == c.FREEZE:
            target_alpha = 192
            if self.image is not self._last_image or target_alpha != self._last_alpha:
                self.image.set_alpha(target_alpha)
                self._last_image = self.image
                self._last_alpha = target_alpha
            return

        if (self.current_time - self.animate_timer) > (self.animate_interval * self.getTimeRatio()):
            self.frame_index += 1
            if self.frame_index >= self.frame_num:
                if self.state == c.DIE:
                    self.kill()
                    return
                self.frame_index = 0
            self.animate_timer = self.current_time

        self.image = self.frames[self.frame_index]
        target_alpha = 255 if (self.current_time - self.hit_timer) >= 200 else 192
        if self.image is not self._last_image or target_alpha != self._last_alpha:
            self.image.set_alpha(target_alpha)
            self._last_image = self.image
            self._last_alpha = target_alpha

    def getTimeRatio(self):
        return self.ice_slow_ratio

    def setIceSlow(self):
        '''when get a ice bullet damage, slow the attack or walk speed of the zombie'''
        self.ice_slow_timer = self.current_time
        self.ice_slow_ratio = 2

    def updateIceSlow(self):
        if self.ice_slow_ratio > 1:
            if (self.current_time - self.ice_slow_timer) > c.ICE_SLOW_TIME:
                self.ice_slow_ratio = 1

    def updateHitbox(self):
        '''更新碰撞矩形位置，使其跟随僵尸移动'''
        if self.is_hypno:
            # 被催眠的僵尸向右移动，hitbox 在左侧
            self.hitbox.right = self.rect.right - self.hitbox_offset_x
        else:
            # 正常僵尸向左移动，hitbox 在右侧（跳过前面的空白）
            self.hitbox.left = self.rect.left + self.hitbox_offset_x
        self.hitbox.width = int(self.rect.width * self.hitbox_width_ratio)
        self.hitbox.centery = self.rect.centery

    def setDamage(self, damage, ice=False):
        self.health -= damage
        self.hit_timer = self.current_time
        if ice:
            self.setIceSlow()
    
    def setWalk(self):
        self.state = c.WALK
        self.animate_interval = 150
        
        if self.helmet:
            self.changeFrames(self.helmet_walk_frames)
        elif self.losHead:
            self.changeFrames(self.losthead_walk_frames)
        else:
            self.changeFrames(self.walk_frames)

    def setAttack(self, prey, is_plant=True):
        self.prey = prey  # prey can be plant or other zombies
        self.prey_is_plant = is_plant
        self.state = c.ATTACK
        self.attack_timer = self.current_time
        self.animate_interval = 100
        
        if self.helmet:
            self.changeFrames(self.helmet_attack_frames)
        elif self.losHead:
            self.changeFrames(self.losthead_attack_frames)
        else:
            self.changeFrames(self.attack_frames)
    
    def setDie(self):
        self.state = c.DIE
        self.animate_interval = 200
        self.changeFrames(self.die_frames)
    
    def setBoomDie(self):
        self.state = c.DIE
        self.animate_interval = 200
        self.changeFrames(self.boomdie_frames)

    def setFreeze(self, ice_trap_image):
        self.old_state = self.state
        self.state = c.FREEZE
        self.freeze_timer = self.current_time
        self.ice_trap_image = ice_trap_image
        self.ice_trap_rect = ice_trap_image.get_rect()
        self.ice_trap_rect.centerx = self.rect.centerx
        self.ice_trap_rect.bottom = self.rect.bottom

    def drawFreezeTrap(self, surface):
        if self.state == c.FREEZE:
            surface.blit(self.ice_trap_image, self.ice_trap_rect)

    def setHypno(self):
        self.is_hypno = True
        self.setWalk()

    def _get_frames(self, frames):
        if not self.is_hypno:
            return frames
        cached = self._flip_cache.get(id(frames))
        if cached is None:
            cached = [pg.transform.flip(frame, True, False) for frame in frames]
            self._flip_cache[id(frames)] = cached
        return cached

class ZombieHead(Zombie):
    def __init__(self, x, y):
        Zombie.__init__(self, x, y, c.ZOMBIE_HEAD, 0)
        self.state = c.DIE
    
    def loadImages(self):
        cache = Zombie._FRAME_CACHE.get(self.__class__)
        if cache:
            self.die_frames = cache['die_frames']
            self.frames = self.die_frames
            return

        self.die_frames = []
        die_name =  self.name
        self.loadFrames(self.die_frames, die_name, 0)
        self.frames = self.die_frames
        Zombie._FRAME_CACHE[self.__class__] = {
            'die_frames': self.die_frames
        }

    def setWalk(self):
        self.animate_interval = 100

class NormalZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.NORMAL_ZOMBIE, c.NORMAL_HEALTH, head_group)

    def loadImages(self):
        cache = Zombie._FRAME_CACHE.get(self.__class__)
        if cache:
            self.walk_frames = cache['walk_frames']
            self.attack_frames = cache['attack_frames']
            self.losthead_walk_frames = cache['losthead_walk_frames']
            self.losthead_attack_frames = cache['losthead_attack_frames']
            self.die_frames = cache['die_frames']
            self.boomdie_frames = cache['boomdie_frames']
            self.frames = self.walk_frames
            return

        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        walk_name = self.name
        attack_name = self.name + 'Attack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name =  self.name + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]
        
        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'])

        self.frames = self.walk_frames
        Zombie._FRAME_CACHE[self.__class__] = {
            'walk_frames': self.walk_frames,
            'attack_frames': self.attack_frames,
            'losthead_walk_frames': self.losthead_walk_frames,
            'losthead_attack_frames': self.losthead_attack_frames,
            'die_frames': self.die_frames,
            'boomdie_frames': self.boomdie_frames
        }

class ConeHeadZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.CONEHEAD_ZOMBIE, c.CONEHEAD_HEALTH, head_group)
        self.helmet = True

    def loadImages(self):
        cache = Zombie._FRAME_CACHE.get(self.__class__)
        if cache:
            self.helmet_walk_frames = cache['helmet_walk_frames']
            self.helmet_attack_frames = cache['helmet_attack_frames']
            self.walk_frames = cache['walk_frames']
            self.attack_frames = cache['attack_frames']
            self.losthead_walk_frames = cache['losthead_walk_frames']
            self.losthead_attack_frames = cache['losthead_attack_frames']
            self.die_frames = cache['die_frames']
            self.boomdie_frames = cache['boomdie_frames']
            self.frames = self.helmet_walk_frames
            return

        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []
        
        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.NORMAL_ZOMBIE
        attack_name = c.NORMAL_ZOMBIE + 'Attack'
        losthead_walk_name = c.NORMAL_ZOMBIE + 'LostHead'
        losthead_attack_name = c.NORMAL_ZOMBIE + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]
        
        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'])

        self.frames = self.helmet_walk_frames
        Zombie._FRAME_CACHE[self.__class__] = {
            'helmet_walk_frames': self.helmet_walk_frames,
            'helmet_attack_frames': self.helmet_attack_frames,
            'walk_frames': self.walk_frames,
            'attack_frames': self.attack_frames,
            'losthead_walk_frames': self.losthead_walk_frames,
            'losthead_attack_frames': self.losthead_attack_frames,
            'die_frames': self.die_frames,
            'boomdie_frames': self.boomdie_frames
        }

class BucketHeadZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.BUCKETHEAD_ZOMBIE, c.BUCKETHEAD_HEALTH, head_group)
        self.helmet = True

    def loadImages(self):
        cache = Zombie._FRAME_CACHE.get(self.__class__)
        if cache:
            self.helmet_walk_frames = cache['helmet_walk_frames']
            self.helmet_attack_frames = cache['helmet_attack_frames']
            self.walk_frames = cache['walk_frames']
            self.attack_frames = cache['attack_frames']
            self.losthead_walk_frames = cache['losthead_walk_frames']
            self.losthead_attack_frames = cache['losthead_attack_frames']
            self.die_frames = cache['die_frames']
            self.boomdie_frames = cache['boomdie_frames']
            self.frames = self.helmet_walk_frames
            return

        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = c.NORMAL_ZOMBIE
        attack_name = c.NORMAL_ZOMBIE + 'Attack'
        losthead_walk_name = c.NORMAL_ZOMBIE + 'LostHead'
        losthead_attack_name = c.NORMAL_ZOMBIE + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]
        
        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'])

        self.frames = self.helmet_walk_frames
        Zombie._FRAME_CACHE[self.__class__] = {
            'helmet_walk_frames': self.helmet_walk_frames,
            'helmet_attack_frames': self.helmet_attack_frames,
            'walk_frames': self.walk_frames,
            'attack_frames': self.attack_frames,
            'losthead_walk_frames': self.losthead_walk_frames,
            'losthead_attack_frames': self.losthead_attack_frames,
            'die_frames': self.die_frames,
            'boomdie_frames': self.boomdie_frames
        }

class FlagZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.FLAG_ZOMBIE, c.FLAG_HEALTH, head_group)
    
    def loadImages(self):
        cache = Zombie._FRAME_CACHE.get(self.__class__)
        if cache:
            self.walk_frames = cache['walk_frames']
            self.attack_frames = cache['attack_frames']
            self.losthead_walk_frames = cache['losthead_walk_frames']
            self.losthead_attack_frames = cache['losthead_attack_frames']
            self.die_frames = cache['die_frames']
            self.boomdie_frames = cache['boomdie_frames']
            self.frames = self.walk_frames
            return

        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        walk_name = self.name
        attack_name = self.name + 'Attack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name = c.NORMAL_ZOMBIE + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]
        
        for i, name in enumerate(name_list):
            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'])

        self.frames = self.walk_frames
        Zombie._FRAME_CACHE[self.__class__] = {
            'walk_frames': self.walk_frames,
            'attack_frames': self.attack_frames,
            'losthead_walk_frames': self.losthead_walk_frames,
            'losthead_attack_frames': self.losthead_attack_frames,
            'die_frames': self.die_frames,
            'boomdie_frames': self.boomdie_frames
        }

class NewspaperZombie(Zombie):
    def __init__(self, x, y, head_group):
        Zombie.__init__(self, x, y, c.NEWSPAPER_ZOMBIE, c.NEWSPAPER_HEALTH, head_group)
        self.helmet = True

    def loadImages(self):
        cache = Zombie._FRAME_CACHE.get(self.__class__)
        if cache:
            self.helmet_walk_frames = cache['helmet_walk_frames']
            self.helmet_attack_frames = cache['helmet_attack_frames']
            self.walk_frames = cache['walk_frames']
            self.attack_frames = cache['attack_frames']
            self.losthead_walk_frames = cache['losthead_walk_frames']
            self.losthead_attack_frames = cache['losthead_attack_frames']
            self.die_frames = cache['die_frames']
            self.boomdie_frames = cache['boomdie_frames']
            self.frames = self.helmet_walk_frames
            return

        self.helmet_walk_frames = []
        self.helmet_attack_frames = []
        self.walk_frames = []
        self.attack_frames = []
        self.losthead_walk_frames = []
        self.losthead_attack_frames = []
        self.die_frames = []
        self.boomdie_frames = []

        helmet_walk_name = self.name
        helmet_attack_name = self.name + 'Attack'
        walk_name = self.name + 'NoPaper'
        attack_name = self.name + 'NoPaperAttack'
        losthead_walk_name = self.name + 'LostHead'
        losthead_attack_name = self.name + 'LostHeadAttack'
        die_name = self.name + 'Die'
        boomdie_name = c.BOOMDIE

        frame_list = [self.helmet_walk_frames, self.helmet_attack_frames,
                      self.walk_frames, self.attack_frames, self.losthead_walk_frames,
                      self.losthead_attack_frames, self.die_frames, self.boomdie_frames]
        name_list = [helmet_walk_name, helmet_attack_name,
                     walk_name, attack_name, losthead_walk_name,
                     losthead_attack_name, die_name, boomdie_name]

        for i, name in enumerate(name_list):
            # NewspaperZombie 和 NewspaperZombieAttack 是透明背景，使用 BLACK
            # 其他状态（无报纸、失头、死亡）是白色背景，使用 WHITE
            if name in [c.NEWSPAPER_ZOMBIE, c.NEWSPAPER_ZOMBIE + 'Attack', c.BOOMDIE]:
                color = c.BLACK
            else:
                color = c.WHITE

            # 带报纸的状态缩放为 0.85
            if name in [c.NEWSPAPER_ZOMBIE, c.NEWSPAPER_ZOMBIE + 'Attack']:
                scale = 0.85
            else:
                scale = 1

            self.loadFrames(frame_list[i], name, tool.ZOMBIE_RECT[name]['x'], color, scale)

        self.frames = self.helmet_walk_frames
        Zombie._FRAME_CACHE[self.__class__] = {
            'helmet_walk_frames': self.helmet_walk_frames,
            'helmet_attack_frames': self.helmet_attack_frames,
            'walk_frames': self.walk_frames,
            'attack_frames': self.attack_frames,
            'losthead_walk_frames': self.losthead_walk_frames,
            'losthead_attack_frames': self.losthead_attack_frames,
            'die_frames': self.die_frames,
            'boomdie_frames': self.boomdie_frames
        }
