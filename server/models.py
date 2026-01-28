"""
数据模型定义
"""

# SQLite 表结构定义

PLAYERS_TABLE = """
CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    employee_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

GAME_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS game_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    game_duration INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id)
)
"""

ZOMBIE_KILLS_TABLE = """
CREATE TABLE IF NOT EXISTS zombie_kills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_record_id INTEGER NOT NULL,
    zombie_type TEXT NOT NULL,
    count INTEGER NOT NULL,
    FOREIGN KEY (game_record_id) REFERENCES game_records(id)
)
"""
