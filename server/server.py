"""
Flask 服务器主程序
"""

import os
import sys
import webbrowser
import threading
from flask import Flask, send_from_directory
from flask_cors import CORS
from .api import api
from . import config

def create_app():
    """创建 Flask 应用"""
    # 获取静态文件目录路径
    static_folder = os.path.join(os.path.dirname(__file__), 'static')

    app = Flask(__name__, static_folder=static_folder)

    # 启用 CORS 支持跨域请求
    CORS(app)

    # 注册 API 蓝图
    app.register_blueprint(api, url_prefix='/api')

    # 根路由返回排行榜页面
    @app.route('/')
    def index():
        return send_from_directory(static_folder, 'index.html')

    return app


def main():
    """启动服务器"""
    werkzeug_run_main = os.environ.get('WERKZEUG_RUN_MAIN')

    app = create_app()

    # 构造访问地址
    url = f'http://localhost:{config.PORT}'

    print(f'Starting server on {config.HOST}:{config.PORT}')
    print(f'Access the server at {url}')
    print('Press Ctrl+C to stop the server')

    # 只在主进程中打开浏览器（避免 reloader 重启时重复打开）
    # 主进程的 WERKZEUG_RUN_MAIN 为 None，子进程为 'true'
    # Docker 环境下不自动打开浏览器
    is_docker = os.path.exists('/.dockerenv') or os.environ.get('DATABASE_PATH', '').startswith('/app/')
    if not werkzeug_run_main and not is_docker:
        def open_browser():
            print(f'Opening browser at {url}', flush=True)
            try:
                if sys.platform == 'win32':
                    # Windows: 使用 os.startfile 直接调用系统 URL 处理
                    os.startfile(url)
                else:
                    webbrowser.open(url)
            except Exception as e:
                print(f'Failed to open browser: {e}', flush=True)

        # 使用定时器在1秒后打开浏览器
        timer = threading.Timer(1.0, open_browser)
        timer.daemon = True
        timer.start()

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )


if __name__ == '__main__':
    main()
