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
        self.language_button_rect = pg.Rect(650, 50, 100, 40)

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
        if self.active_input == 'name':
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

        # 绘制页面
        self.draw(surface)

    def handle_input(self, events):
        """处理键盘输入"""
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_TAB:
                    # Tab键切换输入框
                    self.active_input = 'employee_id' if self.active_input == 'name' else 'name'
                    self.update_text_input_rect()
                elif event.key == pg.K_RETURN:
                    # 回车键登录
                    self.do_login()
                elif event.key == pg.K_BACKSPACE:
                    # 退格键删除字符
                    if self.active_input == 'name':
                        self.name_text = self.name_text[:-1]
                    else:
                        self.employee_id_text = self.employee_id_text[:-1]
            elif event.type == pg.TEXTINPUT:
                # 使用 TEXTINPUT 事件处理文本输入（支持中文 IME）
                if self.active_input == 'name':
                    self.name_text += event.text
                else:
                    self.employee_id_text += event.text

    def handle_mouse_click(self, mouse_pos):
        """处理鼠标点击"""
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

        # 点击语言切换按钮
        if self.language_button_rect.collidepoint(mouse_pos):
            self.toggle_language()

    def do_login(self):
        """执行登录"""
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

        # 尝试连接服务器并登录
        self.connecting = True
        try:
            # 检查服务器连接
            if not NETWORK.check_connection():
                raise Exception('服务器未响应')

            # 登录
            result = NETWORK.login(self.name_text.strip(), self.employee_id_text.strip())
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

        # 跳转到主菜单
        self.done = True
        self.next = c.MAIN_MENU

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
        surface.blit(name_label, (150, 260))

        # 绘制姓名输入框
        tool.renderInputBox(surface, self.name_input_rect, self.name_text,
                           self.active_input == 'name', 24)

        # 绘制工号标签
        id_label = label_font.render(LANG.get('login_employee_id'), True, c.WHITE)
        surface.blit(id_label, (150, 330))

        # 绘制工号输入框
        tool.renderInputBox(surface, self.id_input_rect, self.employee_id_text,
                           self.active_input == 'employee_id', 24)

        # 绘制登录按钮 - 使用金黄色与标题呼应
        pg.draw.rect(surface, c.GOLD, self.login_button_rect)
        pg.draw.rect(surface, c.WHITE, self.login_button_rect, 2)
        button_text = label_font.render(LANG.get('login_button'), True, c.BLACK)
        button_text_rect = button_text.get_rect()
        button_text_rect.center = self.login_button_rect.center
        surface.blit(button_text, button_text_rect)

        # 绘制语言切换按钮 - 使用与背景协调的浅金色
        lang_button_color = (120, 100, 150)  # 淡紫色，与深蓝背景协调
        pg.draw.rect(surface, lang_button_color, self.language_button_rect)
        pg.draw.rect(surface, c.WHITE, self.language_button_rect, 2)
        lang_text = label_font.render(LANG.get('login_language'), True, c.WHITE)
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
