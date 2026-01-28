# 快速开始

## 安装依赖
```bash
pip install -r requirements.txt
```

## 启动游戏

### 🚀 一键启动（推荐）

**Windows**
```bash
start.bat          # 或双击运行
```

**Linux / macOS**
```bash
chmod +x start.sh  # 首次需要
./start.sh
```

脚本会自动检测依赖、提供图形菜单，并管理服务器进程。

---

## 配置

编辑 `source/config.ini` 修改服务器地址或语言：

```ini
[Server]
url = http://127.0.0.1:5000    # 局域网部署改为服务器IP
timeout = 3

[Game]
language = zh_CN               # 语言：zh_CN 或 en_US
default_level = 0              # 起始关卡
```

## 游戏流程

1. **加载界面**（10秒）
2. **登录页面**（输入姓名和工号，Tab切换输入框）
3. **主菜单**（点击 Adventure）
4. **疯狂模式**（120秒，初始阳光1000，显示分数/时间/击杀数）
5. **游戏报告**（显示排名、分数、击杀统计，可导出截图）


**开始游戏！** 🌻🧟‍♂️
