"""
服务器配置
"""
import os

# 服务器端口
PORT = int(os.environ.get('FLASK_PORT', 5000))

# 监听地址 (0.0.0.0 表示监听所有网络接口，可在局域网内访问)
HOST = os.environ.get('FLASK_HOST', '0.0.0.0')

# 数据库路径
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'game.db')

# 调试模式
DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'
