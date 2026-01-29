__author__ = 'marble_xu'

import pygame as pg
from .. import tool
from .. import constants as c
from ..language import LANG
from ..network import NETWORK


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

        # 输入框位置
        self.name_input_rect = (250, 250, 300, 40)
        self.id_input_rect = (250, 320, 300, 40)

        # 按钮位置
        self.login_button_rect = pg.Rect(300, 400, 200, 50)
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

    def update(self, surface, current_time, mouse_pos, mouse_click, events):
        self.current_time = current_time

        # 处理输入
        self.handle_input(events)

        # 处理鼠标点击
        if mouse_pos and mouse_click[0]:
            self.handle_mouse_click(mouse_pos)

        # 错误消息3秒后消失
        if self.error_message and current_time - self.error_time > 3000:
            self.error_message = ''

        # 设置消息2秒后消失
        if self.settings_message and current_time - self.settings_message_time > 2000:
            self.settings_message = ''

        # 绘制页面
        self.draw(surface)

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
            elif event.type == pg.TEXTINPUT:
                # 使用 TEXTINPUT 事件处理文本输入（支持中文 IME）
                if self.show_settings:
                    self.settings_server_url += event.text
                elif self.active_input == 'name':
                    self.name_text += event.text
                else:
                    self.employee_id_text += event.text

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

        # 直接进入游戏关卡，跳过冒险模式页面
        self.done = True
        self.next = c.LEVEL

    def toggle_language(self):
        """切换语言"""
        current_lang = LANG.get_current_language()
        if current_lang == c.LANGUAGE_ZH_CN:
            LANG.set_language(c.LANGUAGE_EN_US)
        else:
            LANG.set_language(c.LANGUAGE_ZH_CN)

    def draw(self, surface):
        """绘制登录页面"""
        # 填充背景
        surface.fill(c.NAVYBLUE)

        # 绘制标题
        title_text = LANG.get('login_title')
        title_font = pg.font.SysFont('SimHei', 36)
        title_surface = title_font.render(title_text, True, c.GOLD)
        title_rect = title_surface.get_rect()
        title_rect.centerx = c.SCREEN_WIDTH // 2
        title_rect.y = 100
        surface.blit(title_surface, title_rect)

        # 绘制姓名标签
        label_font = pg.font.SysFont('SimHei', 24)
        name_label = label_font.render(LANG.get('login_name'), True, c.WHITE)
        surface.blit(name_label, (100, 260))

        # 绘制姓名输入框
        tool.renderInputBox(surface, self.name_input_rect, self.name_text,
                           self.active_input == 'name' and not self.show_settings, 24)

        # 绘制工号标签
        id_label = label_font.render(LANG.get('login_employee_id'), True, c.WHITE)
        surface.blit(id_label, (100, 330))

        # 绘制工号输入框
        tool.renderInputBox(surface, self.id_input_rect, self.employee_id_text,
                           self.active_input == 'employee_id' and not self.show_settings, 24)

        # 绘制登录按钮 - 使用金黄色与标题呼应
        pg.draw.rect(surface, c.GOLD, self.login_button_rect)
        pg.draw.rect(surface, c.WHITE, self.login_button_rect, 2)
        button_text = label_font.render(LANG.get('login_button'), True, c.BLACK)
        button_text_rect = button_text.get_rect()
        button_text_rect.center = self.login_button_rect.center
        surface.blit(button_text, button_text_rect)

        # 绘制设置按钮 - 使用小字体和低调颜色
        small_font = pg.font.SysFont('SimHei', 14)
        settings_button_color = (60, 60, 80)  # 更暗的颜色
        pg.draw.rect(surface, settings_button_color, self.settings_button_rect, border_radius=3)
        pg.draw.rect(surface, (100, 100, 120), self.settings_button_rect, 1, border_radius=3)  # 更细的边框
        settings_text = small_font.render(LANG.get('settings_button'), True, (180, 180, 200))  # 更低调的文字颜色
        settings_text_rect = settings_text.get_rect()
        settings_text_rect.center = self.settings_button_rect.center
        surface.blit(settings_text, settings_text_rect)

        # 绘制语言切换按钮 - 使用小字体和低调颜色
        lang_button_color = (70, 60, 90)  # 更暗的颜色
        pg.draw.rect(surface, lang_button_color, self.language_button_rect, border_radius=3)
        pg.draw.rect(surface, (110, 100, 130), self.language_button_rect, 1, border_radius=3)  # 更细的边框
        lang_text = small_font.render(LANG.get('login_switch_language'), True, (180, 180, 200))  # 更低调的文字颜色
        lang_text_rect = lang_text.get_rect()
        lang_text_rect.center = self.language_button_rect.center
        surface.blit(lang_text, lang_text_rect)

        # 绘制离线模式提示
        if self.is_offline:
            offline_text = label_font.render(LANG.get('login_offline_mode'), True, c.ORANGE)
            offline_rect = offline_text.get_rect()
            offline_rect.centerx = c.SCREEN_WIDTH // 2
            offline_rect.y = 480
            surface.blit(offline_text, offline_rect)

        # 绘制错误消息
        if self.error_message:
            error_font = pg.font.SysFont('SimHei', 20)
            error_surface = error_font.render(self.error_message, True, c.ORANGE)
            error_rect = error_surface.get_rect()
            error_rect.centerx = c.SCREEN_WIDTH // 2
            error_rect.y = 370
            surface.blit(error_surface, error_rect)

        # 绘制连接提示
        if self.connecting:
            connecting_text = label_font.render(LANG.get('login_connecting'), True, c.WHITE)
            connecting_rect = connecting_text.get_rect()
            connecting_rect.centerx = c.SCREEN_WIDTH // 2
            connecting_rect.y = 480
            surface.blit(connecting_text, connecting_rect)

        # 绘制设置弹窗
        if self.show_settings:
            self.draw_settings_panel(surface)

    def draw_settings_panel(self, surface):
        """绘制设置弹窗"""
        # 半透明遮罩
        overlay = pg.Surface((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        # 弹窗背景
        pg.draw.rect(surface, (50, 50, 80), self.settings_panel_rect, border_radius=10)
        pg.draw.rect(surface, c.GOLD, self.settings_panel_rect, 3, border_radius=10)

        # 标题
        title_font = pg.font.SysFont('SimHei', 28, bold=True)
        title_text = title_font.render(LANG.get('settings_title'), True, c.GOLD)
        title_rect = title_text.get_rect()
        title_rect.centerx = self.settings_panel_rect.centerx
        title_rect.y = self.settings_panel_rect.y + 20
        surface.blit(title_text, title_rect)

        # 服务器地址标签
        label_font = pg.font.SysFont('SimHei', 20)
        url_label = label_font.render(LANG.get('settings_server_url'), True, c.WHITE)
        surface.blit(url_label, (180, 210))

        # 服务器地址输入框
        tool.renderInputBox(surface, self.settings_url_input_rect, self.settings_server_url,
                           True, 18)

        # 按钮
        button_font = pg.font.SysFont('SimHei', 18)

        # 测试按钮
        pg.draw.rect(surface, c.SKY_BLUE, self.settings_test_button_rect, border_radius=5)
        pg.draw.rect(surface, c.WHITE, self.settings_test_button_rect, 2, border_radius=5)
        test_text = button_font.render(LANG.get('settings_test'), True, c.WHITE)
        test_text_rect = test_text.get_rect()
        test_text_rect.center = self.settings_test_button_rect.center
        surface.blit(test_text, test_text_rect)

        # 保存按钮
        pg.draw.rect(surface, c.GREEN, self.settings_save_button_rect, border_radius=5)
        pg.draw.rect(surface, c.WHITE, self.settings_save_button_rect, 2, border_radius=5)
        save_text = button_font.render(LANG.get('settings_save'), True, c.BLACK)
        save_text_rect = save_text.get_rect()
        save_text_rect.center = self.settings_save_button_rect.center
        surface.blit(save_text, save_text_rect)

        # 取消按钮
        pg.draw.rect(surface, (100, 100, 100), self.settings_cancel_button_rect, border_radius=5)
        pg.draw.rect(surface, c.WHITE, self.settings_cancel_button_rect, 2, border_radius=5)
        cancel_text = button_font.render(LANG.get('settings_cancel'), True, c.WHITE)
        cancel_text_rect = cancel_text.get_rect()
        cancel_text_rect.center = self.settings_cancel_button_rect.center
        surface.blit(cancel_text, cancel_text_rect)

        # 显示测试/保存消息
        if self.settings_message:
            msg_font = pg.font.SysFont('SimHei', 18)
            msg_surface = msg_font.render(self.settings_message, True, self.settings_message_color)
            msg_rect = msg_surface.get_rect()
            msg_rect.centerx = self.settings_panel_rect.centerx
            msg_rect.y = 360
            surface.blit(msg_surface, msg_rect)
