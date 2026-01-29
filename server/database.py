"""
数据库操作封装
"""

import sqlite3
import os
from . import models
from . import config


class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DATABASE_PATH
        self.init_db()

    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(models.PLAYERS_TABLE)
        cursor.execute(models.GAME_RECORDS_TABLE)
        cursor.execute(models.ZOMBIE_KILLS_TABLE)

        conn.commit()
        conn.close()
        print('Database initialized')

    def get_or_create_player(self, name, employee_id):
        """
        获取或创建玩家（工号唯一标识）
        Args:
            name: 玩家姓名
            employee_id: 工号（唯一标识）
        Returns:
            int: 玩家ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # 只用 employee_id 查询
        cursor.execute(
            'SELECT id, name FROM players WHERE employee_id = ?',
            (employee_id,)
        )
        row = cursor.fetchone()

        if row:
            player_id = row['id']
            old_name = row['name']
            # 如果姓名不同，更新姓名
            if old_name != name:
                cursor.execute(
                    'UPDATE players SET name = ? WHERE id = ?',
                    (name, player_id)
                )
                conn.commit()
                print(f'Updated player name: {old_name} -> {name} (employee_id={employee_id})')
        else:
            # 创建新玩家
            cursor.execute(
                'INSERT INTO players (name, employee_id) VALUES (?, ?)',
                (name, employee_id)
            )
            player_id = cursor.lastrowid
            conn.commit()

        conn.close()
        return player_id

    def add_game_record(self, player_id, score, game_duration, zombie_details):
        """
        添加游戏记录
        Args:
            player_id: 玩家ID
            score: 分数
            game_duration: 游戏时长（毫秒）
            zombie_details: 僵尸击杀详情列表 [{'zombie_type': 'Zombie', 'count': 10}, ...]
        Returns:
            tuple: (game_record_id, rank)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # 插入游戏记录
        cursor.execute(
            'INSERT INTO game_records (player_id, score, game_duration) VALUES (?, ?, ?)',
            (player_id, score, game_duration)
        )
        game_record_id = cursor.lastrowid

        # 插入僵尸击杀详情
        for detail in zombie_details:
            cursor.execute(
                'INSERT INTO zombie_kills (game_record_id, zombie_type, count) VALUES (?, ?, ?)',
                (game_record_id, detail['zombie_type'], detail['count'])
            )

        conn.commit()

        # 计算排名（按每个玩家的最高分去重）
        cursor.execute('''
            SELECT COUNT(DISTINCT p.employee_id) + 1 as rank
            FROM (
                SELECT p2.employee_id, MAX(g2.score) as max_score
                FROM game_records g2
                JOIN players p2 ON g2.player_id = p2.id
                GROUP BY p2.employee_id
            ) p
            WHERE p.max_score > (
                SELECT MAX(g3.score)
                FROM game_records g3
                WHERE g3.player_id = ?
            )
        ''', (player_id,))
        rank = cursor.fetchone()['rank']

        conn.close()
        return game_record_id, rank

    def get_leaderboard(self, limit=10):
        """
        获取排行榜（每个工号只显示最高分）
        Args:
            limit: 返回记录数
        Returns:
            list: 排行榜记录列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # 使用子查询为每个 employee_id 选择最高分的记录
        cursor.execute('''
            SELECT p.name, p.employee_id, g.score, g.game_duration, g.created_at
            FROM game_records g
            JOIN players p ON g.player_id = p.id
            WHERE g.id IN (
                SELECT g2.id
                FROM game_records g2
                JOIN players p2 ON g2.player_id = p2.id
                WHERE p2.employee_id = p.employee_id
                ORDER BY g2.score DESC, g2.created_at ASC
                LIMIT 1
            )
            ORDER BY g.score DESC, g.created_at ASC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        leaderboard = []
        for row in rows:
            leaderboard.append({
                'name': row['name'],
                'employee_id': row['employee_id'],
                'score': row['score'],
                'game_duration': row['game_duration'],
                'created_at': row['created_at']
            })

        conn.close()
        return leaderboard

    def get_player_history(self, player_id, limit=10):
        """
        获取玩家历史记录
        Args:
            player_id: 玩家ID
            limit: 返回记录数
        Returns:
            list: 历史记录列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT score, game_duration, created_at
            FROM game_records
            WHERE player_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (player_id, limit))

        rows = cursor.fetchall()
        history = []
        for row in rows:
            history.append({
                'score': row['score'],
                'game_duration': row['game_duration'],
                'created_at': row['created_at']
            })

        conn.close()
        return history
