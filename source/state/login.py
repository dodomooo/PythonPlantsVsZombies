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


class LoginScreen(tool.State):
    """登录页面，输入姓名和工号"""

    def __init__(self):
        tool.State.__init__(self)
        self.name_text = ''
        self.employee_id_text = ''
        self.active_input = 'name'  # 'name' or 'employee_id'
        self.error_message = ''
        self.error_time = 0
        self.is_offline = False
        self.connecting = False

        # 主面板居中位置
        self.panel_width = 420
        self.panel_height = 340
        self.panel_x = (c.SCREEN_WIDTH - self.panel_width) // 2
        self.panel_y = 130

        # 输入框位置（相对于面板）
        self.name_input_rect = (self.panel_x + 60, self.panel_y + 120, 300, 40)
        self.id_input_rect = (self.panel_x + 60, self.panel_y + 190, 300, 40)

        # 按钮位置
        self.login_button_rect = pg.Rect(self.panel_x + 110, self.panel_y + 260, 200, 50)
        self.settings_button_rect = pg.Rect(655, 15, 65, 28)
        self.language_button_rect = pg.Rect(730, 15, 55, 28)

        # 设置弹窗状态
        self.show_settings = False
        self.settings_server_url = ''
        self.settings_message = ''
        self.settings_message_time = 0
        self.settings_message_color = c.GREEN

        # 设置弹窗输入框和按钮位置
        self.settings_panel_rect = pg.Rect(150, 150, 500, 250)
        self.settings_url_input_rect = (180, 240, 440, 40)
        self.settings_test_button_rect = pg.Rect(180, 310, 120, 40)
        self.settings_save_button_rect = pg.Rect(320, 310, 120, 40)
        self.settings_cancel_button_rect = pg.Rect(460, 310, 120, 40)

        # 加载背景图片
        self.background = None
        self.load_background()

    def load_background(self):
        """加载并缩放背景图片"""
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
        self.name_text = ''
        self.employee_id_text = ''
        self.active_input = 'name'
        self.error_message = ''
        self.is_offline = False
        self.connecting = False
        self.show_settings = False
        self.settings_server_url = NETWORK.get_server_url()
        self.settings_message = ''
        # 启用 IME 文本输入支持（用于中文输入）
        pg.key.start_text_input()
        self.update_text_input_rect()

    def cleanup(self):
        # 离开登录页面时停止 IME 文本输入
        pg.key.stop_text_input()
        self.done = False
        return self.persist

    def update_text_input_rect(self):
        """更新 IME 候选框显示位置"""
        if self.show_settings:
            rect = self.settings_url_input_rect
        elif self.active_input == 'name':
            rect = self.name_input_rect
        else:
            rect = self.id_input_rect
        # 设置 IME 候选框显示在输入框下方
        pg.key.set_text_input_rect(pg.Rect(rect[0], rect[1] + rect[3], rect[2], rect[3]))

    def update(self, surface, current_time, mouse_pos, mouse_click, events, mouse_hover_pos=None):
        self.current_time = current_time

        # 处理输入
        self.handle_input(events)

        # 处理鼠标点击
        if mouse_pos and mouse_click[0]:
            self.handle_mouse_click(mouse_pos)

        # 处理鼠标悬浮光标变化
        self.update_cursor(mouse_hover_pos)

        # 错误消息3秒后消失
        if self.error_message and current_time - self.error_time > 3000:
            self.error_message = ''

        # 设置消息2秒后消失
        if self.settings_message and current_time - self.settings_message_time > 2000:
            self.settings_message = ''

        # 绘制页面
        self.draw(surface)

    def update_cursor(self, mouse_hover_pos):
        """根据鼠标位置更新光标样式"""
        if mouse_hover_pos:
            # 检查是否悬浮在可点击元素上
            is_on_clickable = False

            if self.show_settings:
                # 设置弹窗中的可点击元素
                url_rect = pg.Rect(self.settings_url_input_rect)
                if (url_rect.collidepoint(mouse_hover_pos) or
                    self.settings_test_button_rect.collidepoint(mouse_hover_pos) or
                    self.settings_save_button_rect.collidepoint(mouse_hover_pos) or
                    self.settings_cancel_button_rect.collidepoint(mouse_hover_pos)):
                    is_on_clickable = True
            else:
                # 主页面的可点击元素
                name_rect = pg.Rect(self.name_input_rect)
                id_rect = pg.Rect(self.id_input_rect)
                if (name_rect.collidepoint(mouse_hover_pos) or
                    id_rect.collidepoint(mouse_hover_pos) or
                    self.login_button_rect.collidepoint(mouse_hover_pos) or
                    self.settings_button_rect.collidepoint(mouse_hover_pos) or
                    self.language_button_rect.collidepoint(mouse_hover_pos)):
                    is_on_clickable = True

            if is_on_clickable:
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_HAND)
            else:
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)

    def handle_input(self, events):
        """处理键盘输入"""
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    # ESC键关闭设置弹窗
                    if self.show_settings:
                        self.show_settings = False
                        self.update_text_input_rect()
                elif event.key == pg.K_TAB:
                    if not self.show_settings:
                        # Tab键切换输入框
                        self.active_input = 'employee_id' if self.active_input == 'name' else 'name'
                        self.update_text_input_rect()
                elif event.key == pg.K_RETURN:
                    if not self.show_settings:
                        # 回车键登录
                        self.do_login()
                elif event.key == pg.K_BACKSPACE:
                    # 退格键删除字符
                    if self.show_settings:
                        self.settings_server_url = self.settings_server_url[:-1]
                    elif self.active_input == 'name':
                        self.name_text = self.name_text[:-1]
                    else:
                        self.employee_id_text = self.employee_id_text[:-1]
                elif event.key == pg.K_v and (event.mod & pg.KMOD_CTRL):
                    # Ctrl+V 粘贴
                    self.handle_paste()
            elif event.type == pg.TEXTINPUT:
                # 使用 TEXTINPUT 事件处理文本输入（支持中文 IME）
                if self.show_settings:
                    self.settings_server_url += event.text
                elif self.active_input == 'name':
                    self.name_text += event.text
                else:
                    self.employee_id_text += event.text

    def handle_paste(self):
        """处理粘贴操作"""
        try:
            # 获取剪贴板文本
            clipboard_text = pg.scrap.get(pg.SCRAP_TEXT)
            if clipboard_text:
                # 解码并清理文本（移除空字符）
                text = clipboard_text.decode('utf-8', errors='ignore').rstrip('\x00')
                if text:
                    if self.show_settings:
                        self.settings_server_url += text
                    elif self.active_input == 'name':
                        self.name_text += text
                    else:
                        self.employee_id_text += text
        except Exception as e:
            print(f'Paste failed: {e}')

    def handle_mouse_click(self, mouse_pos):
        """处理鼠标点击"""
        if self.show_settings:
            # 设置弹窗内的点击
            self.handle_settings_click(mouse_pos)
        else:
            # 主页面点击
            self.handle_main_click(mouse_pos)

    def handle_main_click(self, mouse_pos):
        """处理主页面点击"""
        # 点击姓名输入框
        name_rect = pg.Rect(self.name_input_rect)
        if name_rect.collidepoint(mouse_pos):
            self.active_input = 'name'
            self.update_text_input_rect()

        # 点击工号输入框
        id_rect = pg.Rect(self.id_input_rect)
        if id_rect.collidepoint(mouse_pos):
            self.active_input = 'employee_id'
            self.update_text_input_rect()

        # 点击登录按钮
        if self.login_button_rect.collidepoint(mouse_pos):
            self.do_login()

        # 点击设置按钮
        if self.settings_button_rect.collidepoint(mouse_pos):
            self.show_settings = True
            self.settings_server_url = NETWORK.get_server_url()
            self.settings_message = ''
            self.update_text_input_rect()

        # 点击语言切换按钮
        if self.language_button_rect.collidepoint(mouse_pos):
            self.toggle_language()

    def handle_settings_click(self, mouse_pos):
        """处理设置弹窗点击"""
        # 点击输入框
        url_rect = pg.Rect(self.settings_url_input_rect)
        if url_rect.collidepoint(mouse_pos):
            self.update_text_input_rect()

        # 点击测试按钮
        if self.settings_test_button_rect.collidepoint(mouse_pos):
            self.test_server_connection()

        # 点击保存按钮
        if self.settings_save_button_rect.collidepoint(mouse_pos):
            self.save_server_settings()

        # 点击取消按钮
        if self.settings_cancel_button_rect.collidepoint(mouse_pos):
            self.show_settings = False
            self.update_text_input_rect()

        # 点击弹窗外部关闭
        if not self.settings_panel_rect.collidepoint(mouse_pos):
            self.show_settings = False
            self.update_text_input_rect()

    def test_server_connection(self):
        """测试服务器连接"""
        url = self.settings_server_url.strip()
        if not url:
            self.settings_message = LANG.get('settings_test_failed')
            self.settings_message_color = c.RED
            self.settings_message_time = self.current_time
            return

        if NETWORK.test_connection(url):
            self.settings_message = LANG.get('settings_test_success')
            self.settings_message_color = c.GREEN
        else:
            self.settings_message = LANG.get('settings_test_failed')
            self.settings_message_color = c.RED
        self.settings_message_time = self.current_time

    def save_server_settings(self):
        """保存服务器设置"""
        url = self.settings_server_url.strip()
        if not url:
            url = 'http://127.0.0.1:5000'

        if NETWORK.save_config(url):
            self.settings_message = LANG.get('settings_save_success')
            self.settings_message_color = c.GREEN
            self.settings_message_time = self.current_time
            # 关闭设置弹窗
            self.show_settings = False
            self.update_text_input_rect()
        else:
            self.settings_message = LANG.get('settings_save_failed')
            self.settings_message_color = c.RED
            self.settings_message_time = self.current_time

    def do_login(self):
        """执行登录"""
        import time
        t0 = time.time()

        # 验证输入
        if not self.name_text.strip():
            self.error_message = LANG.get('login_name_empty')
            self.error_time = self.current_time
            return

        if not self.employee_id_text.strip():
            self.error_message = LANG.get('login_id_empty')
            self.error_time = self.current_time
            return

        # 保存用户信息到 game_info
        self.game_info['player_name'] = self.name_text.strip()
        self.game_info['employee_id'] = self.employee_id_text.strip()

        # 尝试连接服务器并登录（直接登录，无需预先检查连接）
        self.connecting = True
        try:
            # 直接登录，login 失败会自动抛出异常
            result = NETWORK.login(self.name_text.strip(), self.employee_id_text.strip())
            t1 = time.time()
            print(f'[DEBUG] login: {t1-t0:.3f}s')
            self.game_info['player_id'] = result.get('player_id')
            self.game_info['is_offline'] = False
            self.is_offline = False
        except Exception as e:
            # 连接失败，进入离线模式
            print(f'Login failed: {e}')
            self.error_message = f"{LANG.get('login_error')}{str(e)}"
            self.error_time = self.current_time
            self.is_offline = True
            self.game_info['is_offline'] = True
            self.game_info['player_id'] = None

        self.connecting = False
        print(f'[DEBUG] do_login total: {time.time()-t0:.3f}s')

        # 设置游戏模式信息（原本在主菜单中设置）
        self.game_info['is_crazy_mode'] = True
        self.game_info[c.LEVEL_NUM] = 'crazy'

        # 进入 Loading 页面
        self.done = True
        self.next = c.LOADING_SCREEN

    def toggle_language(self):
        """切换语言"""
        current_lang = LANG.get_current_language()
        if current_lang == c.LANGUAGE_ZH_CN:
            LANG.set_language(c.LANGUAGE_EN_US)
        else:
            LANG.set_language(c.LANGUAGE_ZH_CN)

    def draw(self, surface):
        """绘制登录页面 - PVZ风格"""
        # 绘制背景图片
        if self.background:
            surface.blit(self.background, (0, 0))
        else:
            # 备用渐变背景
            for y in range(c.SCREEN_HEIGHT):
                ratio = y / c.SCREEN_HEIGHT
                r = int(135 * (1 - ratio) + 34 * ratio)
                g = int(206 * (1 - ratio) + 139 * ratio)
                b = int(235 * (1 - ratio) + 34 * ratio)
                pg.draw.line(surface, (r, g, b), (0, y), (c.SCREEN_WIDTH, y))

        # 绘制木质主面板
        self.draw_wood_panel(surface, self.panel_x, self.panel_y,
                            self.panel_width, self.panel_height)

        # 绘制标题 - 金黄色带描边（字体大小26适配中英文及描边）
        title_text = LANG.get('login_title')
        self.draw_outlined_text(surface, title_text,
                               c.SCREEN_WIDTH // 2, self.panel_y + 50,
                               26, PVZ_YELLOW, PVZ_BROWN_DARK)

        # 绘制姓名标签
        label_font = pg.font.SysFont('SimHei', 22)
        name_label = label_font.render(LANG.get('login_name'), True, PVZ_CREAM)
        surface.blit(name_label, (self.panel_x + 60, self.panel_y + 90))

        # 绘制姓名输入框 - PVZ风格
        self.draw_pvz_input_box(surface, self.name_input_rect, self.name_text,
                               self.active_input == 'name' and not self.show_settings)

        # 绘制工号标签
        id_label = label_font.render(LANG.get('login_employee_id'), True, PVZ_CREAM)
        surface.blit(id_label, (self.panel_x + 60, self.panel_y + 160))

        # 绘制工号输入框 - PVZ风格
        self.draw_pvz_input_box(surface, self.id_input_rect, self.employee_id_text,
                               self.active_input == 'employee_id' and not self.show_settings)

        # 绘制登录按钮 - PVZ木质按钮风格
        self.draw_pvz_button(surface, self.login_button_rect,
                            LANG.get('login_button'), PVZ_GREEN, 24)

        # 绘制设置按钮 - 小型木质按钮
        self.draw_small_button(surface, self.settings_button_rect,
                              LANG.get('settings_button'))

        # 绘制语言切换按钮 - 小型木质按钮
        self.draw_small_button(surface, self.language_button_rect,
                              LANG.get('login_switch_language'))

        # 绘制离线模式提示
        if self.is_offline:
            self.draw_outlined_text(surface, LANG.get('login_offline_mode'),
                                   c.SCREEN_WIDTH // 2, self.panel_y + self.panel_height + 30,
                                   22, c.ORANGE, PVZ_BROWN_DARK)

        # 绘制错误消息
        if self.error_message:
            self.draw_outlined_text(surface, self.error_message,
                                   c.SCREEN_WIDTH // 2, self.panel_y + 235,
                                   18, c.ORANGE, PVZ_BROWN_DARK)

        # 绘制连接提示
        if self.connecting:
            self.draw_outlined_text(surface, LANG.get('login_connecting'),
                                   c.SCREEN_WIDTH // 2, self.panel_y + self.panel_height + 30,
                                   22, c.WHITE, PVZ_BROWN_DARK)

        # 绘制设置弹窗
        if self.show_settings:
            self.draw_settings_panel(surface)

    def draw_wood_panel(self, surface, x, y, width, height):
        """绘制木质面板"""
        # 外层阴影
        shadow_rect = pg.Rect(x + 6, y + 6, width, height)
        pg.draw.rect(surface, (0, 0, 0, 100), shadow_rect, border_radius=15)

        # 主面板背景 - 深棕色
        panel_rect = pg.Rect(x, y, width, height)
        pg.draw.rect(surface, PVZ_BROWN, panel_rect, border_radius=12)

        # 内层面板 - 浅棕色
        inner_rect = pg.Rect(x + 8, y + 8, width - 16, height - 16)
        pg.draw.rect(surface, PVZ_BROWN_LIGHT, inner_rect, border_radius=8)

        # 金色边框
        pg.draw.rect(surface, PVZ_YELLOW, panel_rect, 4, border_radius=12)

        # 顶部装饰条 - 深棕色横条
        top_bar = pg.Rect(x + 15, y + 15, width - 30, 8)
        pg.draw.rect(surface, PVZ_BROWN_DARK, top_bar, border_radius=4)

        # 底部装饰条
        bottom_bar = pg.Rect(x + 15, y + height - 23, width - 30, 8)
        pg.draw.rect(surface, PVZ_BROWN_DARK, bottom_bar, border_radius=4)

        # 木纹效果 - 水平线条
        for i in range(4):
            line_y = y + 60 + i * 70
            if line_y < y + height - 40:
                pg.draw.line(surface, PVZ_BROWN_DARK,
                           (x + 20, line_y), (x + width - 20, line_y), 1)

    def draw_pvz_input_box(self, surface, rect, text, active):
        """绘制PVZ风格的输入框"""
        box_rect = pg.Rect(rect)

        # 输入框阴影
        shadow = pg.Rect(rect[0] + 3, rect[1] + 3, rect[2], rect[3])
        pg.draw.rect(surface, PVZ_BROWN_DARK, shadow, border_radius=8)

        # 输入框背景 - 米黄色
        pg.draw.rect(surface, PVZ_CREAM, box_rect, border_radius=8)

        # 边框颜色
        border_color = PVZ_YELLOW if active else PVZ_BROWN
        pg.draw.rect(surface, border_color, box_rect, 3, border_radius=8)

        # 文字
        font = pg.font.SysFont('SimHei', 22)
        if text:
            text_surface = font.render(text, True, PVZ_BROWN_DARK)
            text_rect = text_surface.get_rect()
            text_rect.midleft = (rect[0] + 12, rect[1] + rect[3] // 2)
            surface.blit(text_surface, text_rect)

        # 光标
        if active:
            cursor_x = rect[0] + 12
            if text:
                cursor_x += font.size(text)[0]
            cursor_rect = pg.Rect(cursor_x, rect[1] + 8, 2, rect[3] - 16)
            # 闪烁效果
            if (pg.time.get_ticks() // 500) % 2 == 0:
                pg.draw.rect(surface, PVZ_BROWN_DARK, cursor_rect)

    def draw_pvz_button(self, surface, rect, text, base_color, font_size):
        """绘制PVZ风格的按钮"""
        # 按钮阴影
        shadow = pg.Rect(rect.x + 4, rect.y + 4, rect.width, rect.height)
        pg.draw.rect(surface, PVZ_BROWN_DARK, shadow, border_radius=10)

        # 按钮主体 - 渐变效果模拟
        pg.draw.rect(surface, base_color, rect, border_radius=10)

        # 高光效果
        highlight = pg.Rect(rect.x + 4, rect.y + 4, rect.width - 8, rect.height // 3)
        highlight_color = (min(base_color[0] + 40, 255),
                          min(base_color[1] + 40, 255),
                          min(base_color[2] + 40, 255))
        pg.draw.rect(surface, highlight_color, highlight, border_radius=6)

        # 金色边框
        pg.draw.rect(surface, PVZ_YELLOW, rect, 3, border_radius=10)

        # 按钮文字 - 带描边
        self.draw_outlined_text(surface, text, rect.centerx, rect.centery,
                               font_size, c.WHITE, PVZ_BROWN_DARK)

    def draw_small_button(self, surface, rect, text):
        """绘制小型按钮"""
        # 按钮阴影
        shadow = pg.Rect(rect.x + 2, rect.y + 2, rect.width, rect.height)
        pg.draw.rect(surface, (0, 0, 0), shadow, border_radius=5)

        # 按钮主体
        pg.draw.rect(surface, PVZ_BROWN_LIGHT, rect, border_radius=5)
        pg.draw.rect(surface, PVZ_YELLOW, rect, 2, border_radius=5)

        # 文字
        font = pg.font.SysFont('SimHei', 12)
        text_surface = font.render(text, True, PVZ_CREAM)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    def draw_outlined_text(self, surface, text, x, y, size, color, outline_color):
        """绘制带描边的文字"""
        font = pg.font.SysFont('SimHei', size, bold=True)

        # 绘制描边（8个方向）
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

    def draw_settings_panel(self, surface):
        """绘制设置弹窗 - PVZ风格"""
        # 半透明遮罩
        overlay = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # 木质弹窗面板
        self.draw_wood_panel(surface, self.settings_panel_rect.x, self.settings_panel_rect.y,
                            self.settings_panel_rect.width, self.settings_panel_rect.height)

        # 标题 - 金黄色带描边
        self.draw_outlined_text(surface, LANG.get('settings_title'),
                               self.settings_panel_rect.centerx, self.settings_panel_rect.y + 45,
                               28, PVZ_YELLOW, PVZ_BROWN_DARK)

        # 服务器地址标签
        label_font = pg.font.SysFont('SimHei', 18)
        url_label = label_font.render(LANG.get('settings_server_url'), True, PVZ_CREAM)
        surface.blit(url_label, (180, 210))

        # 服务器地址输入框 - PVZ风格
        self.draw_pvz_input_box(surface, self.settings_url_input_rect,
                               self.settings_server_url, True)

        # 测试按钮
        self.draw_pvz_button(surface, self.settings_test_button_rect,
                            LANG.get('settings_test'), c.SKY_BLUE, 16)

        # 保存按钮
        self.draw_pvz_button(surface, self.settings_save_button_rect,
                            LANG.get('settings_save'), PVZ_GREEN, 16)

        # 取消按钮
        self.draw_pvz_button(surface, self.settings_cancel_button_rect,
                            LANG.get('settings_cancel'), (139, 90, 43), 16)

        # 显示测试/保存消息
        if self.settings_message:
            self.draw_outlined_text(surface, self.settings_message,
                                   self.settings_panel_rect.centerx, 365,
                                   16, self.settings_message_color, PVZ_BROWN_DARK)
