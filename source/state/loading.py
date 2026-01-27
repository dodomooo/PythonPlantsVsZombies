__author__ = 'marble_xu'

import pygame as pg
from .. import tool
from .. import constants as c
from ..language import LANG


class LoadingScreen(tool.State):
    """Loading 页面，显示安全产品故事"""

    def __init__(self):
        tool.State.__init__(self)
        self.stories = []
        self.current_story_index = 0
        self.story_duration = 2500  # 每段故事显示2.5秒
        self.story_start_time = 0
        self.alpha = 0  # 透明度
        self.fade_in_speed = 5  # 渐入速度
        self.max_alpha = 255
        self.total_duration = 10000  # 总时长10秒

    def startup(self, current_time, persist):
        self.persist = persist
        self.game_info = self.persist
        self.start_time = current_time
        self.story_start_time = current_time
        self.current_story_index = 0
        self.alpha = 0

        # 加载故事文本
        self.stories = [
            LANG.get('loading_story_1'),
            LANG.get('loading_story_2'),
            LANG.get('loading_story_3'),
            LANG.get('loading_story_4'),
        ]

    def update(self, surface, current_time, mouse_pos, mouse_click, events):
        self.current_time = current_time

        # 检查总时长，超过10秒自动跳转
        if current_time - self.start_time >= self.total_duration:
            self.done = True
            self.next = c.LOGIN_SCREEN
            return

        # 检查是否需要切换到下一段故事
        if current_time - self.story_start_time >= self.story_duration:
            self.current_story_index += 1
            if self.current_story_index >= len(self.stories):
                # 所有故事显示完毕，跳转到登录页面
                self.done = True
                self.next = c.LOGIN_SCREEN
                return
            self.story_start_time = current_time
            self.alpha = 0  # 重置透明度

        # 渐入效果
        if self.alpha < self.max_alpha:
            self.alpha = min(self.max_alpha, self.alpha + self.fade_in_speed)

        # 绘制页面
        self.draw(surface)

    def wrap_text(self, text, font, max_width):
        """
        将文本按照最大宽度自动换行
        Args:
            text: 要换行的文本
            font: 字体对象
            max_width: 最大宽度（像素）
        Returns:
            list: 分割后的文本行列表
        """
        words = list(text)  # 将文本拆分为字符列表（支持中文）
        lines = []
        current_line = ''

        for char in words:
            test_line = current_line + char
            # 检查当前行宽度
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                # 当前行已满，保存并开始新行
                if current_line:
                    lines.append(current_line)
                current_line = char

        # 添加最后一行
        if current_line:
            lines.append(current_line)

        return lines

    def draw(self, surface):
        """绘制 Loading 页面"""
        # 填充黑色背景
        surface.fill(c.BLACK)

        # 获取当前故事文本
        if self.current_story_index < len(self.stories):
            story_text = self.stories[self.current_story_index]

            # 文本自动换行处理
            font = pg.font.SysFont('SimHei', 28)  # 使用中文字体
            max_width = c.SCREEN_WIDTH - 100  # 左右各留50像素边距

            # 将文本分割成多行
            lines = self.wrap_text(story_text, font, max_width)

            # 计算总高度
            line_height = font.get_linesize()
            total_height = line_height * len(lines)

            # 起始Y坐标（居中）
            start_y = (c.SCREEN_HEIGHT - total_height) // 2

            # 逐行绘制文字
            for i, line in enumerate(lines):
                text_surface = font.render(line, True, c.WHITE)
                text_surface.set_alpha(self.alpha)
                text_rect = text_surface.get_rect()
                text_rect.centerx = c.SCREEN_WIDTH // 2
                text_rect.y = start_y + i * line_height
                surface.blit(text_surface, text_rect)

            # 绘制进度指示器（小点点）
            dot_y = c.SCREEN_HEIGHT - 50
            dot_spacing = 30
            total_width = len(self.stories) * dot_spacing
            start_x = (c.SCREEN_WIDTH - total_width) // 2

            for i in range(len(self.stories)):
                dot_x = start_x + i * dot_spacing + 15
                if i == self.current_story_index:
                    # 当前故事用金色实心圆
                    pg.draw.circle(surface, c.GOLD, (dot_x, dot_y), 8)
                elif i < self.current_story_index:
                    # 已显示的故事用白色实心圆
                    pg.draw.circle(surface, c.WHITE, (dot_x, dot_y), 8)
                else:
                    # 未显示的故事用灰色空心圆
                    pg.draw.circle(surface, c.WHITE, (dot_x, dot_y), 8, 2)
