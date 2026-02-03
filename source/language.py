__author__ = 'marble_xu'

from . import constants as c


class LanguageManager:
    """多语言管理器，支持中英文切换"""

    def __init__(self, default_language=c.LANGUAGE_ZH_CN):
        self.current_language = default_language
        self.translations = {}
        self._load_translations()

    def _load_translations(self):
        """加载所有语言翻译"""
        self.translations[c.LANGUAGE_ZH_CN] = self._load_chinese()
        self.translations[c.LANGUAGE_EN_US] = self._load_english()

    def _load_chinese(self):
        """中文翻译"""
        return {
            # Loading Screen
            'loading_story_1': '数智化浪潮下，企业的核心资产正面临前所未有的威胁！',
            'loading_story_2': '你是用户的首席安全官，在深信服 GPT 强力 AI 引擎的加持下，构筑最后一道数字防线。',
            'loading_story_3': '这不是一场持久战，而是一场2分钟的极限生存赛。',
            'loading_story_4': '面对汹涌而来的各种变种病毒和黑客攻击，你需要迅速部署深信服安全产品矩阵，精准拦截，守护企业数据安全！',

            # Login Screen
            'login_title': 'GPT助力：安全保卫战',
            'login_name': '姓名：',
            'login_employee_id': '工号：',
            'login_button': '开始游戏',
            'login_language': '语言',
            'login_switch_language': 'English',
            'login_offline_mode': '离线模式',
            'login_connecting': '正在连接服务器...',
            'login_error': '登录失败：',
            'login_name_empty': '请输入姓名',
            'login_id_empty': '请输入工号',

            # Settings
            'settings_button': '设置',
            'settings_title': '服务器设置',
            'settings_server_url': '服务器地址：',
            'settings_test': '测试连接',
            'settings_save': '保存',
            'settings_cancel': '取消',
            'settings_test_success': '连接成功',
            'settings_test_failed': '连接失败',
            'settings_save_success': '保存成功',
            'settings_save_failed': '保存失败',

            # Main Menu
            'menu_adventure': '开始冒险',
            'menu_crazy_mode': '疯狂模式',

            # Game UI
            'game_score': '分数：',
            'game_time': '时间：',
            'game_kills': '击杀：',
            'game_sun': '阳光：',

            # Game Report
            'report_title': '游戏报告',
            'report_score_card': '游戏成绩',
            'report_final_score': '最终分数：',
            'report_rank': '排名：',
            'report_duration': '游戏时长：',
            'report_kills_title': '击杀统计',
            'report_total_kills': '总击杀: {}',
            'report_count_unit': '{}个',
            'report_leaderboard': '排行榜',
            'report_export': '导出截图',
            'report_play_again': '再来一局',
            'report_exit': '退出游戏',
            'report_offline': '离线模式（无排名）',
            'report_rank_format': '第 {} 名',
            'report_no_rank': '未上榜',

            # Zombie Names
            'zombie_preview_title': '本关僵尸',
            'zombie_normal': '木马僵尸',
            'zombie_conehead': '勒索僵尸',
            'zombie_buckethead': '银狐僵尸',
            'zombie_flag': '钓鱼僵尸',
            'zombie_newspaper': '漏洞僵尸',

            # Plant Tooltip
            'plant_tooltip_prototype': '参照原型',
            'plant_name_sunflower': '向日葵',
            'plant_name_peashooter': '豌豆射手',
            'plant_name_snowpeashooter': '寒冰射手',
            'plant_name_wallnut': '坚果墙',
            'plant_name_cherrybomb': '樱桃炸弹',
            'plant_name_threepeashooter': '三线射手',
            'plant_name_repeaterpea': '双发射手',
            'plant_name_chomper': '大嘴花',
            'plant_name_potatomine': '土豆雷',
            'plant_name_squash': '窝瓜',
            'plant_name_spikeweed': '地刺',
            'plant_name_jalapeno': '火爆辣椒',
            'plant_desc_sunflower': '阳光是AI能力，护栏是AI护栏',
            'plant_desc_peashooter': '终端杀毒',
            'plant_desc_repeaterpea': '终端行为级检测与响应',
            'plant_desc_threepeashooter': '扩展检测与响应平台',
            'plant_desc_snowpeashooter': '安全感知管理平台',
            'plant_desc_wallnut': 'AF+SASE组网安全解决方案',
            'plant_desc_cherrybomb': '安全托管服务',
            'plant_desc_chomper': '下一代上网行为管理',
            'plant_desc_potatomine': '零信任防护平台',
            'plant_desc_squash': '数据安全平台',
            'plant_desc_spikeweed': '零信任访问控制系统',
            'plant_desc_jalapeno': 'AI安全平台',

            # Common
            'seconds': '秒',
            'points': '分',
            'loading': '加载中...',
        }

    def _load_english(self):
        """英文翻译"""
        return {
            # Loading Screen
            'loading_story_1': 'In the wave of digital intelligence, enterprise core assets are facing unprecedented threats!',
            'loading_story_2': 'You are the Chief Security Officer, empowered by Sangfor GPT AI engine to build the last line of digital defense.',
            'loading_story_3': 'This is not a prolonged battle, but a 2-minute extreme survival challenge.',
            'loading_story_4': 'Facing the onslaught of virus variants and hacker attacks, deploy Sangfor security products to protect enterprise data!',

            # Login Screen
            'login_title': 'GPT Powered: Security Defense',
            'login_name': 'Name:',
            'login_employee_id': 'Employee ID:',
            'login_button': 'Start Game',
            'login_language': 'Language',
            'login_switch_language': '中文',
            'login_offline_mode': 'Offline Mode',
            'login_connecting': 'Connecting to server...',
            'login_error': 'Login failed: ',
            'login_name_empty': 'Please enter your name',
            'login_id_empty': 'Please enter your employee ID',

            # Settings
            'settings_button': 'Settings',
            'settings_title': 'Server Settings',
            'settings_server_url': 'Server URL:',
            'settings_test': 'Test',
            'settings_save': 'Save',
            'settings_cancel': 'Cancel',
            'settings_test_success': 'Connected',
            'settings_test_failed': 'Connection Failed',
            'settings_save_success': 'Saved',
            'settings_save_failed': 'Save Failed',

            # Main Menu
            'menu_adventure': 'Adventure',
            'menu_crazy_mode': 'Crazy Mode',

            # Game UI
            'game_score': 'Score: ',
            'game_time': 'Time: ',
            'game_kills': 'Kills: ',
            'game_sun': 'Sun: ',

            # Game Report
            'report_title': 'Game Report',
            'report_score_card': 'Game Score',
            'report_final_score': 'Final Score: ',
            'report_rank': 'Rank: ',
            'report_duration': 'Duration: ',
            'report_kills_title': 'Kill Statistics',
            'report_total_kills': 'Total Kills: {}',
            'report_count_unit': '{}',
            'report_leaderboard': 'Leaderboard',
            'report_export': 'Export Screenshot',
            'report_play_again': 'Play Again',
            'report_exit': 'Exit Game',
            'report_offline': 'Offline Mode (No Ranking)',
            'report_rank_format': 'Rank #{}',
            'report_no_rank': 'Not Ranked',

            # Zombie Names
            'zombie_preview_title': 'Zombies in This Level',
            'zombie_normal': 'Trojan Zombie',
            'zombie_conehead': 'Ransomware Zombie',
            'zombie_buckethead': 'SilverFox Zombie',
            'zombie_flag': 'Phishing Zombie',
            'zombie_newspaper': 'Exploit Zombie',

            # Plant Tooltip
            'plant_tooltip_prototype': 'Prototype',
            'plant_name_sunflower': 'Sunflower',
            'plant_name_peashooter': 'Peashooter',
            'plant_name_snowpeashooter': 'Snow Pea',
            'plant_name_wallnut': 'Wall-nut',
            'plant_name_cherrybomb': 'Cherry Bomb',
            'plant_name_threepeashooter': 'Threepeater',
            'plant_name_repeaterpea': 'Repeater',
            'plant_name_chomper': 'Chomper',
            'plant_name_potatomine': 'Potato Mine',
            'plant_name_squash': 'Squash',
            'plant_name_spikeweed': 'Spikeweed',
            'plant_name_jalapeno': 'Jalapeno',
            'plant_desc_sunflower': 'Sun is AI power, guardrails are AI guardrails',
            'plant_desc_peashooter': 'Endpoint Antivirus',
            'plant_desc_repeaterpea': 'Endpoint Detection & Response',
            'plant_desc_threepeashooter': 'Extended Detection & Response Platform',
            'plant_desc_snowpeashooter': 'Security Intelligence Platform',
            'plant_desc_wallnut': 'AF+SASE Network Security Solution',
            'plant_desc_cherrybomb': 'Managed Security Service',
            'plant_desc_chomper': 'Next-Gen Internet Behavior Management',
            'plant_desc_potatomine': 'Zero Trust Protection Platform',
            'plant_desc_squash': 'Data Security Platform',
            'plant_desc_spikeweed': 'Zero Trust Access Control System',
            'plant_desc_jalapeno': 'AI Security Platform',

            # Common
            'seconds': 's',
            'points': 'pts',
            'loading': 'Loading...',
        }

    def get(self, key, default=''):
        """获取翻译文本"""
        return self.translations.get(self.current_language, {}).get(key, default)

    def set_language(self, language):
        """切换语言"""
        if language in self.translations:
            self.current_language = language
            return True
        return False

    def get_current_language(self):
        """获取当前语言"""
        return self.current_language


# 创建全局语言管理器实例
LANG = LanguageManager()
