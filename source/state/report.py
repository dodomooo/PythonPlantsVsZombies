__author__ = 'marble_xu'

import pygame as pg
from .. import tool
from .. import constants as c
from ..language import LANG
from ..network import NETWORK


class GameReportScreen(tool.State):
    """游戏报告页面，显示最终分数和击杀统计"""

    def __init__(self):
        tool.State.__init__(self)
        self.score = 0
        self.game_duration = 0
        self.zombies_killed = {}
        self.is_offline = False

        # 按钮位置 - 只保留两个按钮
        self.play_again_button_rect = pg.Rect(200, 330, 200, 40)
        self.exit_button_rect = pg.Rect(450, 330, 200, 40)

    def startup(self, current_time, persist):
        self.persist = persist
        self.game_info = self.persist
        self.start_time = current_time

        # 从 game_info 获取游戏数据
        self.score = self.game_info.get('final_score', 0)
        self.game_duration = self.game_info.get('game_duration', 0)
        self.zombies_killed = self.game_info.get('zombies_killed', {})
        self.is_offline = self.game_info.get('is_offline', True)

        # 如果是在线模式，提交成绩
        if not self.is_offline:
            try:
                player_id = self.game_info.get('player_id')
                if player_id:
                    # 提交成绩
                    NETWORK.submit_score(
                        player_id,
                        self.score,
                        self.game_duration,
                        self.zombies_killed
                    )
            except Exception as e:
                print(f'Failed to submit score: {e}')
                self.is_offline = True

    def update(self, surface, current_time, mouse_pos, mouse_click, events):
        self.current_time = current_time

        # 处理鼠标点击
        if mouse_pos and mouse_click[0]:
            self.handle_mouse_click(mouse_pos)

        # 绘制页面
        self.draw(surface)

    def handle_mouse_click(self, mouse_pos):
        """处理鼠标点击"""
        # 再来一局
        if self.play_again_button_rect.collidepoint(mouse_pos):
            self.done = True
            self.next = c.LEVEL

        # 退出游戏
        if self.exit_button_rect.collidepoint(mouse_pos):
            pg.event.post(pg.event.Event(pg.QUIT))

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
        score_card_rect = pg.Rect(30, 100, 360, 200)
        self.draw_card(surface, score_card_rect, LANG.get('report_score_card'))

        # 绘制最终分数
        score_font = pg.font.SysFont('SimHei', 36, bold=True)
        score_label = pg.font.SysFont('SimHei', 20).render(LANG.get('report_final_score'), True, c.LIGHTYELLOW)
        surface.blit(score_label, (50, 130))
        score_text = score_font.render(str(self.score), True, c.GOLD)
        surface.blit(score_text, (50, 155))

        # 绘制游戏时长
        duration_seconds = self.game_duration // 1000
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        duration_label = pg.font.SysFont('SimHei', 20).render(LANG.get('report_duration'), True, c.LIGHTYELLOW)
        surface.blit(duration_label, (50, 210))
        duration_text = pg.font.SysFont('SimHei', 28).render(f"{minutes:02d}:{seconds:02d}", True, c.WHITE)
        surface.blit(duration_text, (50, 235))

        # 右侧：击杀统计卡片
        kills_card_rect = pg.Rect(410, 100, 360, 200)
        kills_card_right_edge = kills_card_rect.x + kills_card_rect.width - 10
        self.draw_card(surface, kills_card_rect, LANG.get('report_kills_title'))

        # 绘制各类僵尸击杀统计
        kill_font = pg.font.SysFont('SimHei', 16)
        zombie_name_map = {
            c.NORMAL_ZOMBIE: 'zombie_normal',
            c.CONEHEAD_ZOMBIE: 'zombie_conehead',
            c.BUCKETHEAD_ZOMBIE: 'zombie_buckethead',
            c.FLAG_ZOMBIE: 'zombie_flag',
            c.NEWSPAPER_ZOMBIE: 'zombie_newspaper',
        }

        total_kills = sum(self.zombies_killed.values())
        total_label = pg.font.SysFont('SimHei', 18, bold=True).render(
            LANG.get('report_total_kills').format(total_kills), True, c.GOLD)
        surface.blit(total_label, (430, 140))

        y_offset = 165
        for zombie_type, count in self.zombies_killed.items():
            if count > 0:
                zombie_name = LANG.get(zombie_name_map.get(zombie_type, zombie_type))
                score_value = c.ZOMBIE_SCORES.get(zombie_type, 0)

                # 绘制僵尸名称
                name_text_content = f"{zombie_name}:"
                name_text = kill_font.render(name_text_content, True, c.LIGHTYELLOW)
                if name_text.get_width() > 120:
                    truncated_name = zombie_name[:8] + "..." if len(zombie_name) > 8 else zombie_name
                    name_text = kill_font.render(f"{truncated_name}:", True, c.LIGHTYELLOW)
                surface.blit(name_text, (430, y_offset))

                # 绘制数量
                count_text = kill_font.render(LANG.get('report_count_unit').format(count), True, c.WHITE)
                surface.blit(count_text, (560, y_offset))

                # 绘制得分
                score_text_content = f"(+{count * score_value})"
                score_text = kill_font.render(score_text_content, True, c.GREEN)
                score_x = min(620, kills_card_right_edge - score_text.get_width())
                surface.blit(score_text, (score_x, y_offset))

                y_offset += 23

        # 绘制按钮
        button_font = pg.font.SysFont('SimHei', 22)

        # 再来一局按钮
        self.draw_button(surface, self.play_again_button_rect, LANG.get('report_play_again'),
                        c.GREEN, c.BLACK, button_font)

        # 退出游戏按钮
        self.draw_button(surface, self.exit_button_rect, LANG.get('report_exit'),
                        c.RED, c.WHITE, button_font)

    def draw_card(self, surface, rect, title):
        """绘制卡片背景"""
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
        """绘制按钮"""
        # 绘制阴影
        shadow_rect = rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pg.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=8)

        # 绘制按钮
        pg.draw.rect(surface, bg_color, rect, border_radius=8)
        pg.draw.rect(surface, c.WHITE, rect, 2, border_radius=8)

        # 绘制文字 - 自适应字体大小
        button_text = font.render(text, True, text_color)
        text_width = button_text.get_rect().width

        if text_width > rect.width - 20:
            scale_factor = (rect.width - 20) / text_width
            smaller_font = pg.font.SysFont('SimHei', int(font.get_height() * scale_factor))
            button_text = smaller_font.render(text, True, text_color)

        button_text_rect = button_text.get_rect()
        button_text_rect.center = rect.center
        surface.blit(button_text, button_text_rect)
