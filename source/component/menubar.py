__author__ = 'marble_xu'

import random
import pygame as pg
from .. import tool
from .. import constants as c

PANEL_Y_START = c.scale(87)
PANEL_X_START = c.scale(22)
PANEL_Y_INTERNAL = c.scale(74)
PANEL_X_INTERNAL = c.scale(53)
CARD_LIST_NUM = 8

# 僵尸名称到行走动画帧的映射
ZOMBIE_WALK_FRAMES = {
    c.NORMAL_ZOMBIE: 'Zombie',
    c.CONEHEAD_ZOMBIE: 'ConeheadZombie',
    c.BUCKETHEAD_ZOMBIE: 'BucketheadZombie',
    c.FLAG_ZOMBIE: 'FlagZombie',
    c.NEWSPAPER_ZOMBIE: 'NewspaperZombie',
}

# 僵尸中文名称映射
ZOMBIE_DISPLAY_NAMES = {
    c.NORMAL_ZOMBIE: '木马僵尸',
    c.CONEHEAD_ZOMBIE: '蠕虫僵尸',
    c.BUCKETHEAD_ZOMBIE: '勒索僵尸',
    c.FLAG_ZOMBIE: '钓鱼僵尸',
    c.NEWSPAPER_ZOMBIE: '间谍僵尸',
}

# 僵尸图片水平偏移量（用于居中校正）
ZOMBIE_X_OFFSET = {
    c.NORMAL_ZOMBIE: -15,
    c.CONEHEAD_ZOMBIE: -20,
    c.BUCKETHEAD_ZOMBIE: -15,
    c.FLAG_ZOMBIE: -10,
    c.NEWSPAPER_ZOMBIE: 10,
}

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
    font = pg.font.SysFont(None, c.scale(22))
    width = c.scale(32)
    msg_image = font.render(str(sun_value), True, c.NAVYBLUE, c.LIGHTYELLOW)
    msg_rect = msg_image.get_rect()
    msg_w = msg_rect.width

    image = pg.Surface([width, c.scale(17)])
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
        self.rect.x = c.scale(10)
        self.rect.y = 0

        self.sun_value = sun_value
        self.card_offset_x = c.scale(32)
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
        y = c.scale(8)
        for index in card_list:
            x += c.scale(55)
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
        self.value_rect.x = c.scale(21)
        self.value_rect.y = self.rect.bottom - c.scale(21)

        self.image.blit(self.value_image, self.value_rect)

    def drawScore(self, surface, score):
        """绘制分数显示（右上角最右边）
        Returns:
            int: 面板底部 y 坐标，供 Timer 定位使用
        """
        font = pg.font.SysFont('Arial', c.scale(24))
        score_text = font.render(f'Score: {score}', True, c.GOLD)

        # 计算文本矩形，放置在右上角最右边
        text_rect = score_text.get_rect()
        padding_x = c.scale(10)
        padding_y = c.scale(5)
        text_rect.right = c.SCREEN_WIDTH - padding_x - c.scale(5)
        text_rect.y = c.scale(10)

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
        pg.draw.rect(surface, c.GOLD, bg_rect, c.scale(1), border_radius=c.scale(5))

        # 绘制文本
        surface.blit(score_text, (text_rect.x, text_rect.y))

        # 返回背景矩形底部 y 坐标和右边界 x 坐标，供 Timer 定位使用
        return bg_rect.bottom, bg_rect.right

    def drawTimer(self, surface, remaining_time, score_bottom_y=None, score_right_x=None):
        """绘制倒计时（在 Score 下方纵向堆叠）
        Args:
            surface: 绘制表面
            remaining_time: 剩余时间（毫秒）
            score_bottom_y: Score 面板的底部 y 坐标
            score_right_x: Score 面板的右边界 x 坐标
        """
        if remaining_time is None:
            return

        # 转换为秒
        seconds = remaining_time // 1000
        minutes = seconds // 60
        seconds = seconds % 60

        font = pg.font.SysFont('Arial', c.scale(24))
        time_text = font.render(f'Time: {minutes:02d}:{seconds:02d}', True, c.WHITE)

        # 计算文本矩形，放置在 Score 下方
        text_rect = time_text.get_rect()
        padding_x = c.scale(10)
        padding_y = c.scale(5)

        # 确保右对齐且不超出屏幕
        if score_right_x is not None:
            text_rect.right = min(score_right_x, c.SCREEN_WIDTH - c.scale(15))
        else:
            text_rect.right = c.SCREEN_WIDTH - padding_x - c.scale(5)

        # 确保不超出左边界
        if text_rect.x < c.scale(5):
            text_rect.x = c.scale(5)

        if score_bottom_y is not None:
            text_rect.y = score_bottom_y + c.scale(5)
        else:
            text_rect.y = c.scale(10)

        # 确保不超出下边界
        if text_rect.y + text_rect.height > c.SCREEN_HEIGHT - c.scale(10):
            text_rect.y = c.SCREEN_HEIGHT - c.scale(10) - text_rect.height

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
        pg.draw.rect(surface, c.WHITE, bg_rect, c.scale(1), border_radius=c.scale(5))

        # 绘制文本
        surface.blit(time_text, (text_rect.x, text_rect.y))

    def drawKills(self, surface, kills):
        """绘制总击杀数
        Args:
            surface: 绘制表面
            kills: 击杀数字典
        """
        total_kills = sum(kills.values())
        font = pg.font.SysFont('Arial', c.scale(24))
        kills_text = font.render(f'Kills: {total_kills}', True, c.WHITE)

        # 计算文本矩形，放置在右上角
        text_rect = kills_text.get_rect()
        padding_x = c.scale(10)
        padding_y = c.scale(5)
        text_rect.right = c.SCREEN_WIDTH - padding_x - c.scale(5)
        text_rect.y = c.scale(80)

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
        pg.draw.rect(surface, c.WHITE, bg_rect, c.scale(1), border_radius=c.scale(5))

        # 绘制文本
        surface.blit(kills_text, (text_rect.x, text_rect.y))

    def drawProtectAI(self, surface, right_margin=None):
        """绘制"保护AI"高清文字（无边框，纯描边效果）
        Args:
            surface: 绘制表面
            right_margin: 右边界 x 坐标（如果有得分面板，传入其左边界）
        """
        try:
            font = pg.font.SysFont('SimHei', c.scale(32), bold=True)
        except:
            font = pg.font.SysFont(None, c.scale(34))

        text = '保护AI'

        # 计算位置
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()

        if right_margin is not None:
            text_rect.right = right_margin - c.scale(20)
        else:
            text_rect.right = c.SCREEN_WIDTH - c.scale(25)
        text_rect.y = c.scale(15)

        # 绘制多层描边实现立体效果
        # 外层阴影（深色）
        shadow_color = (30, 20, 10)
        shadow_offset = c.scale(3)
        shadow_surface = font.render(text, True, shadow_color)
        surface.blit(shadow_surface, (text_rect.x + shadow_offset, text_rect.y + shadow_offset))

        # 描边层（深金色）
        outline_color = (139, 90, 43)
        outline_offset = c.scale(2)
        for dx in [-outline_offset, 0, outline_offset]:
            for dy in [-outline_offset, 0, outline_offset]:
                if dx != 0 or dy != 0:
                    outline_surface = font.render(text, True, outline_color)
                    surface.blit(outline_surface, (text_rect.x + dx, text_rect.y + dy))

        # 主文字（亮金色渐变效果）
        main_color = (255, 215, 0)
        main_surface = font.render(text, True, main_color)
        surface.blit(main_surface, text_rect)

        # 高光层（浅色，偏移-1像素）
        highlight_color = (255, 245, 180)
        highlight_surface = font.render(text, True, highlight_color)
        highlight_surface.set_alpha(100)
        surface.blit(highlight_surface, (text_rect.x - c.scale(1), text_rect.y - c.scale(1)))

        return text_rect.x  # 返回左边界供其他元素定位

    def draw(self, surface):
        self.drawSunValue()
        surface.blit(self.image, self.rect)
        for card in self.card_list:
            card.draw(surface)

    def drawTooltip(self, surface):
        """单独绘制 tooltip，确保显示在最上层"""
        self.tooltip.draw(surface)

class Panel():
    def __init__(self, card_list, sun_value, zombie_types=None):
        self.loadImages(sun_value)
        self.selected_cards = []
        self.selected_num = 0
        self.setupCards(card_list)
        self.tooltip = Tooltip()
        # 僵尸预览相关
        self.zombie_types = zombie_types or []
        self.setupZombiePreview()

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
        self.value_rect.x = c.scale(21)
        self.value_rect.y = self.menu_rect.bottom - c.scale(21)

        self.button_image =  self.loadFrame(c.START_BUTTON)
        self.button_rect = self.button_image.get_rect()
        self.button_rect.x = c.scale(155)
        self.button_rect.y = c.scale(547)

    def setupCards(self, card_list):
        self.card_list = []
        x = PANEL_X_START - PANEL_X_INTERNAL
        y = PANEL_Y_START + c.scale(43) - PANEL_Y_INTERNAL
        for i, index in enumerate(card_list):
            if i % 8 == 0:
                x = PANEL_X_START - PANEL_X_INTERNAL
                y += PANEL_Y_INTERNAL
            x += PANEL_X_INTERNAL
            self.card_list.append(Card(x, y, index, 0.75))

    def setupZombiePreview(self):
        """设置僵尸预览"""
        self.zombie_frames = {}
        self.zombie_frame_indices = {}
        self.zombie_animation_timer = 0

        # 去重并保持顺序
        seen = set()
        unique_zombies = []
        for z in self.zombie_types:
            if z not in seen:
                seen.add(z)
                unique_zombies.append(z)
        self.zombie_types = unique_zombies

        # 加载每种僵尸的行走动画帧
        for zombie_name in self.zombie_types:
            frame_key = ZOMBIE_WALK_FRAMES.get(zombie_name)
            if frame_key and frame_key in tool.GFX:
                frames = tool.GFX[frame_key]
                if isinstance(frames, list) and len(frames) > 0:
                    self.zombie_frames[zombie_name] = frames
                    self.zombie_frame_indices[zombie_name] = 0

    def checkCardClick(self, mouse_pos):
        delete_card = None
        for card in self.selected_cards:
            if delete_card: # when delete a card, move right cards to left
                card.rect.x -= c.scale(55)
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
        y = c.scale(8)
        x = c.scale(78) + self.selected_num * c.scale(55)
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
        """更新 Panel 状态，包括 Tooltip 和僵尸动画"""
        self.current_time = current_time
        self.checkCardHover(mouse_hover_pos)
        self.tooltip.update(current_time)
        # 更新僵尸动画帧
        if current_time - self.zombie_animation_timer >= 150:
            self.zombie_animation_timer = current_time
            for zombie_name in self.zombie_frames:
                frames = self.zombie_frames[zombie_name]
                self.zombie_frame_indices[zombie_name] = (
                    self.zombie_frame_indices[zombie_name] + 1
                ) % len(frames)

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

        # 绘制僵尸预览
        self.drawZombiePreview(surface)

        self.tooltip.draw(surface)

    def drawZombiePreview(self, surface):
        """绘制僵尸预览区域"""
        if not self.zombie_frames:
            return

        # 预览区域配置
        preview_x = c.scale(460)  # 右侧区域起始 x
        preview_y = c.scale(100)  # 起始 y
        preview_width = c.scale(330)
        preview_height = c.scale(450)

        # 绘制半透明背景
        bg_surface = pg.Surface((preview_width, preview_height), pg.SRCALPHA)
        bg_color = (20, 25, 40, 220)
        pg.draw.rect(bg_surface, bg_color, (0, 0, preview_width, preview_height),
                     border_radius=c.scale(12))
        # 绘制边框
        border_color = (180, 140, 60, 255)
        pg.draw.rect(bg_surface, border_color, (0, 0, preview_width, preview_height),
                     width=c.scale(3), border_radius=c.scale(12))
        surface.blit(bg_surface, (preview_x, preview_y))

        # 绘制标题
        try:
            title_font = pg.font.SysFont('SimHei', c.scale(20), bold=True)
        except:
            title_font = pg.font.SysFont(None, c.scale(22))
        title_text = title_font.render('本关僵尸', True, (255, 215, 100))
        title_rect = title_text.get_rect(centerx=preview_x + preview_width // 2,
                                         y=preview_y + c.scale(12))
        surface.blit(title_text, title_rect)

        # 僵尸图像显示尺寸和布局
        zombie_display_size = c.scale(95)
        cols = 2
        spacing_x = c.scale(155)
        spacing_y = c.scale(130)
        start_x = preview_x + c.scale(20)
        start_y = preview_y + c.scale(50)

        try:
            name_font = pg.font.SysFont('SimHei', c.scale(12))
        except:
            name_font = pg.font.SysFont(None, c.scale(14))

        for i, zombie_name in enumerate(self.zombie_types):
            if zombie_name not in self.zombie_frames:
                continue

            col = i % cols
            row = i // cols
            x = start_x + col * spacing_x
            y = start_y + row * spacing_y

            # 获取当前帧
            frames = self.zombie_frames[zombie_name]
            frame_idx = self.zombie_frame_indices[zombie_name]
            frame = frames[frame_idx]
            frame_rect = frame.get_rect()

            # 缩放以适配显示区域
            scale_x = zombie_display_size / frame_rect.width
            scale_y = zombie_display_size / frame_rect.height
            scale = min(scale_x, scale_y)

            new_width = int(frame_rect.width * scale)
            new_height = int(frame_rect.height * scale)
            scaled_frame = pg.transform.smoothscale(frame, (new_width, new_height))

            # 居中显示（应用偏移量校正）
            x_offset = c.scale(ZOMBIE_X_OFFSET.get(zombie_name, 0))
            img_x = x + (zombie_display_size - new_width) // 2 + x_offset
            img_y = y + (zombie_display_size - new_height) // 2
            surface.blit(scaled_frame, (img_x, img_y))

            # 绘制僵尸名称
            display_name = ZOMBIE_DISPLAY_NAMES.get(zombie_name, zombie_name)
            name_text = name_font.render(display_name, True, (200, 205, 215))
            name_rect = name_text.get_rect(centerx=x + zombie_display_size // 2,
                                           y=y + zombie_display_size + c.scale(2))
            surface.blit(name_text, name_rect)

class MoveCard():
    def __init__(self, x, y, card_name, plant_name, scale=0.78):
        self.loadFrame(card_name, scale)
        self.rect = self.orig_image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.rect.w = c.scale(1)
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
            self.rect.w += c.scale(1)
        else:
            image = self.orig_image
        return image

    def update(self, left_x, current_time):
        if self.move_timer == 0:
            self.move_timer = current_time
        elif (current_time - self.move_timer) >= c.CARD_MOVE_TIME:
            if self.rect.x > left_x:
                self.rect.x -= c.scale(1)
                self.image = self.createShowImage()
            self.move_timer += c.CARD_MOVE_TIME

    def draw(self, surface):
        surface.blit(self.image, self.rect)

class MoveBar():
    def __init__(self, card_pool):
        self.loadFrame(c.MOVEBAR_BACKGROUND)
        self.rect = self.image.get_rect()
        self.rect.x = c.scale(90)
        self.rect.y = 0
        
        self.card_start_x = self.rect.x + c.scale(8)
        self.card_end_x = self.rect.right - c.scale(5)
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
        y = c.scale(6)
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
            left_x = card.rect.right + c.scale(1)

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

    def drawTooltip(self, surface):
        """MoveBar 不需要 Tooltip，空实现以保持接口一致"""
        pass

    def drawProtectAI(self, surface, right_margin=None):
        """绘制"保护AI"高清文字（无边框，纯描边效果）
        Args:
            surface: 绘制表面
            right_margin: 右边界 x 坐标
        """
        try:
            font = pg.font.SysFont('SimHei', c.scale(32), bold=True)
        except:
            font = pg.font.SysFont(None, c.scale(34))

        text = '保护AI'
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect()

        if right_margin is not None:
            text_rect.right = right_margin - c.scale(20)
        else:
            text_rect.right = c.SCREEN_WIDTH - c.scale(25)
        text_rect.y = c.scale(15)

        # 外层阴影
        shadow_color = (30, 20, 10)
        shadow_offset = c.scale(3)
        shadow_surface = font.render(text, True, shadow_color)
        surface.blit(shadow_surface, (text_rect.x + shadow_offset, text_rect.y + shadow_offset))

        # 描边层
        outline_color = (139, 90, 43)
        outline_offset = c.scale(2)
        for dx in [-outline_offset, 0, outline_offset]:
            for dy in [-outline_offset, 0, outline_offset]:
                if dx != 0 or dy != 0:
                    outline_surface = font.render(text, True, outline_color)
                    surface.blit(outline_surface, (text_rect.x + dx, text_rect.y + dy))

        # 主文字
        main_color = (255, 215, 0)
        main_surface = font.render(text, True, main_color)
        surface.blit(main_surface, text_rect)

        # 高光层
        highlight_color = (255, 245, 180)
        highlight_surface = font.render(text, True, highlight_color)
        highlight_surface.set_alpha(100)
        surface.blit(highlight_surface, (text_rect.x - c.scale(1), text_rect.y - c.scale(1)))

        return text_rect.x


class Tooltip:
    """植物卡片悬浮提示框"""

    # 动画帧间隔（毫秒）
    ANIMATION_INTERVAL = 100
    # Tooltip 尺寸（左右布局，加宽）
    TOOLTIP_WIDTH = c.scale(320)
    TOOLTIP_HEIGHT = c.scale(110)
    # 左侧区域宽度
    LEFT_AREA_WIDTH = c.scale(200)
    # 植物图像显示尺寸
    PLANT_DISPLAY_SIZE = c.scale(65)
    # 内边距
    PADDING = c.scale(10)
    # 行间距
    LINE_SPACING = c.scale(2)

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
                     border_radius=c.scale(10))

        # 绘制边框（金色）
        border_color = (255, 200, 50, 255)
        pg.draw.rect(self.image, border_color, (0, 0, self.TOOLTIP_WIDTH, self.TOOLTIP_HEIGHT),
                     width=c.scale(2), border_radius=c.scale(10))

        # 绘制植物图像和标题
        self._drawHeader(plant_name)

        self.rect = self.image.get_rect()

    def _drawHeader(self, plant_name):
        """绘制左右布局：左侧（植物图像+产品名+介绍），右侧（参照原型+植物名称）"""
        # 字体
        try:
            product_font = pg.font.SysFont('SimHei', c.scale(14), bold=True)
            desc_font = pg.font.SysFont('SimHei', c.scale(11))
            label_font = pg.font.SysFont('SimHei', c.scale(11))
            plant_name_font = pg.font.SysFont('SimHei', c.scale(14), bold=True)
        except:
            product_font = pg.font.SysFont(None, c.scale(16))
            desc_font = pg.font.SysFont(None, c.scale(13))
            label_font = pg.font.SysFont(None, c.scale(13))
            plant_name_font = pg.font.SysFont(None, c.scale(16))

        # ========== 左侧区域 ==========
        # 绘制植物图像（左上角）
        img_x = self.PADDING
        img_y = self.PADDING
        if self.animation_frames and len(self.animation_frames) > 0:
            frame = self.animation_frames[self.frame_index % len(self.animation_frames)]
            frame_rect = frame.get_rect()

            scale_x = self.PLANT_DISPLAY_SIZE / frame_rect.width
            scale_y = self.PLANT_DISPLAY_SIZE / frame_rect.height
            scale = min(scale_x, scale_y)

            new_width = int(frame_rect.width * scale)
            new_height = int(frame_rect.height * scale)
            scaled_frame = pg.transform.smoothscale(frame, (new_width, new_height))

            img_draw_x = img_x + (self.PLANT_DISPLAY_SIZE - new_width) // 2
            img_draw_y = img_y + (self.PLANT_DISPLAY_SIZE - new_height) // 2
            self.image.blit(scaled_frame, (img_draw_x, img_draw_y))

        # 文字区域（植物图像右侧）
        text_x = img_x + self.PLANT_DISPLAY_SIZE + c.scale(8)
        text_max_width = self.LEFT_AREA_WIDTH - self.PLANT_DISPLAY_SIZE - c.scale(18)
        y_offset = self.PADDING + c.scale(2)

        # 获取文字信息
        product_name = PLANT_PRODUCT_NAMES.get(plant_name, '')
        product_desc = PLANT_PRODUCT_DESC.get(plant_name, '')

        # 绘制产品名称（金色加粗）
        if product_name:
            product_lines = self._wrapText(product_name, product_font, text_max_width)
            for line in product_lines:
                product_surface = product_font.render(line, True, (255, 215, 100))
                self.image.blit(product_surface, (text_x, y_offset))
                y_offset += product_surface.get_height() + c.scale(2)

        # 绘制产品说明（浅灰色）
        if product_desc:
            y_offset += c.scale(3)
            desc_lines = self._wrapText(product_desc, desc_font, text_max_width)
            for line in desc_lines:
                if y_offset + desc_font.get_height() > self.TOOLTIP_HEIGHT - self.PADDING:
                    break
                desc_surface = desc_font.render(line, True, (200, 205, 215))
                self.image.blit(desc_surface, (text_x, y_offset))
                y_offset += desc_font.get_height() + c.scale(2)

        # ========== 分隔线 ==========
        separator_x = self.LEFT_AREA_WIDTH
        pg.draw.line(self.image, (100, 110, 130, 180),
                     (separator_x, self.PADDING + c.scale(5)),
                     (separator_x, self.TOOLTIP_HEIGHT - self.PADDING - c.scale(5)),
                     width=c.scale(1))

        # ========== 右侧区域 ==========
        right_x = self.LEFT_AREA_WIDTH + c.scale(12)
        right_width = self.TOOLTIP_WIDTH - self.LEFT_AREA_WIDTH - self.PADDING - c.scale(12)

        # "参照原型" 标签（顶端对齐）
        label_text = '参照原型'
        label_surface = label_font.render(label_text, True, (150, 160, 180))
        label_y = self.PADDING + c.scale(2)
        self.image.blit(label_surface, (right_x, label_y))

        # 植物中文名称
        display_name = PLANT_DISPLAY_NAMES.get(plant_name, plant_name)
        name_lines = self._wrapText(display_name, plant_name_font, right_width)
        name_y = label_y + label_surface.get_height() + c.scale(6)
        for line in name_lines:
            name_surface = plant_name_font.render(line, True, (120, 220, 120))
            self.image.blit(name_surface, (right_x, name_y))
            name_y += name_surface.get_height() + c.scale(2)

    def _updatePosition(self, card_rect):
        """更新 Tooltip 位置，确保不超出屏幕"""
        if self.rect is None:
            return

        # 默认显示在卡片右侧
        x = card_rect.right + c.scale(8)
        y = card_rect.top - c.scale(20)

        # 边界检测 - 右边界，如果超出则显示在卡片左侧
        if x + self.rect.width > c.SCREEN_WIDTH - c.scale(5):
            x = card_rect.left - self.rect.width - c.scale(8)

        # 边界检测 - 左边界
        if x < c.scale(5):
            x = card_rect.centerx - self.rect.width // 2
            if x < c.scale(5):
                x = c.scale(5)

        # 边界检测 - 下边界
        if y + self.rect.height > c.SCREEN_HEIGHT - c.scale(5):
            y = c.SCREEN_HEIGHT - c.scale(5) - self.rect.height

        # 边界检测 - 上边界
        if y < c.scale(5):
            y = c.scale(5)

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
