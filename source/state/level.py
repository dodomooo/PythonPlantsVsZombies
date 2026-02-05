__author__ = 'marble_xu'

import os
import json
import random
import pygame as pg
from .. import tool
from .. import constants as c
from ..component import map, plant, zombie, menubar


class CrazyModeSpawner:
    """疯狂模式僵尸动态生成器"""

    def __init__(self, config, map_y_len):
        """
        Args:
            config: 生成配置，包含：
                - initial_interval: 初始生成间隔（毫秒）
                - min_interval: 最小生成间隔（毫秒）
                - interval_decrease_rate: 间隔递减率
                - spawn_probability: 各类僵尸生成概率字典
            map_y_len: 地图行数
        """
        self.current_interval = config['initial_interval']
        self.min_interval = config['min_interval']
        self.decrease_rate = config['interval_decrease_rate']
        self.spawn_prob = config['spawn_probability']
        self.last_spawn_time = 0
        self.map_y_len = map_y_len

    def should_spawn(self, current_time):
        """
        检查是否应该生成僵尸
        Args:
            current_time: 当前游戏时间（毫秒）
        Returns:
            bool: 如果应该生成僵尸返回 True
        """
        if current_time - self.last_spawn_time >= self.current_interval:
            self.last_spawn_time = current_time
            # 逐渐缩短生成间隔
            self.current_interval = max(
                self.min_interval,
                int(self.current_interval * self.decrease_rate)
            )
            return True
        return False

    def get_zombie_type(self):
        """
        根据概率随机选择僵尸类型
        Returns:
            str: 僵尸类型名称
        """
        rand = random.random()
        cumulative = 0
        for zombie_type, prob in self.spawn_prob.items():
            cumulative += prob
            if rand <= cumulative:
                return zombie_type
        # 如果没有匹配到（概率和不为1的情况），返回普通僵尸
        return c.NORMAL_ZOMBIE

    def get_random_map_y(self):
        """
        随机选择一个地图行
        Returns:
            int: 地图行索引（0 到 map_y_len-1）
        """
        return random.randint(0, self.map_y_len - 1)


class Level(tool.State):
    def __init__(self):
        tool.State.__init__(self)
    
    def startup(self, current_time, persist):
        import time
        t0 = time.time()
        self.game_info = persist
        self.persist = self.game_info
        self.game_info[c.CURRENT_TIME] = current_time
        self.map_y_len = c.GRID_Y_LEN
        self.map = map.Map(c.GRID_X_LEN, self.map_y_len)
        self._collide_ratio = {
            0.6: pg.sprite.collide_circle_ratio(0.6),
            0.7: pg.sprite.collide_circle_ratio(0.7),
            0.8: pg.sprite.collide_circle_ratio(0.8)
        }

        t1 = time.time()
        self.loadMap()
        t2 = time.time()
        self.setupBackground()
        t3 = time.time()
        self.initState()
        t4 = time.time()
        print(f'[DEBUG] Level.startup: map={t1-t0:.3f}s, loadMap={t2-t1:.3f}s, setupBg={t3-t2:.3f}s, initState={t4-t3:.3f}s')

    def loadMap(self):
        map_file = 'level_' + str(self.game_info[c.LEVEL_NUM]) + '.json'
        file_path = os.path.join('source', 'data', 'map', map_file)
        f = open(file_path)
        self.map_data = json.load(f)
        f.close()
    
    def setupBackground(self):
        img_index = self.map_data[c.BACKGROUND_TYPE]
        self.background_type = img_index
        bg = tool.GFX[c.BACKGROUND_NAME][img_index]

        # 检测是否为高清背景图
        actual_w, actual_h = bg.get_width(), bg.get_height()
        is_hd = (actual_w > c.HD_BACKGROUND_WIDTH_THRESHOLD or
                 actual_h > c.HD_BACKGROUND_HEIGHT_THRESHOLD)

        if is_hd:
            # 高清图：缩放到与低清图相同的目标尺寸
            target_width = int(c.BASE_BACKGROUND_REF_WIDTH * c.ASSET_SCALE)
            target_height = int(c.BASE_BACKGROUND_REF_HEIGHT * c.ASSET_SCALE)
            self.background = pg.transform.smoothscale(bg, (target_width, target_height))
        elif c.ASSET_SCALE != 1:
            # 低清图：按 ASSET_SCALE 缩放
            self.background = pg.transform.scale(
                bg,
                (int(bg.get_width() * c.ASSET_SCALE), int(bg.get_height() * c.ASSET_SCALE))
            )
        else:
            self.background = bg
        self.bg_rect = self.background.get_rect()

        self.level = pg.Surface((self.bg_rect.w, self.bg_rect.h)).convert()
        self.viewport = tool.SCREEN.get_rect(bottom=self.bg_rect.bottom)
        self.viewport.x += c.BACKGROUND_OFFSET_X
    
    def setupGroups(self):
        self.sun_group = pg.sprite.Group()
        self.head_group = pg.sprite.Group()

        self.plant_groups = []
        self.zombie_groups = []
        self.hypno_zombie_groups = [] #zombies who are hypno after eating hypnoshroom
        self.bullet_groups = []
        for i in range(self.map_y_len):
            self.plant_groups.append(pg.sprite.Group())
            self.zombie_groups.append(pg.sprite.Group())
            self.hypno_zombie_groups.append(pg.sprite.Group())
            self.bullet_groups.append(pg.sprite.Group())
    
    def setupZombies(self):
        def takeTime(element):
            return element[0]

        self.zombie_list = []
        for data in self.map_data[c.ZOMBIE_LIST]:
            self.zombie_list.append((data['time'], data['name'], data['map_y']))
        self.zombie_start_time = 0
        self.zombie_list.sort(key=takeTime)

    def setupCars(self):
        self.cars = []
        for i in range(self.map_y_len):
            _, y = self.map.getMapGridPos(0, i)
            self.cars.append(plant.Car(-c.scale(25), y - c.scale(20), i))

    def update(self, surface, current_time, mouse_pos, mouse_click, events, mouse_hover_pos=None):
        self.current_time = self.game_info[c.CURRENT_TIME] = current_time

        # 检测 ESC 键，重新开始游戏
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                if getattr(self, 'drag_plant', False):
                    self.removeMouseImage()
                self.next = c.LOGIN_SCREEN
                self.done = True
                return

        if self.state == c.CHOOSE:
            self.choose(mouse_pos, mouse_click, mouse_hover_pos)
        elif self.state == c.PLAY:
            self.play(mouse_pos, mouse_click, mouse_hover_pos)

        self.draw(surface)

    def initBowlingMap(self):
        print('initBowlingMap')
        for x in range(3, self.map.width):
            for y in range(self.map.height):
                self.map.setMapGridType(x, y, c.MAP_EXIST)

    def initState(self):
        if c.CHOOSEBAR_TYPE in self.map_data:
            self.bar_type = self.map_data[c.CHOOSEBAR_TYPE]
        else:
            self.bar_type = c.CHOOSEBAR_STATIC

        if self.bar_type == c.CHOOSEBAR_STATIC:
            self.initChoose()
        else:
            card_pool = menubar.getCardPool(self.map_data[c.CARD_POOL])
            self.initPlay(card_pool)
            if self.bar_type == c.CHOSSEBAR_BOWLING:
                self.initBowlingMap()

    def initChoose(self):
        self.state = c.CHOOSE
        # 从关卡数据中提取僵尸类型列表
        zombie_types = []
        # 首先尝试从 zombie_list 获取
        for data in self.map_data.get(c.ZOMBIE_LIST, []):
            zombie_types.append(data['name'])
        # 如果 zombie_list 为空，尝试从 zombie_spawn_config 获取
        if not zombie_types:
            spawn_config = self.map_data.get('zombie_spawn_config', {})
            spawn_prob = spawn_config.get('spawn_probability', {})
            zombie_types = list(spawn_prob.keys())
        self.panel = menubar.Panel(menubar.all_card_list, self.map_data[c.INIT_SUN_NAME], zombie_types)

    def choose(self, mouse_pos, mouse_click, mouse_hover_pos=None):
        if mouse_pos and mouse_click[0]:
            self.panel.checkCardClick(mouse_pos)
            if self.panel.checkStartButtonClick(mouse_pos):
                self.initPlay(self.panel.getSelectedCards())
        self.panel.update(self.current_time, mouse_hover_pos)

    def initPlay(self, card_list):
        self.state = c.PLAY
        if self.bar_type == c.CHOOSEBAR_STATIC:
            self.menubar = menubar.MenuBar(card_list, self.map_data[c.INIT_SUN_NAME])
        else:
            self.menubar = menubar.MoveBar(card_list)
        self.drag_plant = False
        self.hint_image = None
        self.hint_plant = False
        if self.background_type == c.BACKGROUND_DAY and self.bar_type == c.CHOOSEBAR_STATIC:
            self.produce_sun = True
        else:
            self.produce_sun = False
        self.sun_timer = self.current_time

        # 积分系统
        self.score = 0
        self.zombies_killed = {
            c.NORMAL_ZOMBIE: 0,
            c.CONEHEAD_ZOMBIE: 0,
            c.BUCKETHEAD_ZOMBIE: 0,
            c.FLAG_ZOMBIE: 0,
            c.NEWSPAPER_ZOMBIE: 0
        }

        # 检查是否是疯狂模式
        self.is_crazy_mode = self.map_data.get('game_mode') == c.GAME_MODE_CRAZY
        if self.is_crazy_mode:
            self.game_duration = self.map_data.get('game_duration', c.CRAZY_MODE_DURATION)
            self.crazy_start_time = 0
            # 初始化疯狂模式生成器
            spawn_config = self.map_data.get('zombie_spawn_config', {
                'initial_interval': 3000,
                'min_interval': 1000,
                'interval_decrease_rate': 0.95,
                'spawn_probability': {
                    c.NORMAL_ZOMBIE: 0.4,
                    c.CONEHEAD_ZOMBIE: 0.25,
                    c.BUCKETHEAD_ZOMBIE: 0.15,
                    c.FLAG_ZOMBIE: 0.1,
                    c.NEWSPAPER_ZOMBIE: 0.1
                }
            })
            self.crazy_spawner = CrazyModeSpawner(spawn_config, self.map_y_len)

        self.removeMouseImage()
        self.setupGroups()
        self.setupZombies()
        self.setupCars()

    def play(self, mouse_pos, mouse_click, mouse_hover_pos=None):
        # 僵尸生成逻辑
        if self.zombie_start_time == 0:
            self.zombie_start_time = self.current_time
            if self.is_crazy_mode:
                self.crazy_start_time = self.current_time
        elif self.is_crazy_mode:
            # 疯狂模式：使用动态生成器
            if self.crazy_spawner.should_spawn(self.current_time):
                zombie_type = self.crazy_spawner.get_zombie_type()
                map_y = self.crazy_spawner.get_random_map_y()
                self.createZombie(zombie_type, map_y)
        elif len(self.zombie_list) > 0:
            # 普通模式：使用预定义列表
            data = self.zombie_list[0]
            if data[0] <= (self.current_time - self.zombie_start_time):
                self.createZombie(data[1], data[2])
                self.zombie_list.remove(data)

        for i in range(self.map_y_len):
            self.bullet_groups[i].update(self.game_info)
            self.plant_groups[i].update(self.game_info)
            self.zombie_groups[i].update(self.game_info)
            self.hypno_zombie_groups[i].update(self.game_info)
            for zombie in self.hypno_zombie_groups[i]:
                if zombie.rect.x > c.SCREEN_WIDTH:
                    zombie.kill()

        self.head_group.update(self.game_info)
        self.sun_group.update(self.game_info)
        
        if not self.drag_plant and mouse_pos and mouse_click[0]:
            result = self.menubar.checkCardClick(mouse_pos)
            if result:
                self.setupMouseImage(result[0], result[1])
        elif self.drag_plant:
            if mouse_click[1]:
                self.removeMouseImage()
            elif mouse_click[0]:
                if self.menubar.checkMenuBarClick(mouse_pos):
                    self.removeMouseImage()
                else:
                    self.addPlant()
            elif mouse_pos is None:
                self.setupHintImage()
        
        if self.produce_sun:
            if(self.current_time - self.sun_timer) > c.PRODUCE_SUN_INTERVAL:
                self.sun_timer = self.current_time
                map_x, map_y = self.map.getRandomMapIndex()
                x, y = self.map.getMapGridPos(map_x, map_y)
                self.sun_group.add(plant.Sun(x, 0, x, y))
        if not self.drag_plant and mouse_pos and mouse_click[0]:
            for sun in self.sun_group:
                if sun.checkCollision(mouse_pos[0], mouse_pos[1]):
                    self.menubar.increaseSunValue(sun.sun_value)

        for car in self.cars:
            car.update(self.game_info)

        self.menubar.update(self.current_time, mouse_hover_pos)

        self.checkBulletCollisions()
        self.checkZombieCollisions()
        self.checkPlants()
        self.checkCarCollisions()
        self.checkZombieKills()  # 检查僵尸击杀并计分
        self.checkGameState()

    def createZombie(self, name, map_y):
        x, y = self.map.getMapGridPos(0, map_y)
        if name == c.NORMAL_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.NormalZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.CONEHEAD_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.ConeHeadZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.BUCKETHEAD_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.BucketHeadZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.FLAG_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.FlagZombie(c.ZOMBIE_START_X, y, self.head_group))
        elif name == c.NEWSPAPER_ZOMBIE:
            self.zombie_groups[map_y].add(zombie.NewspaperZombie(c.ZOMBIE_START_X, y, self.head_group))

    def canSeedPlant(self):
        x, y = pg.mouse.get_pos()
        return self.map.showPlant(x, y)
        
    def addPlant(self):
        pos = self.canSeedPlant()
        if pos is None:
            return

        if self.hint_image is None:
            self.setupHintImage()
        x, y = self.hint_rect.centerx, self.hint_rect.bottom
        map_x, map_y = self.map.getMapIndex(x, y)
        if self.plant_name == c.SUNFLOWER:
            new_plant = plant.SunFlower(x, y, self.sun_group)
        elif self.plant_name == c.PEASHOOTER:
            new_plant = plant.PeaShooter(x, y, self.bullet_groups[map_y])
        elif self.plant_name == c.SNOWPEASHOOTER:
            new_plant = plant.SnowPeaShooter(x, y, self.bullet_groups[map_y])
        elif self.plant_name == c.WALLNUT:
            new_plant = plant.WallNut(x, y)
        elif self.plant_name == c.CHERRYBOMB:
            new_plant = plant.CherryBomb(x, y)
        elif self.plant_name == c.THREEPEASHOOTER:
            new_plant = plant.ThreePeaShooter(x, y, self.bullet_groups, map_y)
        elif self.plant_name == c.REPEATERPEA:
            new_plant = plant.RepeaterPea(x, y, self.bullet_groups[map_y])
        elif self.plant_name == c.CHOMPER:
            new_plant = plant.Chomper(x, y)
        elif self.plant_name == c.PUFFSHROOM:
            new_plant = plant.PuffShroom(x, y, self.bullet_groups[map_y])
        elif self.plant_name == c.POTATOMINE:
            new_plant = plant.PotatoMine(x, y)
        elif self.plant_name == c.SQUASH:
            new_plant = plant.Squash(x, y)
        elif self.plant_name == c.SPIKEWEED:
            new_plant = plant.Spikeweed(x, y)
        elif self.plant_name == c.JALAPENO:
            new_plant = plant.Jalapeno(x, y)
        elif self.plant_name == c.SCAREDYSHROOM:
            new_plant = plant.ScaredyShroom(x, y, self.bullet_groups[map_y])
        elif self.plant_name == c.SUNSHROOM:
            new_plant = plant.SunShroom(x, y, self.sun_group)
        elif self.plant_name == c.ICESHROOM:
            new_plant = plant.IceShroom(x, y)
        elif self.plant_name == c.HYPNOSHROOM:
            new_plant = plant.HypnoShroom(x, y)
        elif self.plant_name == c.WALLNUTBOWLING:
            new_plant = plant.WallNutBowling(x, y, map_y, self)
        elif self.plant_name == c.REDWALLNUTBOWLING:
            new_plant = plant.RedWallNutBowling(x, y)

        if new_plant.can_sleep and self.background_type == c.BACKGROUND_DAY:
            new_plant.setSleep()
        self.plant_groups[map_y].add(new_plant)
        if self.bar_type == c.CHOOSEBAR_STATIC:
            self.menubar.decreaseSunValue(self.select_plant.sun_cost)
            self.menubar.setCardFrozenTime(self.plant_name)
        else:
            self.menubar.deleateCard(self.select_plant)

        if self.bar_type != c.CHOSSEBAR_BOWLING:
            self.map.setMapGridType(map_x, map_y, c.MAP_EXIST)
        self.removeMouseImage()
        #print('addPlant map[%d,%d], grid pos[%d, %d] pos[%d, %d]' % (map_x, map_y, x, y, pos[0], pos[1]))

    def setupHintImage(self):
        pos = self.canSeedPlant()
        if pos and self.mouse_image:
            if (self.hint_image and pos[0] == self.hint_rect.x and
                pos[1] == self.hint_rect.y):
                return
            width, height = self.mouse_rect.w, self.mouse_rect.h
            image = pg.Surface([width, height])
            image.blit(self.mouse_image, (0, 0), (0, 0, width, height))
            image.set_colorkey(c.BLACK)
            image.set_alpha(128)
            self.hint_image = image
            self.hint_rect = image.get_rect()
            self.hint_rect.centerx = pos[0]
            self.hint_rect.bottom = pos[1]
            self.hint_plant = True
        else:
            self.hint_plant = False

    def setupMouseImage(self, plant_name, select_plant):
        frame_list = tool.GFX[plant_name]
        if plant_name in tool.PLANT_RECT:
            data = tool.PLANT_RECT[plant_name]
            x, y, width, height = data['x'], data['y'], data['width'], data['height']
        else:
            x, y = 0, 0
            min_w = min(f.get_rect().w for f in frame_list)
            min_h = min(f.get_rect().h for f in frame_list)
            width, height = min_w, min_h

        if (plant_name == c.SCAREDYSHROOM or plant_name == c.SUNSHROOM or
            plant_name == c.ICESHROOM or plant_name == c.HYPNOSHROOM or
            plant_name == c.WALLNUTBOWLING or plant_name == c.REDWALLNUTBOWLING):
            color = c.WHITE
        else:
            color = c.BLACK

        # 为倭瓜和食人花设置缩放比例
        if plant_name == c.SQUASH:
            scale = 0.5
        elif plant_name == c.CHOMPER:
            scale = 0.85
        elif plant_name == c.SNOWPEASHOOTER:
            scale = 0.95
        elif plant_name == c.PEASHOOTER:
            scale = 0.95
        elif plant_name == c.REPEATERPEA:
            scale = 1.1
        elif plant_name == c.WALLNUT:
            scale = 1.1
        elif plant_name == c.SUNFLOWER:
            scale = 0.88
        elif plant_name == c.THREEPEASHOOTER:
            scale = 0.85
        elif plant_name == c.CHERRYBOMB:
            scale = 0.85
        elif plant_name == c.POTATOMINE:
            scale = 1
        elif plant_name == c.SPIKEWEED:
            scale = 1
        elif plant_name == c.JALAPENO:
            scale = 1
        else:
            scale = 0.75

        frame = frame_list[0]
        actual_rect = frame.get_rect()
        actual_w, actual_h = actual_rect.w, actual_rect.h
        expected_w = x + width
        expected_h = y + height
        is_hd = (actual_w > expected_w * 2 or actual_h > expected_h * 2)

        if is_hd:
            hd_ratio = actual_w / expected_w if expected_w > 0 else 1
            scaled_x = int(x * hd_ratio)
            scaled_y = int(y * hd_ratio)
            crop_width = int(width * hd_ratio)
            crop_height = int(height * hd_ratio)
            target_width = int(width * scale * c.ASSET_SCALE)
            target_height = int(height * scale * c.ASSET_SCALE)
            self.mouse_image = tool.get_image_fit(
                frame, scaled_x, scaled_y, crop_width, crop_height, color,
                target_width=target_width, target_height=target_height)
        else:
            self.mouse_image = tool.get_image(frame, x, y, width, height, color, scale)
        self.mouse_rect = self.mouse_image.get_rect()
        pg.mouse.set_visible(False)
        self.drag_plant = True
        self.plant_name = plant_name
        self.select_plant = select_plant

    def removeMouseImage(self):
        pg.mouse.set_visible(True)
        self.drag_plant = False
        self.mouse_image = None
        self.hint_image = None
        self.hint_plant = False

    def checkBulletCollisions(self):
        collided_func = self._collide_ratio[0.7]
        for i in range(self.map_y_len):
            if len(self.zombie_groups[i]) == 0:
                continue
            for bullet in self.bullet_groups[i]:
                if bullet.state == c.FLY:
                    zombie = pg.sprite.spritecollideany(bullet, self.zombie_groups[i], collided_func)
                    if zombie and zombie.state != c.DIE:
                        zombie.setDamage(bullet.damage, bullet.ice)
                        bullet.setExplode()
    
    def checkZombieCollisions(self):
        if self.bar_type == c.CHOSSEBAR_BOWLING:
            ratio = 0.6
        else:
            ratio = 0.7
        collided_func = self._collide_ratio[ratio]
        for i in range(self.map_y_len):
            plants = self.plant_groups[i]
            if len(plants) > 0:
                min_left = min(plant.rect.left for plant in plants)
                max_right = max(plant.rect.right for plant in plants)
            else:
                min_left = None
                max_right = None
            hypo_zombies = []
            for zombie in self.zombie_groups[i]:
                if zombie.state != c.WALK:
                    continue
                if len(plants) == 0:
                    continue
                if zombie.rect.left > max_right or zombie.rect.right < min_left:
                    continue
                plant = pg.sprite.spritecollideany(zombie, self.plant_groups[i], collided_func)
                if plant:
                    if plant.name == c.WALLNUTBOWLING:
                        if plant.canHit(i):
                            zombie.setDamage(c.WALLNUT_BOWLING_DAMAGE)
                            plant.changeDirection(i)
                    elif plant.name == c.REDWALLNUTBOWLING:
                        if plant.state == c.IDLE:
                            plant.setAttack()
                    elif plant.name != c.SPIKEWEED:
                        zombie.setAttack(plant)

            for hypno_zombie in self.hypno_zombie_groups[i]:
                if hypno_zombie.health <= 0:
                    continue
                zombie_list = pg.sprite.spritecollide(hypno_zombie,
                               self.zombie_groups[i], False,collided_func)
                for zombie in zombie_list:
                    if zombie.state == c.DIE:
                        continue
                    if zombie.state == c.WALK:
                        zombie.setAttack(hypno_zombie, False)
                    if hypno_zombie.state == c.WALK:
                        hypno_zombie.setAttack(zombie, False)

    def checkCarCollisions(self):
        collided_func = self._collide_ratio[0.8]
        for car in self.cars:
            zombies = pg.sprite.spritecollide(car, self.zombie_groups[car.map_y], False, collided_func)
            for zombie in zombies:
                if zombie and zombie.state != c.DIE:
                    car.setWalk()
                    zombie.setDie()
            if car.dead:
                self.cars.remove(car)

    def boomZombies(self, x, map_y, y_range, x_range):
        for i in range(self.map_y_len):
            if abs(i - map_y) > y_range:
                continue
            for zombie in self.zombie_groups[i]:
                if abs(zombie.rect.centerx - x) <= x_range:
                    zombie.setBoomDie()

    def freezeZombies(self, plant):
        for i in range(self.map_y_len):
            for zombie in self.zombie_groups[i]:
                if zombie.rect.centerx < c.SCREEN_WIDTH:
                    zombie.setFreeze(plant.trap_frames[0])

    def killPlant(self, plant):
        x, y = plant.getPosition()
        map_x, map_y = self.map.getMapIndex(x, y)
        if self.bar_type != c.CHOSSEBAR_BOWLING:
            self.map.setMapGridType(map_x, map_y, c.MAP_EMPTY)
        if (plant.name == c.CHERRYBOMB or plant.name == c.JALAPENO or
            (plant.name == c.POTATOMINE and not plant.is_init) or
            plant.name == c.REDWALLNUTBOWLING):
            self.boomZombies(plant.rect.centerx, map_y, plant.explode_y_range,
                            plant.explode_x_range)
        elif plant.name == c.ICESHROOM and plant.state != c.SLEEP:
            self.freezeZombies(plant)
        elif plant.name == c.HYPNOSHROOM and plant.state != c.SLEEP:
            zombie = plant.kill_zombie
            zombie.setHypno()
            _, map_y = self.map.getMapIndex(zombie.rect.centerx, zombie.rect.bottom)
            self.zombie_groups[map_y].remove(zombie)
            self.hypno_zombie_groups[map_y].add(zombie)
        plant.kill()

    def checkPlant(self, plant, i):
        zombie_len = len(self.zombie_groups[i])
        if plant.name == c.THREEPEASHOOTER:
            if plant.state == c.IDLE:
                if zombie_len > 0:
                    plant.setAttack()
                elif (i-1) >= 0 and len(self.zombie_groups[i-1]) > 0:
                    plant.setAttack()
                elif (i+1) < self.map_y_len and len(self.zombie_groups[i+1]) > 0:
                    plant.setAttack()
            elif plant.state == c.ATTACK:
                if zombie_len > 0:
                    pass
                elif (i-1) >= 0 and len(self.zombie_groups[i-1]) > 0:
                    pass
                elif (i+1) < self.map_y_len and len(self.zombie_groups[i+1]) > 0:
                    pass
                else:
                    plant.setIdle()
        elif plant.name == c.CHOMPER:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack(zombie, self.zombie_groups[i])
                    break
        elif plant.name == c.POTATOMINE:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack()
                    break
        elif plant.name == c.SQUASH:
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    plant.setAttack(zombie, self.zombie_groups[i])
                    break
        elif plant.name == c.SPIKEWEED:
            can_attack = False
            for zombie in self.zombie_groups[i]:
                if plant.canAttack(zombie):
                    can_attack = True
                    break
            if plant.state == c.IDLE and can_attack:
                plant.setAttack(self.zombie_groups[i])
            elif plant.state == c.ATTACK and not can_attack:
                plant.setIdle()
        elif plant.name == c.SCAREDYSHROOM:
            need_cry = False
            can_attack = False
            for zombie in self.zombie_groups[i]:
                if plant.needCry(zombie):
                    need_cry = True
                    break
                elif plant.canAttack(zombie):
                    can_attack = True
            if need_cry:
                if plant.state != c.CRY:
                    plant.setCry()
            elif can_attack:
                if plant.state != c.ATTACK:
                    plant.setAttack()
            elif plant.state != c.IDLE:
                plant.setIdle()
        elif(plant.name == c.WALLNUTBOWLING or
             plant.name == c.REDWALLNUTBOWLING):
            pass
        else:
            can_attack = False
            if (plant.state == c.IDLE and zombie_len > 0):
                for zombie in self.zombie_groups[i]:
                    if plant.canAttack(zombie):
                        can_attack = True
                        break
            if plant.state == c.IDLE and can_attack:
                plant.setAttack()
            elif (plant.state == c.ATTACK and not can_attack):
                plant.setIdle()

    def checkPlants(self):
        for i in range(self.map_y_len):
            for plant in self.plant_groups[i]:
                if plant.state != c.SLEEP:
                    self.checkPlant(plant, i)
                if plant.health <= 0:
                    self.killPlant(plant)

    def checkVictory(self):
        if len(self.zombie_list) > 0:
            return False
        for i in range(self.map_y_len):
            if len(self.zombie_groups[i]) > 0:
                return False
        return True
    
    def checkLose(self):
        for i in range(self.map_y_len):
            for zombie in self.zombie_groups[i]:
                if zombie.rect.right < 0:
                    return True
        return False

    def checkGameState(self):
        # 疯狂模式：时间到则游戏结束，跳转到报告页面
        if self.is_crazy_mode:
            remaining_time = self.checkCrazyModeTime()
            if remaining_time is not None and remaining_time <= 0:
                # 保存游戏数据到 game_info
                self.game_info['final_score'] = self.score
                self.game_info['game_duration'] = self.game_duration
                self.game_info['zombies_killed'] = self.zombies_killed.copy()
                self.next = c.GAME_REPORT
                self.done = True
                return

            # 疯狂模式下只检查失败条件，不检查胜利条件
            if self.checkLose():
                self.next = c.GAME_LOSE
                self.done = True
            return

        # 普通模式：检查胜利和失败
        if self.checkVictory():
            self.game_info[c.LEVEL_NUM] += 1
            self.next = c.GAME_VICTORY
            self.done = True
        elif self.checkLose():
            self.next = c.GAME_LOSE
            self.done = True

    def addScore(self, zombie_name):
        """添加分数并更新击杀统计"""
        score_value = c.ZOMBIE_SCORES.get(zombie_name, 0)
        self.score += score_value
        if zombie_name in self.zombies_killed:
            self.zombies_killed[zombie_name] += 1

    def checkZombieKills(self):
        """检查僵尸击杀并计分"""
        for i in range(self.map_y_len):
            for zombie in self.zombie_groups[i]:
                # 当僵尸进入死亡状态且未计分时
                if zombie.state == c.DIE and not zombie.scored:
                    self.addScore(zombie.name)
                    zombie.scored = True

    def checkCrazyModeTime(self):
        """
        检查疯狂模式倒计时
        Returns:
            int: 剩余时间（毫秒），如果不是疯狂模式返回 None
        """
        if not self.is_crazy_mode:
            return None

        if self.crazy_start_time == 0:
            return self.game_duration

        elapsed = self.current_time - self.crazy_start_time
        remaining = self.game_duration - elapsed
        return max(0, remaining)

    def drawMouseShow(self, surface):
        if self.hint_plant:
            surface.blit(self.hint_image, self.hint_rect)
        x, y = pg.mouse.get_pos()
        self.mouse_rect.centerx = x
        self.mouse_rect.centery = y
        surface.blit(self.mouse_image, self.mouse_rect)

    def drawZombieFreezeTrap(self, i, surface):
        for zombie in self.zombie_groups[i]:
            zombie.drawFreezeTrap(surface)

    def draw(self, surface):
        self.level.blit(self.background, self.viewport, self.viewport)
        surface.blit(self.level, (0,0), self.viewport)
        if self.state == c.CHOOSE:
            self.panel.draw(surface)
        elif self.state == c.PLAY:
            self.menubar.draw(surface)

            # 疯狂模式显示分数和倒计时（纵向堆叠在右上角）
            if self.is_crazy_mode:
                score_bottom_y, score_right_x = self.menubar.drawScore(surface, self.score)
                remaining_time = self.checkCrazyModeTime()
                self.menubar.drawTimer(surface, remaining_time, score_bottom_y, score_right_x)
                # 在得分面板左侧显示"保护AI"
                self.menubar.drawProtectAI(surface, score_right_x - c.scale(150))
            else:
                # 普通模式也显示"保护AI"，在右上角
                self.menubar.drawProtectAI(surface)

            for i in range(self.map_y_len):
                self.plant_groups[i].draw(surface)
                self.zombie_groups[i].draw(surface)
                self.hypno_zombie_groups[i].draw(surface)
                self.bullet_groups[i].draw(surface)
                self.drawZombieFreezeTrap(i, surface)
            for car in self.cars:
                car.draw(surface)
            self.head_group.draw(surface)
            self.sun_group.draw(surface)

            if self.drag_plant:
                self.drawMouseShow(surface)

            # 最后绘制 tooltip，确保显示在最上层
            self.menubar.drawTooltip(surface)
