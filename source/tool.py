__author__ = 'marble_xu'

import os
# 在导入 pygame 之前设置 SDL 环境变量，启用 Windows 原生 IME 候选框
os.environ["SDL_IME_SHOW_UI"] = "1"

import json
from abc import abstractmethod
import pygame as pg
from . import constants as c

class State():
    def __init__(self):
        self.start_time = 0.0
        self.current_time = 0.0
        self.done = False
        self.next = None
        self.persist = {}
    
    @abstractmethod
    def startup(self, current_time, persist):
        '''abstract method'''

    def cleanup(self):
        self.done = False
        return self.persist
    
    @abstractmethod
    def update(self, surface, keys, current_time):
        '''abstract method'''

class Control():
    def __init__(self):
        self.screen = pg.display.get_surface()
        self.done = False
        self.clock = pg.time.Clock()
        self.fps = 60
        self.keys = pg.key.get_pressed()
        self.mouse_pos = None
        self.mouse_click = [False, False]  # value:[left mouse click, right mouse click]
        self.current_time = 0.0
        self.state_dict = {}
        self.state_name = None
        self.state = None
        self.events = []  # 存储当前帧的所有事件
        self.game_info = {c.CURRENT_TIME:0.0,
                          c.LEVEL_NUM:c.START_LEVEL_NUM}
 
    def setup_states(self, state_dict, start_state):
        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.current_time, self.game_info)

    def update(self):
        self.current_time = pg.time.get_ticks()
        if self.state.done:
            self.flip_state()
        self.state.update(self.screen, self.current_time, self.mouse_pos, self.mouse_click, self.events)
        self.mouse_pos = None
        self.mouse_click[0] = False
        self.mouse_click[1] = False
        self.events = []  # 清空事件列表

    def flip_state(self):
        import time
        t0 = time.time()
        previous, self.state_name = self.state_name, self.state.next
        persist = self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        t1 = time.time()
        self.state.startup(self.current_time, persist)
        t2 = time.time()
        print(f'[DEBUG] flip_state: {previous} -> {self.state_name}, cleanup: {t1-t0:.3f}s, startup: {t2-t1:.3f}s')

    def event_loop(self):
        self.events = pg.event.get()  # 获取所有事件
        for event in self.events:
            if event.type == pg.QUIT:
                self.done = True
            elif event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.mouse_pos = pg.mouse.get_pos()
                self.mouse_click[0], _, self.mouse_click[1] = pg.mouse.get_pressed()
                print('pos:', self.mouse_pos, ' mouse:', self.mouse_click)

    def main(self):
        while not self.done:
            self.event_loop()
            self.update()
            pg.display.update()
            self.clock.tick(self.fps)
        print('game over')

def get_image(sheet, x, y, width, height, colorkey=c.BLACK, scale=1):
        image = pg.Surface([width, height])
        rect = image.get_rect()

        image.blit(sheet, (0, 0), (x, y, width, height))
        image.set_colorkey(colorkey)
        image = pg.transform.scale(image,
                                   (int(rect.width*scale),
                                    int(rect.height*scale)))
        return image

def load_image_frames(directory, image_name, colorkey, accept):
    frame_list = []
    tmp = {}
    # image_name is "Peashooter", pic name is 'Peashooter_1', get the index 1
    index_start = len(image_name) + 1 
    frame_num = 0;
    for pic in os.listdir(directory):
        name, ext = os.path.splitext(pic)
        if ext.lower() in accept:
            index = int(name[index_start:])
            img = pg.image.load(os.path.join(directory, pic))
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
                img.set_colorkey(colorkey)
            tmp[index]= img
            frame_num += 1

    for i in range(frame_num):
        frame_list.append(tmp[i])
    return frame_list

def load_all_gfx(directory, colorkey=c.WHITE, accept=('.png', '.jpg', '.bmp', '.gif')):
    graphics = {}
    for name1 in os.listdir(directory):
        # subfolders under the folder resources\graphics
        dir1 = os.path.join(directory, name1)
        if os.path.isdir(dir1):
            for name2 in os.listdir(dir1):
                dir2 = os.path.join(dir1, name2)
                if os.path.isdir(dir2):
                # e.g. subfolders under the folder resources\graphics\Zombies
                    for name3 in os.listdir(dir2):
                        dir3 = os.path.join(dir2, name3)
                        # e.g. subfolders or pics under the folder resources\graphics\Zombies\ConeheadZombie
                        if os.path.isdir(dir3):
                            # e.g. it's the folder resources\graphics\Zombies\ConeheadZombie\ConeheadZombieAttack
                            image_name, _ = os.path.splitext(name3)
                            graphics[image_name] = load_image_frames(dir3, image_name, colorkey, accept)
                        else:
                            # e.g. pics under the folder resources\graphics\Plants\Peashooter
                            image_name, _ = os.path.splitext(name2)
                            graphics[image_name] = load_image_frames(dir2, image_name, colorkey, accept)
                            break
                else:
                # e.g. pics under the folder resources\graphics\Screen
                    name, ext = os.path.splitext(name2)
                    if ext.lower() in accept:
                        img = pg.image.load(dir2)
                        if img.get_alpha():
                            img = img.convert_alpha()
                        else:
                            img = img.convert()
                            img.set_colorkey(colorkey)
                        graphics[name] = img
    return graphics

def loadZombieImageRect():
    file_path = os.path.join('source', 'data', 'entity', 'zombie.json')
    f = open(file_path)
    data = json.load(f)
    f.close()
    return data[c.ZOMBIE_IMAGE_RECT]

def loadPlantImageRect():
    file_path = os.path.join('source', 'data', 'entity', 'plant.json')
    f = open(file_path)
    data = json.load(f)
    f.close()
    return data[c.PLANT_IMAGE_RECT]

def renderText(text, font_size, color, bg_color=None):
    """渲染文字，返回 Surface 对象"""
    font = pg.font.SysFont('Arial', font_size)
    if bg_color:
        text_surface = font.render(text, True, color, bg_color)
    else:
        text_surface = font.render(text, True, color)
    return text_surface

def renderInputBox(surface, rect, text, active, font_size=24, composing_text=''):
    """渲染输入框
    Args:
        surface: 渲染目标 Surface
        rect: 输入框位置和大小 (x, y, width, height)
        text: 输入框文本
        active: 是否激活（激活时边框高亮）
        font_size: 字体大小
        composing_text: IME 正在编辑的文本（拼音）
    """
    box_rect = pg.Rect(rect)
    # 绘制边框
    border_color = c.GOLD if active else c.WHITE
    pg.draw.rect(surface, border_color, box_rect, 2)
    # 绘制背景
    bg_rect = pg.Rect(rect[0] + 2, rect[1] + 2, rect[2] - 4, rect[3] - 4)
    pg.draw.rect(surface, c.BLACK, bg_rect)
    # 渲染文字
    font = pg.font.SysFont('SimHei', font_size)
    text_x = rect[0] + 10
    text_y = rect[1] + (rect[3] - font_size) // 2

    if text:
        text_surface = font.render(text, True, c.WHITE)
        surface.blit(text_surface, (text_x, text_y))
        text_x += text_surface.get_width()

    # 渲染正在编辑的文本（拼音），用不同颜色显示
    if composing_text:
        composing_surface = font.render(composing_text, True, c.GOLD)
        # 绘制下划线背景表示正在编辑
        underline_rect = pg.Rect(text_x, text_y + font_size - 2, composing_surface.get_width(), 2)
        pg.draw.rect(surface, c.GOLD, underline_rect)
        surface.blit(composing_surface, (text_x, text_y))

def fadeInText(surface, text, alpha, pos, font_size=30, color=c.WHITE):
    """渲染渐入文字效果
    Args:
        surface: 渲染目标 Surface
        text: 文字内容
        alpha: 透明度 (0-255)
        pos: 文字位置 (x, y)
        font_size: 字体大小
        color: 文字颜色
    """
    font = pg.font.SysFont('Arial', font_size)
    text_surface = font.render(text, True, color)
    text_surface.set_alpha(alpha)
    surface.blit(text_surface, pos)

pg.init()
pg.display.set_caption(c.ORIGINAL_CAPTION)
SCREEN = pg.display.set_mode(c.SCREEN_SIZE)

GFX = load_all_gfx(os.path.join("resources","graphics"))
ZOMBIE_RECT = loadZombieImageRect()
PLANT_RECT = loadPlantImageRect()
