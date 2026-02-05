__author__ = 'marble_xu'

import os
# 在导入 pygame 之前设置 SDL 环境变量，启用 Windows 原生 IME 候选框
os.environ["SDL_IME_SHOW_UI"] = "1"

import json
from abc import abstractmethod
import pygame as pg
from . import constants as c

_LOADING_SURFACE = None
_LOADING_RECT = None

def _refresh_loading_screen():
    # Keep window responsive and avoid transient white areas during heavy loading.
    if _LOADING_SURFACE is None:
        return
    try:
        pg.event.pump()
    except pg.error:
        return
    screen = pg.display.get_surface()
    if not screen:
        return
    screen.fill((0, 0, 0))
    screen.blit(_LOADING_SURFACE, _LOADING_RECT)
    pg.display.update()

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
        self.mouse_hover_pos = None  # 鼠标悬浮位置
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
        self.state.update(self.screen, self.current_time, self.mouse_pos,
                          self.mouse_click, self.events, self.mouse_hover_pos)
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
        # 检查本帧是否有 ESC 按键（ESC 由各状态自行处理，不应触发退出）
        has_esc = any(e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE for e in self.events)
        for event in self.events:
            if event.type == pg.QUIT:
                if not has_esc:
                    self.done = True
            elif event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()
            elif event.type == pg.MOUSEBUTTONDOWN:
                self.mouse_pos = pg.mouse.get_pos()
                self.mouse_click[0], _, self.mouse_click[1] = pg.mouse.get_pressed()
                print('pos:', self.mouse_pos, ' mouse:', self.mouse_click)
            elif event.type == pg.MOUSEMOTION:
                self.mouse_hover_pos = pg.mouse.get_pos()

    def main(self):
        while not self.done:
            self.event_loop()
            self.update()
            pg.display.update()
            self.clock.tick(self.fps)
        print('game over')

def get_image(sheet, x, y, width, height, colorkey=c.BLACK, scale=1):
        src_x = int(x * c.ASSET_PIXEL_RATIO)
        src_y = int(y * c.ASSET_PIXEL_RATIO)
        src_w = int(width * c.ASSET_PIXEL_RATIO)
        src_h = int(height * c.ASSET_PIXEL_RATIO)

        # 如果 colorkey 为 None，使用 SRCALPHA 支持完整透明度
        if colorkey is None:
            image = pg.Surface([src_w, src_h], pg.SRCALPHA)
        else:
            image = pg.Surface([src_w, src_h])

        rect = image.get_rect()

        image.blit(sheet, (0, 0), (src_x, src_y, src_w, src_h))
        if colorkey is not None:
            image.set_colorkey(colorkey)

        total_scale = scale * c.ASSET_SCALE
        if total_scale != 1:
            image = pg.transform.scale(image,
                                       (int(rect.width*total_scale),
                                        int(rect.height*total_scale)))
        return image

def get_image_fit(sheet, x, y, width, height, colorkey=c.BLACK, target_width=None, target_height=None, keep_ratio=True):
    """根据目标尺寸缩放图片，适用于高清图片自适应显示

    Args:
        sheet: 源图像 Surface
        x, y: 源图像裁剪起始坐标
        width, height: 源图像裁剪尺寸
        colorkey: 透明色（None 时使用 SRCALPHA）
        target_width: 目标宽度
        target_height: 目标高度
        keep_ratio: 是否保持宽高比（默认 True）

    Returns:
        缩放后的 Surface
    """
    src_x = int(x * c.ASSET_PIXEL_RATIO)
    src_y = int(y * c.ASSET_PIXEL_RATIO)
    src_w = int(width * c.ASSET_PIXEL_RATIO)
    src_h = int(height * c.ASSET_PIXEL_RATIO)

    # 如果 colorkey 为 None，使用 SRCALPHA 支持完整透明度
    if colorkey is None:
        image = pg.Surface([src_w, src_h], pg.SRCALPHA)
    else:
        image = pg.Surface([src_w, src_h])

    image.blit(sheet, (0, 0), (src_x, src_y, src_w, src_h))
    if colorkey is not None:
        image.set_colorkey(colorkey)

    if target_width is None and target_height is None:
        return image

    if keep_ratio:
        # 计算缩放比例，取较小值以保证图片完全适配
        scale_x = target_width / width if target_width else float('inf')
        scale_y = target_height / height if target_height else float('inf')
        scale = min(scale_x, scale_y)
        new_width = int(width * scale)
        new_height = int(height * scale)
    else:
        new_width = target_width if target_width else width
        new_height = target_height if target_height else height

    # 计算缩放倍数，超过 2 倍使用 smoothscale 获得更好质量
    scale_factor = max(width / new_width, height / new_height)
    if scale_factor > 2:
        image = pg.transform.smoothscale(image, (new_width, new_height))
    else:
        image = pg.transform.scale(image, (new_width, new_height))

    return image

def load_image_frames(directory, image_name, colorkey, accept, tick=None):
    frame_list = []
    tmp = {}
    # image_name is "Peashooter", pic name is 'Peashooter_1', get the index 1
    index_start = len(image_name) + 1 
    frame_num = 0;
    for pic in os.listdir(directory):
        if tick:
            tick()
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
        if tick:
            tick()

    for i in range(len(tmp)):
        frame_list.append(tmp[i])
    return frame_list

def load_all_gfx(directory, colorkey=c.WHITE, accept=('.png', '.jpg', '.bmp', '.gif')):
    graphics = {}
    refresh = _refresh_loading_screen
    refresh_counter = 0

    def tick():
        nonlocal refresh_counter
        refresh_counter += 1
        if refresh_counter >= 30:
            refresh_counter = 0
            refresh()

    for name1 in os.listdir(directory):
        tick()
        # subfolders under the folder resources\graphics
        dir1 = os.path.join(directory, name1)
        if os.path.isdir(dir1):
            for name2 in os.listdir(dir1):
                tick()
                dir2 = os.path.join(dir1, name2)
                if os.path.isdir(dir2):
                # e.g. subfolders under the folder resources\graphics\Zombies
                    for name3 in os.listdir(dir2):
                        tick()
                        dir3 = os.path.join(dir2, name3)
                        # e.g. subfolders or pics under the folder resources\graphics\Zombies\ConeheadZombie
                        if os.path.isdir(dir3):
                            # e.g. it's the folder resources\graphics\Zombies\ConeheadZombie\ConeheadZombieAttack
                            image_name, _ = os.path.splitext(name3)
                            graphics[image_name] = load_image_frames(dir3, image_name, colorkey, accept, tick)
                        else:
                            # e.g. pics under the folder resources\graphics\Plants\Peashooter
                            image_name, _ = os.path.splitext(name2)
                            graphics[image_name] = load_image_frames(dir2, image_name, colorkey, accept, tick)
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
                tick()
    refresh()
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
    font = pg.font.SysFont('Arial', c.scale(font_size))
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
    pg.draw.rect(surface, border_color, box_rect, c.scale(2))
    # 绘制背景
    bg_rect = pg.Rect(rect[0] + c.scale(2), rect[1] + c.scale(2),
                      rect[2] - c.scale(4), rect[3] - c.scale(4))
    pg.draw.rect(surface, c.BLACK, bg_rect)
    # 渲染文字
    font = pg.font.SysFont('SimHei', c.scale(font_size))
    scaled_font_size = c.scale(font_size)
    text_x = rect[0] + c.scale(10)
    text_y = rect[1] + (rect[3] - scaled_font_size) // 2

    if text:
        text_surface = font.render(text, True, c.WHITE)
        surface.blit(text_surface, (text_x, text_y))
        text_x += text_surface.get_width()

    # 渲染正在编辑的文本（拼音），用不同颜色显示
    if composing_text:
        composing_surface = font.render(composing_text, True, c.GOLD)
        # 绘制下划线背景表示正在编辑
        underline_rect = pg.Rect(text_x, text_y + scaled_font_size - c.scale(2),
                                 composing_surface.get_width(), c.scale(2))
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
    font = pg.font.SysFont('Arial', c.scale(font_size))
    text_surface = font.render(text, True, color)
    text_surface.set_alpha(alpha)
    surface.blit(text_surface, pos)

pg.init()
pg.display.set_caption(c.ORIGINAL_CAPTION)
SCREEN = pg.display.set_mode(c.SCREEN_SIZE, pg.RESIZABLE | pg.SCALED)
# 启用按键重复：首次延迟500ms，之后每50ms重复（用于长按backspace等）
pg.key.set_repeat(500, 50)
# 初始化剪贴板模块（用于粘贴功能）
pg.scrap.init()

# 显示加载提示
SCREEN.fill((0, 0, 0))
_loading_font = pg.font.SysFont('Arial', c.scale(48))
_loading_text = _loading_font.render('Loading...', True, (255, 255, 255))
_loading_rect = _loading_text.get_rect(center=(c.SCREEN_WIDTH // 2, c.SCREEN_HEIGHT // 2))
SCREEN.blit(_loading_text, _loading_rect)
pg.display.flip()
_LOADING_SURFACE = _loading_text
_LOADING_RECT = _loading_rect
del _loading_font

GFX = load_all_gfx(os.path.join("resources","graphics"))
ORIGIN_GFX = load_all_gfx(os.path.join("resources","origin_graphics"))
_LOADING_SURFACE = None
_LOADING_RECT = None
ZOMBIE_RECT = loadZombieImageRect()
PLANT_RECT = loadPlantImageRect()
