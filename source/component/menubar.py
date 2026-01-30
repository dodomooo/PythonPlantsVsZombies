__author__ = 'marble_xu'

import random
import pygame as pg
from .. import tool
from .. import constants as c

PANEL_Y_START = 87
PANEL_X_START = 22
PANEL_Y_INTERNAL = 74
PANEL_X_INTERNAL = 53
CARD_LIST_NUM = 8

# 植物中文名称映射
PLANT_DISPLAY_NAMES = {
    c.SUNFLOWER: '向日葵',
    c.PEASHOOTER: '豌豆射手',
    c.SNOWPEASHOOTER: '寒冰射手',
    c.WALLNUT: '坚果墙',
    c.CHERRYBOMB: '樱桃炸弹',
    c.THREEPEASHOOTER: '三线射手',
    c.REPEATERPEA: '双发射手',
    c.CHOMPER: '大嘴花',
    c.POTATOMINE: '土豆雷',
    c.SQUASH: '窝瓜',
    c.SPIKEWEED: '地刺',
    c.JALAPENO: '火爆辣椒',
}

# 植物对应的 Sangfor 产品名称
PLANT_PRODUCT_NAMES = {
    c.SUNFLOWER: 'SecGPT',
    c.PEASHOOTER: 'aES Antivirus',
    c.REPEATERPEA: 'aES DR2.0',
    c.THREEPEASHOOTER: 'XDR',
    c.SNOWPEASHOOTER: 'SIP',
    c.WALLNUT: 'AF + SASE',
    c.CHERRYBOMB: 'MSS',
    c.CHOMPER: 'AC',
    c.POTATOMINE: 'ZTP',
    c.SQUASH: 'DSP',
    c.SPIKEWEED: 'aTrust',
    c.JALAPENO: 'AI Security Platform',
}

# 植物对应的产品说明
PLANT_PRODUCT_DESC = {
    c.SUNFLOWER: '阳光是AI能力，护栏是AI护栏',
    c.PEASHOOTER: '终端杀毒',
    c.REPEATERPEA: '终端行为级检测与响应',
    c.THREEPEASHOOTER: '扩展检测与响应平台',
    c.SNOWPEASHOOTER: '安全感知管理平台',
    c.WALLNUT: 'AF+SASE组网安全解决方案',
    c.CHERRYBOMB: '安全托管服务',
    c.CHOMPER: '下一代上网行为管理',
    c.POTATOMINE: '零信任防护平台',
    c.SQUASH: '数据安全平台',
    c.SPIKEWEED: '零信任访问控制系统',
    c.JALAPENO: 'AI安全平台',
}

card_name_list = [c.CARD_SUNFLOWER, c.CARD_PEASHOOTER, c.CARD_SNOWPEASHOOTER, c.CARD_WALLNUT,
                  c.CARD_CHERRYBOMB, c.CARD_THREEPEASHOOTER, c.CARD_REPEATERPEA, c.CARD_CHOMPER,
                  c.CARD_POTATOMINE, c.CARD_SQUASH, c.CARD_SPIKEWEED, c.CARD_JALAPENO]
plant_name_list = [c.SUNFLOWER, c.PEASHOOTER, c.SNOWPEASHOOTER, c.WALLNUT,
                   c.CHERRYBOMB, c.THREEPEASHOOTER, c.REPEATERPEA, c.CHOMPER,
                   c.POTATOMINE, c.SQUASH, c.SPIKEWEED, c.JALAPENO]
plant_sun_list = [50, 100, 175, 50, 150, 325, 200, 150, 25, 50, 100, 125]
plant_frozen_time_list = [5000, 5000, 5000, 18000, 30000, 5000, 5000, 5000, 18000,
                          18000, 5000, 30000]
all_card_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

def getSunValueImage(sun_value):
    font = pg.font.SysFont(None, 22)
    width = 32
    msg_image = font.render(str(sun_value), True, c.NAVYBLUE, c.LIGHTYELLOW)
    msg_rect = msg_image.get_rect()
    msg_w = msg_rect.width

    image = pg.Surface([width, 17])
    x = width - msg_w

    image.fill(c.LIGHTYELLOW)
    image.blit(msg_image, (x, 0), (0, 0, msg_rect.w, msg_rect.h))
    image.set_colorkey(c.BLACK)
    return image

def getCardPool(data):
    card_pool = []
    for card in data:
        tmp = card['name']
        for i,name in enumerate(plant_name_list):
            if name == tmp:
                card_pool.append(i)
                break
    return card_pool

class Card():
    def __init__(self, x, y, name_index, scale=0.78):
        self.loadFrame(card_name_list[name_index], scale)
        self.rect = self.orig_image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.name_index = name_index
        self.sun_cost = plant_sun_list[name_index]
        self.frozen_time = plant_frozen_time_list[name_index]
        self.frozen_timer = -self.frozen_time
        self.refresh_timer = 0
        self.select = True

    def loadFrame(self, name, scale):
        frame = tool.GFX[name]
        rect = frame.get_rect()
        width, height = rect.w, rect.h

        # 判断是否为高清图片（尺寸超过阈值）
        is_hd = width > c.HD_CARD_WIDTH_THRESHOLD or height > c.HD_CARD_HEIGHT_THRESHOLD

        if is_hd:
            # 高清图片：根据 scale 和标准参考尺寸动态计算目标，保持比例
            target_w = int(c.CARD_REF_WIDTH * scale)
            target_h = int(c.CARD_REF_HEIGHT * scale)
            self.orig_image = tool.get_image_fit(
                frame, 0, 0, width, height, c.BLACK,
                target_width=target_w,
                target_height=target_h,
                keep_ratio=True
            )
        else:
            # 低分辨率图片：保持原有比例缩放（向后兼容）
            self.orig_image = tool.get_image(frame, 0, 0, width, height, c.BLACK, scale)

        self.image = self.orig_image

    def checkMouseClick(self, mouse_pos):
        x, y = mouse_pos
        if(x >= self.rect.x and x <= self.rect.right and
           y >= self.rect.y and y <= self.rect.bottom):
            return True
        return False

    def checkMouseHover(self, mouse_pos):
        """检测鼠标是否悬浮在卡片上"""
        if mouse_pos is None:
            return False
        x, y = mouse_pos
        return (self.rect.x <= x <= self.rect.right and
                self.rect.y <= y <= self.rect.bottom)

    def canClick(self, sun_value, current_time):
        if self.sun_cost <= sun_value and (current_time - self.frozen_timer) > self.frozen_time:
            return True
        return False

    def canSelect(self):
        return self.select

    def setSelect(self, can_select):
        self.select = can_select
        if can_select:
            self.image.set_alpha(255)
        else:
            self.image.set_alpha(128)

    def setFrozenTime(self, current_time):
        self.frozen_timer = current_time

    def createShowImage(self, sun_value, current_time):
        '''create a card image to show cool down status
           or disable status when have not enough sun value'''
        time = current_time - self.frozen_timer
        if time < self.frozen_time: #cool down status
            image = pg.Surface([self.rect.w, self.rect.h])
            frozen_image = self.orig_image.copy()
            frozen_image.set_alpha(128)
            frozen_height = (self.frozen_time - time)/self.frozen_time * self.rect.h
            
            image.blit(frozen_image, (0,0), (0, 0, self.rect.w, frozen_height))
            image.blit(self.orig_image, (0,frozen_height),
                       (0, frozen_height, self.rect.w, self.rect.h - frozen_height))
        elif self.sun_cost > sun_value: #disable status
            image = self.orig_image.copy()
            image.set_alpha(192)
        else:
            image = self.orig_image
        return image

    def update(self, sun_value, current_time):
        if (current_time - self.refresh_timer) >= 250:
            self.image = self.createShowImage(sun_value, current_time)
            self.refresh_timer = current_time

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class MenuBar():
    def __init__(self, card_list, sun_value):
        self.loadFrame(c.MENUBAR_BACKGROUND)
        self.rect = self.image.get_rect()
        self.rect.x = 10
        self.rect.y = 0

        self.sun_value = sun_value
        self.card_offset_x = 32
        self.setupCards(card_list)
        self.tooltip = Tooltip()

    def loadFrame(self, name):
        frame = tool.GFX[name]
        rect = frame.get_rect()
        frame_rect = (rect.x, rect.y, rect.w, rect.h)

        self.image = tool.get_image(tool.GFX[name], *frame_rect, c.WHITE, 1)

    def update(self, current_time, mouse_hover_pos=None):
        self.current_time = current_time
        for card in self.card_list:
            card.update(self.sun_value, self.current_time)
        self.checkCardHover(mouse_hover_pos)
        self.tooltip.update(current_time)

    def checkCardHover(self, mouse_hover_pos):
        """检查卡片悬浮状态并更新 Tooltip"""
        if mouse_hover_pos is None:
            self.tooltip.hide()
            return

        for card in self.card_list:
            if card.checkMouseHover(mouse_hover_pos):
                self.tooltip.show(card, self.current_time)
                return
        self.tooltip.hide()

    def createImage(self, x, y, num):
        if num == 1:
            return
        img = self.image
        rect = self.image.get_rect()
        width = rect.w
        height = rect.h
        self.image = pg.Surface((width * num, height)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        for i in range(num):
            x = i * width
            self.image.blit(img, (x,0))
        self.image.set_colorkey(c.BLACK)
    
    def setupCards(self, card_list):
        self.card_list = []
        x = self.card_offset_x
        y = 8
        for index in card_list:
            x += 55
            self.card_list.append(Card(x, y, index))

    def checkCardClick(self, mouse_pos):
        result = None
        for card in self.card_list:
            if card.checkMouseClick(mouse_pos):
                if card.canClick(self.sun_value, self.current_time):
                    result = (plant_name_list[card.name_index], card)
                break
        return result
    
    def checkMenuBarClick(self, mouse_pos):
        x, y = mouse_pos
        if(x >= self.rect.x and x <= self.rect.right and
           y >= self.rect.y and y <= self.rect.bottom):
            return True
        return False

    def decreaseSunValue(self, value):
        self.sun_value -= value

    def increaseSunValue(self, value):
        self.sun_value += value

    def setCardFrozenTime(self, plant_name):
        for card in self.card_list:
            if plant_name_list[card.name_index] == plant_name:
                card.setFrozenTime(self.current_time)
                break

    def drawSunValue(self):
        self.value_image = getSunValueImage(self.sun_value)
        self.value_rect = self.value_image.get_rect()
        self.value_rect.x = 21
        self.value_rect.y = self.rect.bottom - 21

        self.image.blit(self.value_image, self.value_rect)

    def drawScore(self, surface, score):
        """绘制分数显示"""
        font = pg.font.SysFont('Arial', 24)
        score_text = font.render(f'Score: {score}', True, c.GOLD)

        # 计算文本矩形，放置在右上角
        text_rect = score_text.get_rect()
        padding_x = 10
        padding_y = 5
        text_rect.right = c.SCREEN_WIDTH - padding_x - 5
        text_rect.y = 10

        # 绘制半透明背景
        bg_rect = pg.Rect(
            text_rect.x - padding_x,
            text_rect.y - padding_y,
            text_rect.width + padding_x * 2,
            text_rect.height + padding_y * 2
        )

        # 创建半透明表面
        bg_surface = pg.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(200)
        bg_surface.fill((0, 0, 0))
        surface.blit(bg_surface, (bg_rect.x, bg_rect.y))

        # 绘制边框
        pg.draw.rect(surface, c.GOLD, bg_rect, 1, border_radius=5)

        # 绘制文本
        surface.blit(score_text, (text_rect.x, text_rect.y))

    def drawTimer(self, surface, remaining_time):
        """绘制倒计时
        Args:
            surface: 绘制表面
            remaining_time: 剩余时间（毫秒）
        """
        if remaining_time is None:
            return

        # 转换为秒
        seconds = remaining_time // 1000
        minutes = seconds // 60
        seconds = seconds % 60

        font = pg.font.SysFont('Arial', 24)
        time_text = font.render(f'Time: {minutes:02d}:{seconds:02d}', True, c.WHITE)

        # 计算文本矩形，放置在右上角
        text_rect = time_text.get_rect()
        padding_x = 10
        padding_y = 5
        text_rect.right = c.SCREEN_WIDTH - padding_x - 5
        text_rect.y = 45

        # 绘制半透明背景
        bg_rect = pg.Rect(
            text_rect.x - padding_x,
            text_rect.y - padding_y,
            text_rect.width + padding_x * 2,
            text_rect.height + padding_y * 2
        )

        bg_surface = pg.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(200)
        bg_surface.fill((0, 0, 0))
        surface.blit(bg_surface, (bg_rect.x, bg_rect.y))

        # 绘制边框
        pg.draw.rect(surface, c.WHITE, bg_rect, 1, border_radius=5)

        # 绘制文本
        surface.blit(time_text, (text_rect.x, text_rect.y))

    def drawKills(self, surface, kills):
        """绘制总击杀数
        Args:
            surface: 绘制表面
            kills: 击杀数字典
        """
        total_kills = sum(kills.values())
        font = pg.font.SysFont('Arial', 24)
        kills_text = font.render(f'Kills: {total_kills}', True, c.WHITE)

        # 计算文本矩形，放置在右上角
        text_rect = kills_text.get_rect()
        padding_x = 10
        padding_y = 5
        text_rect.right = c.SCREEN_WIDTH - padding_x - 5
        text_rect.y = 80

        # 绘制半透明背景
        bg_rect = pg.Rect(
            text_rect.x - padding_x,
            text_rect.y - padding_y,
            text_rect.width + padding_x * 2,
            text_rect.height + padding_y * 2
        )

        bg_surface = pg.Surface((bg_rect.width, bg_rect.height))
        bg_surface.set_alpha(200)
        bg_surface.fill((0, 0, 0))
        surface.blit(bg_surface, (bg_rect.x, bg_rect.y))

        # 绘制边框
        pg.draw.rect(surface, c.WHITE, bg_rect, 1, border_radius=5)

        # 绘制文本
        surface.blit(kills_text, (text_rect.x, text_rect.y))

    def draw(self, surface):
        self.drawSunValue()
        surface.blit(self.image, self.rect)
        for card in self.card_list:
            card.draw(surface)

    def drawTooltip(self, surface):
        """单独绘制 tooltip，确保显示在最上层"""
        self.tooltip.draw(surface)

class Panel():
    def __init__(self, card_list, sun_value):
        import time
        t0 = time.time()
        self.loadImages(sun_value)
        t1 = time.time()
        self.selected_cards = []
        self.selected_num = 0
        self.setupCards(card_list)
        t2 = time.time()
        self.tooltip = Tooltip()
        print(f'[DEBUG] Panel.__init__: loadImages={t1-t0:.3f}s, setupCards={t2-t1:.3f}s')

    def loadFrame(self, name):
        frame = tool.GFX[name]
        rect = frame.get_rect()
        frame_rect = (rect.x, rect.y, rect.w, rect.h)

        return tool.get_image(tool.GFX[name], *frame_rect, c.WHITE, 1)

    def loadImages(self, sun_value):
        self.menu_image = self.loadFrame(c.MENUBAR_BACKGROUND)
        self.menu_rect = self.menu_image.get_rect()
        self.menu_rect.x = 0
        self.menu_rect.y = 0

        self.panel_image = self.loadFrame(c.PANEL_BACKGROUND)
        self.panel_rect = self.panel_image.get_rect()
        self.panel_rect.x = 0
        self.panel_rect.y = PANEL_Y_START

        
        self.value_image = getSunValueImage(sun_value)
        self.value_rect = self.value_image.get_rect()
        self.value_rect.x = 21
        self.value_rect.y = self.menu_rect.bottom - 21

        self.button_image =  self.loadFrame(c.START_BUTTON)
        self.button_rect = self.button_image.get_rect()
        self.button_rect.x = 155
        self.button_rect.y = 547

    def setupCards(self, card_list):
        self.card_list = []
        x = PANEL_X_START - PANEL_X_INTERNAL
        y = PANEL_Y_START + 43 - PANEL_Y_INTERNAL
        for i, index in enumerate(card_list):
            if i % 8 == 0:
                x = PANEL_X_START - PANEL_X_INTERNAL
                y += PANEL_Y_INTERNAL
            x += PANEL_X_INTERNAL
            self.card_list.append(Card(x, y, index, 0.75))

    def checkCardClick(self, mouse_pos):
        delete_card = None
        for card in self.selected_cards:
            if delete_card: # when delete a card, move right cards to left
                card.rect.x -= 55
            elif card.checkMouseClick(mouse_pos):
                self.deleteCard(card.name_index)
                delete_card = card

        if delete_card:
            self.selected_cards.remove(delete_card)
            self.selected_num -= 1

        if self.selected_num == CARD_LIST_NUM:
            return

        for card in self.card_list:
            if card.checkMouseClick(mouse_pos):
                if card.canSelect():
                    self.addCard(card)
                break

    def addCard(self, card):
        card.setSelect(False)
        y = 8
        x = 78 + self.selected_num * 55
        self.selected_cards.append(Card(x, y, card.name_index))
        self.selected_num += 1

    def deleteCard(self, index):
        self.card_list[index].setSelect(True)

    def checkStartButtonClick(self, mouse_pos):
        if self.selected_num < CARD_LIST_NUM:
            return False

        x, y = mouse_pos
        if (x >= self.button_rect.x and x <= self.button_rect.right and
            y >= self.button_rect.y and y <= self.button_rect.bottom):
           return True
        return False

    def getSelectedCards(self):
        card_index_list = []
        for card in self.selected_cards:
            card_index_list.append(card.name_index)
        return card_index_list

    def update(self, current_time, mouse_hover_pos=None):
        """更新 Panel 状态，包括 Tooltip"""
        self.current_time = current_time
        self.checkCardHover(mouse_hover_pos)
        self.tooltip.update(current_time)

    def checkCardHover(self, mouse_hover_pos):
        """检查卡片悬浮状态并更新 Tooltip"""
        if mouse_hover_pos is None:
            self.tooltip.hide()
            return

        # 先检查选中的卡片
        for card in self.selected_cards:
            if card.checkMouseHover(mouse_hover_pos):
                self.tooltip.show(card, self.current_time)
                return

        # 再检查面板中的卡片
        for card in self.card_list:
            if card.checkMouseHover(mouse_hover_pos):
                self.tooltip.show(card, self.current_time)
                return
        self.tooltip.hide()

    def draw(self, surface):
        self.menu_image.blit(self.value_image, self.value_rect)
        surface.blit(self.menu_image, self.menu_rect)
        surface.blit(self.panel_image, self.panel_rect)
        for card in self.card_list:
            card.draw(surface)
        for card in self.selected_cards:
            card.draw(surface)

        if self.selected_num == CARD_LIST_NUM:
            surface.blit(self.button_image, self.button_rect)
        self.tooltip.draw(surface)

class MoveCard():
    def __init__(self, x, y, card_name, plant_name, scale=0.78):
        self.loadFrame(card_name, scale)
        self.rect = self.orig_image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.w = 1
        self.image = self.createShowImage()

        self.card_name = card_name
        self.plant_name = plant_name
        self.move_timer = 0
        self.select = True

    def loadFrame(self, name, scale):
        frame = tool.GFX[name]
        rect = frame.get_rect()
        width, height = rect.w, rect.h

        # 判断是否为高清图片（尺寸超过阈值）
        is_hd = width > c.HD_CARD_WIDTH_THRESHOLD or height > c.HD_CARD_HEIGHT_THRESHOLD

        if is_hd:
            # 高清图片：根据 scale 和标准参考尺寸动态计算目标，保持比例
            target_w = int(c.CARD_REF_WIDTH * scale)
            target_h = int(c.CARD_REF_HEIGHT * scale)
            self.orig_image = tool.get_image_fit(
                frame, 0, 0, width, height, c.BLACK,
                target_width=target_w,
                target_height=target_h,
                keep_ratio=True
            )
        else:
            # 低分辨率图片：保持原有比例缩放（向后兼容）
            self.orig_image = tool.get_image(frame, 0, 0, width, height, c.BLACK, scale)

        self.orig_rect = self.orig_image.get_rect()
        self.image = self.orig_image

    def checkMouseClick(self, mouse_pos):
        x, y = mouse_pos
        if(x >= self.rect.x and x <= self.rect.right and
           y >= self.rect.y and y <= self.rect.bottom):
            return True
        return False

    def createShowImage(self):
        '''create a part card image when card appears from left'''
        if self.rect.w < self.orig_rect.w: #create a part card image
            image = pg.Surface([self.rect.w, self.rect.h])
            image.blit(self.orig_image, (0, 0), (0, 0, self.rect.w, self.rect.h))
            self.rect.w += 1
        else:
            image = self.orig_image
        return image

    def update(self, left_x, current_time):
        if self.move_timer == 0:
            self.move_timer = current_time
        elif (current_time - self.move_timer) >= c.CARD_MOVE_TIME:
            if self.rect.x > left_x:
                self.rect.x -= 1
                self.image = self.createShowImage()
            self.move_timer += c.CARD_MOVE_TIME

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class MoveBar():
    def __init__(self, card_pool):
        self.loadFrame(c.MOVEBAR_BACKGROUND)
        self.rect = self.image.get_rect()
        self.rect.x = 90
        self.rect.y = 0
        
        self.card_start_x = self.rect.x + 8
        self.card_end_x = self.rect.right - 5
        self.card_pool = card_pool
        self.card_list = []
        self.create_timer = -c.MOVEBAR_CARD_FRESH_TIME

    def loadFrame(self, name):
        frame = tool.GFX[name]
        rect = frame.get_rect()
        frame_rect = (rect.x, rect.y, rect.w, rect.h)

        self.image = tool.get_image(tool.GFX[name], *frame_rect, c.WHITE, 1)

    def createCard(self):
        if len(self.card_list) > 0 and self.card_list[-1].rect.right > self.card_end_x:
            return False
        x = self.card_end_x
        y = 6
        index = random.randint(0, len(self.card_pool) - 1)
        card_index = self.card_pool[index]
        card_name = card_name_list[card_index] + '_move'
        plant_name = plant_name_list[card_index]
        self.card_list.append(MoveCard(x, y, card_name, plant_name))
        return True

    def update(self, current_time):
        self.current_time = current_time
        left_x = self.card_start_x
        for card in self.card_list:
            card.update(left_x, self.current_time)
            left_x = card.rect.right + 1

        if(self.current_time - self.create_timer) > c.MOVEBAR_CARD_FRESH_TIME:
            if self.createCard():
                self.create_timer = self.current_time

    def checkCardClick(self, mouse_pos):
        result = None
        for index, card in enumerate(self.card_list):
            if card.checkMouseClick(mouse_pos):
                result = (card.plant_name, card)
                break
        return result
    
    def checkMenuBarClick(self, mouse_pos):
        x, y = mouse_pos
        if(x >= self.rect.x and x <= self.rect.right and
           y >= self.rect.y and y <= self.rect.bottom):
            return True
        return False

    def deleateCard(self, card):
        self.card_list.remove(card)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        for card in self.card_list:
            card.draw(surface)


class Tooltip:
    """植物卡片悬浮提示框"""

    # 动画帧间隔（毫秒）
    ANIMATION_INTERVAL = 100
    # Tooltip 尺寸
    TOOLTIP_WIDTH = 230
    TOOLTIP_HEIGHT = 130
    # 植物图像显示尺寸
    PLANT_DISPLAY_SIZE = 70
    # 内边距
    PADDING = 8
    # 行间距
    LINE_SPACING = 2

    def __init__(self):
        self.visible = False
        self.image = None
        self.rect = None
        self.plant_name_index = -1
        self.animation_frames = None
        self.frame_index = 0
        self.animation_timer = 0
        self.card_rect = None

    def show(self, card, current_time):
        """显示 Tooltip"""
        plant_name = plant_name_list[card.name_index]

        # 如果已经显示同一个植物的 Tooltip，只更新位置
        if self.visible and self.plant_name_index == card.name_index:
            self._updatePosition(card.rect)
            return

        self.plant_name_index = card.name_index
        self.visible = True
        self.card_rect = card.rect
        self.frame_index = 0
        self.animation_timer = current_time

        # 加载植物动画帧
        self._loadAnimationFrames(plant_name)

        # 构建 Tooltip Surface
        self._buildTooltipSurface(plant_name, current_time)

        # 计算位置
        self._updatePosition(card.rect)

    def hide(self):
        """隐藏 Tooltip"""
        if self.visible:
            self.visible = False
            self.plant_name_index = -1
            self.animation_frames = None
            self.image = None

    def _loadAnimationFrames(self, plant_name):
        """加载植物动画帧"""
        if plant_name in tool.ORIGIN_GFX:
            self.animation_frames = tool.ORIGIN_GFX[plant_name]
        elif plant_name in tool.GFX:
            frames = tool.GFX[plant_name]
            if isinstance(frames, list):
                self.animation_frames = frames
            else:
                self.animation_frames = [frames]
        else:
            self.animation_frames = None

    def _wrapText(self, text, font, max_width):
        """文本自动换行"""
        lines = []
        current_line = ''
        for char in text:
            test_line = current_line + char
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
        return lines

    def _buildTooltipSurface(self, plant_name, current_time):
        """构建 Tooltip 显示 Surface"""
        # 创建 Tooltip Surface
        self.image = pg.Surface((self.TOOLTIP_WIDTH, self.TOOLTIP_HEIGHT), pg.SRCALPHA)

        # 绘制半透明背景（深蓝色调）
        bg_color = (25, 30, 50, 235)
        pg.draw.rect(self.image, bg_color, (0, 0, self.TOOLTIP_WIDTH, self.TOOLTIP_HEIGHT),
                     border_radius=10)

        # 绘制边框（金色）
        border_color = (255, 200, 50, 255)
        pg.draw.rect(self.image, border_color, (0, 0, self.TOOLTIP_WIDTH, self.TOOLTIP_HEIGHT),
                     width=2, border_radius=10)

        # 绘制植物图像和标题
        self._drawHeader(plant_name)

        # 绘制产品说明
        self._drawProductDesc(plant_name)

        self.rect = self.image.get_rect()

    def _drawHeader(self, plant_name):
        """绘制头部：植物图像 + 名称 + 产品名"""
        # 绘制植物图像（左侧）
        if self.animation_frames and len(self.animation_frames) > 0:
            frame = self.animation_frames[self.frame_index % len(self.animation_frames)]
            frame_rect = frame.get_rect()

            scale_x = self.PLANT_DISPLAY_SIZE / frame_rect.width
            scale_y = self.PLANT_DISPLAY_SIZE / frame_rect.height
            scale = min(scale_x, scale_y)

            new_width = int(frame_rect.width * scale)
            new_height = int(frame_rect.height * scale)
            scaled_frame = pg.transform.smoothscale(frame, (new_width, new_height))

            img_x = self.PADDING + (self.PLANT_DISPLAY_SIZE - new_width) // 2
            img_y = self.PADDING + (self.PLANT_DISPLAY_SIZE - new_height) // 2
            self.image.blit(scaled_frame, (img_x, img_y))

        # 获取文字信息
        display_name = PLANT_DISPLAY_NAMES.get(plant_name, plant_name)
        product_name = PLANT_PRODUCT_NAMES.get(plant_name, '')

        # 文字起始位置（图像右侧）
        text_x = self.PADDING + self.PLANT_DISPLAY_SIZE + 10
        text_max_width = self.TOOLTIP_WIDTH - text_x - self.PADDING

        try:
            name_font = pg.font.SysFont('SimHei', 18, bold=True)
            product_font = pg.font.SysFont('SimHei', 12)
        except:
            name_font = pg.font.SysFont(None, 20)
            product_font = pg.font.SysFont(None, 14)

        # 绘制植物名称（白色，较大）
        y_offset = self.PADDING + 8
        name_surface = name_font.render(display_name, True, c.WHITE)
        self.image.blit(name_surface, (text_x, y_offset))
        y_offset += name_surface.get_height() + 6

        # 绘制产品名称（金色，自动换行处理长名称）
        if product_name:
            # 检查是否需要换行
            product_lines = self._wrapText(product_name, product_font, text_max_width)
            for line in product_lines:
                product_surface = product_font.render(line, True, (255, 215, 100))
                self.image.blit(product_surface, (text_x, y_offset))
                y_offset += product_surface.get_height() + 2

    def _drawProductDesc(self, plant_name):
        """绘制产品说明"""
        product_desc = PLANT_PRODUCT_DESC.get(plant_name, '')
        if not product_desc:
            return

        try:
            desc_font = pg.font.SysFont('SimHei', 12)
        except:
            desc_font = pg.font.SysFont(None, 14)

        # 分隔线位置（在图像下方）
        line_y = self.PADDING + self.PLANT_DISPLAY_SIZE + 6
        pg.draw.line(self.image, (80, 85, 110),
                     (self.PADDING, line_y),
                     (self.TOOLTIP_WIDTH - self.PADDING, line_y), 1)

        # 绘制说明文字
        y_offset = line_y + 6
        max_width = self.TOOLTIP_WIDTH - self.PADDING * 2

        # 文字自动换行
        desc_lines = self._wrapText(product_desc, desc_font, max_width)

        for line in desc_lines:
            if y_offset + desc_font.get_height() > self.TOOLTIP_HEIGHT - self.PADDING:
                break
            desc_surface = desc_font.render(line, True, (200, 205, 215))
            self.image.blit(desc_surface, (self.PADDING, y_offset))
            y_offset += desc_font.get_height() + 1

    def _updatePosition(self, card_rect):
        """更新 Tooltip 位置，确保不超出屏幕"""
        if self.rect is None:
            return

        # 默认显示在卡片右侧
        x = card_rect.right + 8
        y = card_rect.top - 20

        # 边界检测 - 右边界，如果超出则显示在卡片左侧
        if x + self.rect.width > c.SCREEN_WIDTH - 5:
            x = card_rect.left - self.rect.width - 8

        # 边界检测 - 左边界
        if x < 5:
            x = card_rect.centerx - self.rect.width // 2
            if x < 5:
                x = 5

        # 边界检测 - 下边界
        if y + self.rect.height > c.SCREEN_HEIGHT - 5:
            y = c.SCREEN_HEIGHT - 5 - self.rect.height

        # 边界检测 - 上边界
        if y < 5:
            y = 5

        self.rect.x = x
        self.rect.y = y
        self.card_rect = card_rect

    def update(self, current_time):
        """更新动画帧"""
        if not self.visible or self.animation_frames is None:
            return

        if current_time - self.animation_timer >= self.ANIMATION_INTERVAL:
            self.animation_timer = current_time
            self.frame_index = (self.frame_index + 1) % len(self.animation_frames)

            # 重新绘制
            plant_name = plant_name_list[self.plant_name_index]
            self._buildTooltipSurface(plant_name, current_time)
            if self.card_rect:
                self._updatePosition(self.card_rect)

    def draw(self, surface):
        """绘制 Tooltip"""
        if self.visible and self.image and self.rect:
            surface.blit(self.image, self.rect)