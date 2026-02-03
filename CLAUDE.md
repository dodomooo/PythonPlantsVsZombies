# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

基于 Python + Pygame 的植物大战僵尸风格游戏，主题为企业安全防御。包含用户登录、排行榜、多语言支持等功能。

## 运行方式

```bash
# 启动游戏（需先启动服务器，或使用离线模式）
python main.py

# 启动服务器
python start_server.py
```

**依赖**:
- 游戏: pygame==1.9.6, requests
- 服务器: Flask, Flask-CORS

## 代码架构

### 目录结构

```
source/
├── main.py              # 游戏入口
├── tool.py              # 核心工具类：Control、State、图像加载
├── constants.py         # 游戏常量（含缩放系统）
├── language.py          # 多语言管理器（中/英）
├── network.py           # 网络通信管理器
├── state/               # 游戏状态
│   ├── loading.py       # 加载屏幕
│   ├── login.py         # 登录界面
│   ├── mainmenu.py      # 主菜单
│   ├── level.py         # 关卡主逻辑
│   ├── screen.py        # 胜利/失败屏幕
│   └── report.py        # 游戏结算报告
├── component/           # 游戏实体
│   ├── plant.py         # 植物、子弹、阳光
│   ├── zombie.py        # 僵尸
│   ├── map.py           # 地图网格
│   └── menubar.py       # 植物卡片栏
└── data/
    ├── entity/          # 实体配置 JSON
    └── map/             # 关卡配置 JSON

server/                  # Flask 后端服务
├── server.py            # 服务器入口
├── api.py               # API 路由
├── database.py          # 数据库操作
├── config.py            # 配置
└── models.py            # 数据模型
```

### 核心设计模式

**状态机模式**: `tool.Control` 管理游戏状态转换
- 主流程: LOGIN_SCREEN → LOADING_SCREEN → LEVEL → GAME_REPORT
- 所有状态继承 `tool.State` 基类

**精灵组管理**: 按地图行组织，便于碰撞检测
- 每行有独立的 plant_groups、zombie_groups、bullet_groups

**缩放系统**: `constants.py` 中的 `RENDER_SCALE` 控制渲染分辨率
- 所有尺寸通过 `scale()` 函数计算
- 支持高清资源自动缩放

### 坐标系统

- 逻辑基准: 800×600 像素
- 游戏网格: 9×5 (GRID_X_LEN × GRID_Y_LEN)
- 每格大小: 80×100 像素 (基准值)
- `map.Map` 类提供网格/像素坐标转换

### 游戏模式

- **冒险模式**: level_0 ~ level_5
- **疯狂模式**: level_crazy.json，2分钟限时生存

## 常见开发任务

### 添加新植物

1. `constants.py`: 定义植物名称和卡片常量
2. `component/plant.py`: 创建植物类
3. `component/menubar.py`: 添加卡片信息
4. `data/entity/plant.json`: 添加图像矩形数据
5. `resources/graphics/Plants/`: 放置动画帧

### 添加新僵尸

1. `constants.py`: 定义僵尸名称和属性常量
2. `component/zombie.py`: 创建僵尸子类
3. `data/entity/zombie.json`: 添加图像矩形数据
4. 关卡 JSON: 配置生成时间和位置

### 添加新翻译

`language.py`: 在 `_load_chinese()` 和 `_load_english()` 中添加对应键值

## 代码约定

- 时间单位: 毫秒
- 网格坐标: (x, y) = (列, 行)
- 状态常量集中在 `constants.py`
- 图像透明度使用 Pygame colorkey
