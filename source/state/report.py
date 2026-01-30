__author__ = 'marble_xu'

import pygame as pg
from .. import tool
from .. import constants as c
from ..language import LANG
from ..network import NETWORK


# PVZ 风格配色
PVZ_BROWN = (101, 67, 33)        # 木质深棕色
PVZ_BROWN_LIGHT = (139, 90, 43)  # 木质浅棕色
PVZ_BROWN_DARK = (62, 39, 18)    # 木质暗棕色
PVZ_GREEN = (34, 139, 34)        # 草地绿色
PVZ_GREEN_LIGHT = (124, 185, 71) # 浅绿色
PVZ_YELLOW = (255, 215, 0)       # 金黄色
PVZ_CREAM = (255, 248, 220)      # 米黄色
PVZ_PURPLE = (128, 0, 128)       # 紫色（飘带）


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
        self.play_again_button_rect = pg.Rect(200, 520, 180, 45)
        self.exit_button_rect = pg.Rect(420, 520, 180, 45)

        # 排行榜自动刷新机制
        self.refresh_interval = 10000  # 10秒刷新一次
        self.last_refresh_time = 0

        # 加载背景图片
        self.background = None
        self.load_background()

    def load_background(self):
        """加载并处理背景图片"""
        try:
            if 'MainMenu' in tool.GFX:
                bg = tool.GFX['MainMenu']
                self.background = pg.transform.scale(bg, (c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
            else:
                self.background = None
        except Exception:
            self.background = None

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

        # 初始化刷新时间
        self.last_refresh_time = current_time

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

    def update(self, surface, current_time, mouse_pos, mouse_click, events, mouse_hover_pos=None):
        self.current_time = current_time

        # 处理鼠标点击
        if mouse_pos and mouse_click[0]:
            self.handle_mouse_click(mouse_pos)

        # 处理鼠标悬浮光标变化
        self.update_cursor(mouse_hover_pos)

        # 在线模式下自动刷新排行榜
        if not self.is_offline and current_time - self.last_refresh_time >= self.refresh_interval:
            self.refresh_leaderboard()
            self.last_refresh_time = current_time

        # 绘制页面
        self.draw(surface)

    def update_cursor(self, mouse_hover_pos):
        """根据鼠标位置更新光标样式"""
        if mouse_hover_pos:
            # 检查是否悬浮在按钮上
            if (self.play_again_button_rect.collidepoint(mouse_hover_pos) or
                self.exit_button_rect.collidepoint(mouse_hover_pos)):
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            else:
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

    def handle_mouse_click(self, mouse_pos):
        """处理鼠标点击"""
        # 再来一局
        if self.play_again_button_rect.collidepoint(mouse_pos):
            self.done = True
            self.next = c.LOGIN_SCREEN

        # 退出游戏
        if self.exit_button_rect.collidepoint(mouse_pos):
            pg.event.post(pg.event.Event(pg.QUIT))

    def refresh_leaderboard(self):
        """刷新排行榜数据"""
        try:
            self.leaderboard = NETWORK.get_leaderboard(10)
            print(f'Leaderboard refreshed at {self.current_time}')
        except Exception as e:
            print(f'Failed to refresh leaderboard: {e}')

    def draw(self, surface):
        """绘制游戏报告页面 - PVZ风格"""
        # 绘制背景
        if self.background:
            surface.blit(self.background, (0, 0))
            # 添加半透明遮罩使内容更清晰
            overlay = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
            overlay.set_alpha(120)
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))
        else:
            # 备用渐变背景
            for y in range(c.SCREEN_HEIGHT):
                ratio = y / c.SCREEN_HEIGHT
                r = int(135 * (1 - ratio) + 34 * ratio)
                g = int(206 * (1 - ratio) + 100 * ratio)
                b = int(235 * (1 - ratio) + 34 * ratio)
                pg.draw.line(surface, (r, g, b), (0, y), (c.SCREEN_WIDTH, y))

        # 绘制标题横幅（类似GameVictory的紫色飘带）
        self.draw_banner(surface, LANG.get('report_title'), c.SCREEN_WIDTH // 2, 45)

        # 左侧：成绩卡片
        score_card_rect = pg.Rect(25, 95, 365, 185)
        self.draw_pvz_card(surface, score_card_rect, LANG.get('report_score_card'))

        # 绘制最终分数（调整 y 坐标避免遮挡标题）
        self.draw_outlined_text(surface, LANG.get('report_final_score'),
                               100, 145, 18, PVZ_CREAM, PVZ_BROWN_DARK)
        self.draw_outlined_text(surface, str(self.score),
                               100, 175, 36, PVZ_YELLOW, PVZ_BROWN_DARK)

        # 绘制排名（调整 y 坐标避免遮挡标题）
        self.draw_outlined_text(surface, LANG.get('report_rank'),
                               260, 145, 18, PVZ_CREAM, PVZ_BROWN_DARK)
        if self.is_offline:
            rank_text = LANG.get('report_offline')
            rank_color = c.RED
            rank_size = 18
        elif self.rank:
            rank_text = LANG.get('report_rank_format').format(self.rank)
            rank_color = PVZ_GREEN_LIGHT
            rank_size = 28
        else:
            rank_text = LANG.get('report_no_rank')
            rank_color = c.ORANGE
            rank_size = 18
        self.draw_outlined_text(surface, rank_text, 260, 175, rank_size, rank_color, PVZ_BROWN_DARK)

        # 绘制游戏时长（调整 y 坐标）
        duration_seconds = self.game_duration // 1000
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        self.draw_outlined_text(surface, LANG.get('report_duration'),
                               100, 220, 18, PVZ_CREAM, PVZ_BROWN_DARK)
        self.draw_outlined_text(surface, f"{minutes:02d}:{seconds:02d}",
                               100, 250, 28, c.WHITE, PVZ_BROWN_DARK)

        # 右侧：击杀统计卡片
        kills_card_rect = pg.Rect(410, 95, 365, 185)
        self.draw_pvz_card(surface, kills_card_rect, LANG.get('report_kills_title'))

        # 绘制各类僵尸击杀统计
        zombie_name_map = {
            c.NORMAL_ZOMBIE: 'zombie_normal',
            c.CONEHEAD_ZOMBIE: 'zombie_conehead',
            c.BUCKETHEAD_ZOMBIE: 'zombie_buckethead',
            c.FLAG_ZOMBIE: 'zombie_flag',
            c.NEWSPAPER_ZOMBIE: 'zombie_newspaper',
        }

        total_kills = sum(self.zombies_killed.values())
        # 调整总击杀位置，确保在面板内（面板左边界410，内容从420开始）
        total_kills_text = LANG.get('report_total_kills').format(total_kills)
        total_font = pg.font.SysFont('SimHei', 18, bold=True)
        total_surface = total_font.render(total_kills_text, True, PVZ_YELLOW)
        surface.blit(total_surface, (425, 140))

        y_offset = 168
        font = pg.font.SysFont('SimHei', 15)
        for zombie_type, count in self.zombies_killed.items():
            if count > 0 and y_offset < kills_card_rect.bottom - 25:
                zombie_name = LANG.get(zombie_name_map.get(zombie_type, zombie_type))
                score_value = c.ZOMBIE_SCORES.get(zombie_type, 0)

                # 僵尸名称
                name_surface = font.render(f"{zombie_name}:", True, PVZ_CREAM)
                surface.blit(name_surface, (430, y_offset))

                # 数量
                count_surface = font.render(LANG.get('report_count_unit').format(count), True, c.WHITE)
                surface.blit(count_surface, (560, y_offset))

                # 得分
                score_surface = font.render(f"(+{count * score_value})", True, PVZ_GREEN_LIGHT)
                surface.blit(score_surface, (620, y_offset))

                y_offset += 22

        # 底部：排行榜卡片（如果在线）
        if not self.is_offline and self.leaderboard:
            leaderboard_card_rect = pg.Rect(25, 295, 750, 200)
            self.draw_pvz_card(surface, leaderboard_card_rect, LANG.get('report_leaderboard'))

            y_offset = 335
            col1_x = 50
            col2_x = 410

            for i, entry in enumerate(self.leaderboard[:10], 1):
                name = entry.get('name', 'Unknown')
                employee_id = entry.get('employee_id', '')
                score = entry.get('score', 0)

                if employee_id:
                    display_name = f"{name}{employee_id}"
                else:
                    display_name = name

                # 前3名使用特殊颜色
                if i == 1:
                    color = PVZ_YELLOW
                elif i == 2:
                    color = (192, 192, 192)  # 银色
                elif i == 3:
                    color = (205, 127, 50)   # 铜色
                else:
                    color = PVZ_CREAM

                rank_text = f"{i}. {display_name}: {score}"
                font = pg.font.SysFont('SimHei', 17)
                text_surface = font.render(rank_text, True, color)

                if i <= 5:
                    surface.blit(text_surface, (col1_x, y_offset))
                    y_offset += 26
                else:
                    if i == 6:
                        y_offset = 335
                    surface.blit(text_surface, (col2_x, y_offset))
                    y_offset += 26

        # 绘制按钮
        button_y = 515 if (not self.is_offline and self.leaderboard) else 320
        self.play_again_button_rect.y = button_y
        self.exit_button_rect.y = button_y

        # 再来一局按钮 - 绿色
        self.draw_pvz_button(surface, self.play_again_button_rect,
                            LANG.get('report_play_again'), PVZ_GREEN, 20)

        # 退出游戏按钮 - 红色
        self.draw_pvz_button(surface, self.exit_button_rect,
                            LANG.get('report_exit'), (180, 60, 60), 20)

    def draw_banner(self, surface, text, x, y):
        """绘制标题横幅（紫色飘带风格）"""
        banner_width = 500
        banner_height = 60

        # 横幅主体
        banner_rect = pg.Rect(x - banner_width // 2, y - banner_height // 2,
                             banner_width, banner_height)

        # 绘制飘带形状
        points = [
            (banner_rect.left - 20, banner_rect.centery),
            (banner_rect.left + 30, banner_rect.top),
            (banner_rect.right - 30, banner_rect.top),
            (banner_rect.right + 20, banner_rect.centery),
            (banner_rect.right - 30, banner_rect.bottom),
            (banner_rect.left + 30, banner_rect.bottom),
        ]

        # 紫色渐变效果（用两层模拟）
        pg.draw.polygon(surface, (80, 40, 120), points)  # 深紫色底层
        inner_points = [
            (banner_rect.left - 10, banner_rect.centery),
            (banner_rect.left + 35, banner_rect.top + 5),
            (banner_rect.right - 35, banner_rect.top + 5),
            (banner_rect.right + 10, banner_rect.centery),
            (banner_rect.right - 35, banner_rect.bottom - 5),
            (banner_rect.left + 35, banner_rect.bottom - 5),
        ]
        pg.draw.polygon(surface, (120, 60, 160), inner_points)  # 浅紫色

        # 金色边框
        pg.draw.polygon(surface, PVZ_YELLOW, points, 3)

        # 标题文字
        self.draw_outlined_text(surface, text, x, y, 36, PVZ_YELLOW, PVZ_BROWN_DARK)

    def draw_pvz_card(self, surface, rect, title):
        """绘制PVZ风格卡片"""
        # 阴影
        shadow_rect = rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        pg.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=12)

        # 主背景 - 深棕色
        pg.draw.rect(surface, PVZ_BROWN, rect, border_radius=12)

        # 内层背景 - 浅棕色
        inner_rect = pg.Rect(rect.x + 6, rect.y + 6, rect.width - 12, rect.height - 12)
        pg.draw.rect(surface, PVZ_BROWN_LIGHT, inner_rect, border_radius=8)

        # 金色边框
        pg.draw.rect(surface, PVZ_YELLOW, rect, 3, border_radius=12)

        # 标题背景条
        title_bar = pg.Rect(rect.x + 10, rect.y + 8, rect.width - 20, 28)
        pg.draw.rect(surface, PVZ_BROWN_DARK, title_bar, border_radius=5)

        # 标题文字
        self.draw_outlined_text(surface, title, rect.centerx, rect.y + 22,
                               20, PVZ_YELLOW, PVZ_BROWN_DARK)

    def draw_pvz_button(self, surface, rect, text, base_color, font_size):
        """绘制PVZ风格按钮"""
        # 按钮阴影
        shadow = pg.Rect(rect.x + 4, rect.y + 4, rect.width, rect.height)
        pg.draw.rect(surface, PVZ_BROWN_DARK, shadow, border_radius=10)

        # 按钮主体
        pg.draw.rect(surface, base_color, rect, border_radius=10)

        # 高光效果
        highlight = pg.Rect(rect.x + 4, rect.y + 4, rect.width - 8, rect.height // 3)
        highlight_color = (min(base_color[0] + 40, 255),
                          min(base_color[1] + 40, 255),
                          min(base_color[2] + 40, 255))
        pg.draw.rect(surface, highlight_color, highlight, border_radius=6)

        # 金色边框
        pg.draw.rect(surface, PVZ_YELLOW, rect, 3, border_radius=10)

        # 按钮文字
        self.draw_outlined_text(surface, text, rect.centerx, rect.centery,
                               font_size, c.WHITE, PVZ_BROWN_DARK)

    def draw_outlined_text(self, surface, text, x, y, size, color, outline_color):
        """绘制带描边的文字"""
        font = pg.font.SysFont('SimHei', size, bold=True)

        # 绘制描边
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    outline_surface = font.render(text, True, outline_color)
                    outline_rect = outline_surface.get_rect(center=(x + dx, y + dy))
                    surface.blit(outline_surface, outline_rect)

        # 绘制主文字
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=(x, y))
        surface.blit(text_surface, text_rect)
