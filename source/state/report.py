__author__ = 'marble_xu'

import pygame as pg
from datetime import datetime
from .. import tool
from .. import constants as c
from ..language import LANG
from ..network import NETWORK


class GameReportScreen(tool.State):
    """游戏报告页面，显示最终分数、排名和击杀统计"""

    def __init__(self):
        tool.State.__init__(self)
        self.score = 0
        self.rank = None
        self.game_duration = 0
        self.zombies_killed = {}
        self.leaderboard = []
        self.is_offline = False

        # 按钮位置
        self.export_button_rect = pg.Rect(100, 520, 150, 40)
        self.play_again_button_rect = pg.Rect(325, 520, 150, 40)
        self.exit_button_rect = pg.Rect(550, 520, 150, 40)

        # 截图导出反馈
        self.export_message = ''
        self.export_message_time = 0
        self.export_message_duration = 3000  # 显示3秒

    def startup(self, current_time, persist):
        self.persist = persist
        self.game_info = self.persist
        self.start_time = current_time

        # 从 game_info 获取游戏数据
        self.score = self.game_info.get('final_score', 0)
        self.game_duration = self.game_info.get('game_duration', 0)
        self.zombies_killed = self.game_info.get('zombies_killed', {})
        self.is_offline = self.game_info.get('is_offline', True)
        self.rank = None
        self.leaderboard = []

        # 如果是在线模式，提交成绩并获取排行榜
        if not self.is_offline:
            try:
                player_id = self.game_info.get('player_id')
                if player_id:
                    # 提交成绩
                    result = NETWORK.submit_score(
                        player_id,
                        self.score,
                        self.game_duration,
                        self.zombies_killed
                    )
                    self.rank = result.get('rank')

                    # 获取排行榜
                    self.leaderboard = NETWORK.get_leaderboard(10)
            except Exception as e:
                print(f'Failed to submit score or get leaderboard: {e}')
                self.is_offline = True

    def update(self, surface, current_time, mouse_pos, mouse_click, events):
        self.current_time = current_time

        # 处理鼠标点击
        if mouse_pos and mouse_click[0]:
            self.handle_mouse_click(mouse_pos)

        # 检查导出消息是否需要消失
        if self.export_message and current_time - self.export_message_time > self.export_message_duration:
            self.export_message = ''

        # 绘制页面
        self.draw(surface)

    def handle_mouse_click(self, mouse_pos):
        """处理鼠标点击"""
        # 导出截图
        if self.export_button_rect.collidepoint(mouse_pos):
            self.export_screenshot()

        # 再来一局
        if self.play_again_button_rect.collidepoint(mouse_pos):
            self.done = True
            self.next = c.LEVEL

        # 退出游戏
        if self.exit_button_rect.collidepoint(mouse_pos):
            pg.event.post(pg.event.Event(pg.QUIT))

    def export_screenshot(self):
        """导出截图"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'game_report_{timestamp}.png'
        pg.image.save(pg.display.get_surface(), filename)
        print(f'Screenshot saved: {filename}')
        # 显示成功消息
        self.export_message = f'截图已保存: {filename}'
        self.export_message_time = self.current_time

    def draw(self, surface):
        """绘制游戏报告页面"""
        # 填充深色背景
        surface.fill((30, 30, 50))

        # 绘制标题栏
        title_bar_rect = pg.Rect(0, 0, c.SCREEN_WIDTH, 80)
        pg.draw.rect(surface, (50, 50, 80), title_bar_rect)
        pg.draw.rect(surface, c.GOLD, title_bar_rect, 3)

        title_font = pg.font.SysFont('SimHei', 44, bold=True)
        title_text = title_font.render(LANG.get('report_title'), True, c.GOLD)
        title_rect = title_text.get_rect()
        title_rect.center = (c.SCREEN_WIDTH // 2, 40)
        surface.blit(title_text, title_rect)

        # 左侧：成绩卡片
        score_card_rect = pg.Rect(30, 100, 360, 180)
        self.draw_card(surface, score_card_rect, '游戏成绩')

        # 绘制最终分数
        score_font = pg.font.SysFont('SimHei', 36, bold=True)
        score_label = pg.font.SysFont('SimHei', 20).render(LANG.get('report_final_score'), True, c.LIGHTYELLOW)
        surface.blit(score_label, (50, 130))
        score_text = score_font.render(str(self.score), True, c.GOLD)
        surface.blit(score_text, (50, 155))

        # 绘制排名
        rank_label = pg.font.SysFont('SimHei', 20).render(LANG.get('report_rank'), True, c.LIGHTYELLOW)
        surface.blit(rank_label, (220, 130))
        if self.is_offline:
            rank_text = pg.font.SysFont('SimHei', 20).render(LANG.get('report_offline'), True, c.RED)
        elif self.rank:
            rank_display = LANG.get('report_rank_format').format(self.rank)
            rank_text = pg.font.SysFont('SimHei', 28, bold=True).render(rank_display, True, c.GREEN)
        else:
            rank_text = pg.font.SysFont('SimHei', 20).render(LANG.get('report_no_rank'), True, c.ORANGE)
        surface.blit(rank_text, (220, 155))

        # 绘制游戏时长
        duration_seconds = self.game_duration // 1000
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        duration_label = pg.font.SysFont('SimHei', 20).render(LANG.get('report_duration'), True, c.LIGHTYELLOW)
        surface.blit(duration_label, (50, 210))
        duration_text = pg.font.SysFont('SimHei', 28).render(f"{minutes:02d}:{seconds:02d}", True, c.WHITE)
        surface.blit(duration_text, (50, 235))

        # 右侧：击杀统计卡片
        kills_card_rect = pg.Rect(410, 100, 360, 180)
        self.draw_card(surface, kills_card_rect, LANG.get('report_kills_title'))

        # 绘制各类僵尸击杀统计
        kill_font = pg.font.SysFont('SimHei', 18)
        y_offset = 140
        zombie_name_map = {
            c.NORMAL_ZOMBIE: 'zombie_normal',
            c.CONEHEAD_ZOMBIE: 'zombie_conehead',
            c.BUCKETHEAD_ZOMBIE: 'zombie_buckethead',
            c.FLAG_ZOMBIE: 'zombie_flag',
            c.NEWSPAPER_ZOMBIE: 'zombie_newspaper',
        }

        total_kills = sum(self.zombies_killed.values())
        total_label = pg.font.SysFont('SimHei', 20, bold=True).render(f"总击杀: {total_kills}", True, c.GOLD)
        surface.blit(total_label, (430, 140))

        y_offset = 170
        for zombie_type, count in self.zombies_killed.items():
            if count > 0:
                zombie_name = LANG.get(zombie_name_map.get(zombie_type, zombie_type))
                score_value = c.ZOMBIE_SCORES.get(zombie_type, 0)

                # 绘制僵尸名称和数量
                name_text = kill_font.render(f"{zombie_name}:", True, c.LIGHTYELLOW)
                surface.blit(name_text, (430, y_offset))

                count_text = kill_font.render(f"{count}个", True, c.WHITE)
                surface.blit(count_text, (580, y_offset))

                score_text = kill_font.render(f"(+{count * score_value})", True, c.GREEN)
                surface.blit(score_text, (650, y_offset))

                y_offset += 25

        # 底部：排行榜卡片（如果在线）
        if not self.is_offline and self.leaderboard:
            leaderboard_card_rect = pg.Rect(30, 300, 740, 200)
            self.draw_card(surface, leaderboard_card_rect, LANG.get('report_leaderboard'))

            leaderboard_font = pg.font.SysFont('SimHei', 18)
            y_offset = 340

            # 分两列显示排行榜
            col1_x = 50
            col2_x = 410

            for i, entry in enumerate(self.leaderboard[:10], 1):
                name = entry.get('name', 'Unknown')
                score = entry.get('score', 0)

                # 前3名使用特殊颜色
                if i == 1:
                    color = c.GOLD
                elif i == 2:
                    color = (192, 192, 192)  # 银色
                elif i == 3:
                    color = (205, 127, 50)   # 铜色
                else:
                    color = c.WHITE

                rank_text = leaderboard_font.render(f"{i}. {name}: {score}", True, color)

                # 前5名在左列，后5名在右列
                if i <= 5:
                    surface.blit(rank_text, (col1_x, y_offset))
                    y_offset += 28
                else:
                    if i == 6:
                        y_offset = 340
                    surface.blit(rank_text, (col2_x, y_offset))
                    y_offset += 28

        # 绘制按钮（带阴影效果）
        button_font = pg.font.SysFont('SimHei', 22)
        button_y = 520 if (not self.is_offline and self.leaderboard) else 330

        # 更新按钮位置
        self.export_button_rect.y = button_y
        self.play_again_button_rect.y = button_y
        self.exit_button_rect.y = button_y

        # 导出截图按钮
        self.draw_button(surface, self.export_button_rect, LANG.get('report_export'),
                        c.SKY_BLUE, c.WHITE, button_font)

        # 再来一局按钮
        self.draw_button(surface, self.play_again_button_rect, LANG.get('report_play_again'),
                        c.GREEN, c.BLACK, button_font)

        # 退出游戏按钮
        self.draw_button(surface, self.exit_button_rect, LANG.get('report_exit'),
                        c.RED, c.WHITE, button_font)

        # 绘制导出截图反馈消息
        if self.export_message:
            self.draw_export_message(surface)

    def draw_card(self, surface, rect, title):
        """绘制卡片背景
        Args:
            surface: 绘制表面
            rect: 卡片矩形区域
            title: 卡片标题
        """
        # 绘制阴影
        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pg.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=10)

        # 绘制卡片背景
        pg.draw.rect(surface, (60, 60, 90), rect, border_radius=10)
        pg.draw.rect(surface, c.GOLD, rect, 2, border_radius=10)

        # 绘制标题背景条
        title_rect = pg.Rect(rect.x, rect.y, rect.width, 30)
        pg.draw.rect(surface, (50, 50, 70), title_rect, border_top_left_radius=10, border_top_right_radius=10)

        # 绘制标题文字
        title_font = pg.font.SysFont('SimHei', 22, bold=True)
        title_text = title_font.render(title, True, c.GOLD)
        title_text_rect = title_text.get_rect()
        title_text_rect.center = (rect.centerx, rect.y + 15)
        surface.blit(title_text, title_text_rect)

    def draw_button(self, surface, rect, text, bg_color, text_color, font):
        """绘制按钮
        Args:
            surface: 绘制表面
            rect: 按钮矩形区域
            text: 按钮文字
            bg_color: 背景颜色
            text_color: 文字颜色
            font: 字体对象
        """
        # 绘制阴影
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pg.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=8)

        # 绘制按钮
        pg.draw.rect(surface, bg_color, rect, border_radius=8)
        pg.draw.rect(surface, c.WHITE, rect, 2, border_radius=8)

        # 绘制文字
        button_text = font.render(text, True, text_color)
        button_text_rect = button_text.get_rect()
        button_text_rect.center = rect.center
        surface.blit(button_text, button_text_rect)

    def draw_export_message(self, surface):
        """绘制导出截图反馈消息"""
        # 计算淡入淡出效果
        elapsed = self.current_time - self.export_message_time
        if elapsed < 500:
            # 淡入
            alpha = int(255 * (elapsed / 500))
        elif elapsed > self.export_message_duration - 500:
            # 淡出
            alpha = int(255 * ((self.export_message_duration - elapsed) / 500))
        else:
            alpha = 255

        # 创建消息背景
        message_width = 600
        message_height = 60
        message_x = (c.SCREEN_WIDTH - message_width) // 2
        message_y = c.SCREEN_HEIGHT - 100

        # 创建半透明表面
        message_surface = pg.Surface((message_width, message_height))
        message_surface.set_alpha(alpha)
        message_surface.fill((50, 150, 50))

        # 绘制边框
        pg.draw.rect(message_surface, c.WHITE, message_surface.get_rect(), 3, border_radius=10)

        surface.blit(message_surface, (message_x, message_y))

        # 绘制消息文字
        font = pg.font.SysFont('SimHei', 20)
        text_surface = font.render(self.export_message, True, c.WHITE)
        text_surface.set_alpha(alpha)
        text_rect = text_surface.get_rect()
        text_rect.center = (c.SCREEN_WIDTH // 2, message_y + 30)
        surface.blit(text_surface, text_rect)
