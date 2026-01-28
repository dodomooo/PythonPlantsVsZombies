__author__ = 'marble_xu'

import configparser
import os
import requests


class NetworkManager:
    """网络管理器，负责与服务器通信"""

    def __init__(self):
        self.server_url = 'http://127.0.0.1:5000'  # 使用 127.0.0.1 避免 DNS 解析
        self.timeout = 3  # 减少超时时间
        self.session = requests.Session()  # 复用 TCP 连接
        self.load_config()

    def load_config(self):
        """从配置文件加载服务器设置"""
        try:
            config = configparser.ConfigParser()
            config_path = os.path.join('source', 'config.ini')
            config.read(config_path)

            if 'Server' in config:
                self.server_url = config['Server'].get('url', self.server_url)
                self.timeout = int(config['Server'].get('timeout', self.timeout))
        except Exception as e:
            print(f'Failed to load config: {e}')

    def check_connection(self):
        """
        检查服务器连接
        Returns:
            bool: 如果连接成功返回 True
        """
        try:
            response = self.session.get(f'{self.server_url}/api/health', timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            print(f'Connection check failed: {e}')
            return False

    def login(self, name, employee_id):
        """
        玩家登录/注册
        Args:
            name: 玩家姓名
            employee_id: 工号
        Returns:
            dict: 包含 player_id 的字典，失败时抛出异常
        """
        try:
            response = self.session.post(
                f'{self.server_url}/api/login',
                json={'name': name, 'employee_id': employee_id},
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f'Login failed with status {response.status_code}')
        except requests.Timeout:
            raise Exception('服务器连接超时')
        except requests.ConnectionError:
            raise Exception('无法连接到服务器')
        except Exception as e:
            raise Exception(f'登录失败: {str(e)}')

    def submit_score(self, player_id, score, game_duration, zombies_killed):
        """
        提交游戏成绩
        Args:
            player_id: 玩家ID
            score: 最终分数
            game_duration: 游戏时长（毫秒）
            zombies_killed: 僵尸击杀统计字典
        Returns:
            dict: 包含 rank 的字典，失败时抛出异常
        """
        try:
            # 将击杀统计转换为服务器需要的格式
            zombie_details = []
            for zombie_type, count in zombies_killed.items():
                if count > 0:
                    zombie_details.append({
                        'zombie_type': zombie_type,
                        'count': count
                    })

            response = self.session.post(
                f'{self.server_url}/api/submit_score',
                json={
                    'player_id': player_id,
                    'score': score,
                    'game_duration': game_duration,
                    'zombie_details': zombie_details
                },
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f'Submit score failed with status {response.status_code}')
        except Exception as e:
            raise Exception(f'提交成绩失败: {str(e)}')

    def get_leaderboard(self, limit=10):
        """
        获取排行榜
        Args:
            limit: 返回的记录数
        Returns:
            list: 排行榜记录列表，失败时抛出异常
        """
        try:
            response = self.session.get(
                f'{self.server_url}/api/leaderboard',
                params={'limit': limit},
                timeout=self.timeout
            )
            if response.status_code == 200:
                return response.json().get('leaderboard', [])
            else:
                raise Exception(f'Get leaderboard failed with status {response.status_code}')
        except Exception as e:
            raise Exception(f'获取排行榜失败: {str(e)}')


# 创建全局网络管理器实例
NETWORK = NetworkManager()
