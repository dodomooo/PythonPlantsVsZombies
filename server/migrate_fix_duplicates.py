"""
数据清理脚本 - 删除重复玩家记录
功能：
1. 自动备份数据库
2. 识别同一工号的重复玩家记录
3. 保留最早创建的记录，删除其他重复记录
4. 删除重复记录关联的游戏记录
5. 重建表结构，修改 UNIQUE 约束
6. 验证清理结果
"""

import sqlite3
import shutil
from datetime import datetime
import os
import sys

# 设置标准输出编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

__author__ = 'marble_xu'

DATABASE_PATH = 'game.db'


def backup_database():
    """备份数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'{DATABASE_PATH}.backup_{timestamp}'
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f'数据库已备份到: {backup_path}')
    return backup_path


def get_duplicate_employee_ids(conn):
    """查找重复的工号"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT employee_id, COUNT(*) as count
        FROM players
        GROUP BY employee_id
        HAVING count > 1
    ''')
    duplicates = cursor.fetchall()
    return [(row[0], row[1]) for row in duplicates]


def clean_duplicate_players(conn):
    """清理重复的玩家记录"""
    cursor = conn.cursor()

    # 查找重复的工号
    duplicates = get_duplicate_employee_ids(conn)

    if not duplicates:
        print('✓ 未发现重复的工号')
        return

    print(f'发现 {len(duplicates)} 个重复的工号')

    total_deleted_players = 0
    total_deleted_games = 0
    total_deleted_kills = 0

    for employee_id, count in duplicates:
        # 查找该工号的所有玩家记录（按创建时间排序）
        cursor.execute('''
            SELECT id, name, created_at
            FROM players
            WHERE employee_id = ?
            ORDER BY created_at ASC
        ''', (employee_id,))

        players = cursor.fetchall()

        # 保留第一条记录（最早创建的）
        keep_player_id = players[0][0]
        keep_player_name = players[0][1]
        duplicate_player_ids = [p[0] for p in players[1:]]

        print(f'\n清理工号 {employee_id}:')
        print(f'  保留玩家: id={keep_player_id}, name={keep_player_name}')
        print(f'  删除玩家: {duplicate_player_ids}')

        # 删除重复记录关联的游戏击杀详情
        cursor.execute(f'''
            DELETE FROM zombie_kills
            WHERE game_record_id IN (
                SELECT id FROM game_records WHERE player_id IN ({','.join('?' * len(duplicate_player_ids))})
            )
        ''', duplicate_player_ids)
        deleted_kills = cursor.rowcount
        total_deleted_kills += deleted_kills
        if deleted_kills > 0:
            print(f'  删除 {deleted_kills} 条击杀详情')

        # 删除重复记录关联的游戏记录
        cursor.execute(f'''
            DELETE FROM game_records
            WHERE player_id IN ({','.join('?' * len(duplicate_player_ids))})
        ''', duplicate_player_ids)
        deleted_games = cursor.rowcount
        total_deleted_games += deleted_games
        if deleted_games > 0:
            print(f'  删除 {deleted_games} 条游戏记录')

        # 删除重复的玩家记录
        cursor.execute(f'''
            DELETE FROM players
            WHERE id IN ({','.join('?' * len(duplicate_player_ids))})
        ''', duplicate_player_ids)
        deleted_players = cursor.rowcount
        total_deleted_players += deleted_players
        print(f'  删除 {deleted_players} 条重复玩家记录')

    conn.commit()

    print(f'\n总计删除:')
    print(f'  玩家记录: {total_deleted_players} 条')
    print(f'  游戏记录: {total_deleted_games} 条')
    print(f'  击杀详情: {total_deleted_kills} 条')


def recreate_players_table(conn):
    """重建 players 表，修改 UNIQUE 约束"""
    cursor = conn.cursor()

    print('\n重建 players 表...')

    # 创建临时表
    cursor.execute('''
        CREATE TABLE players_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            employee_id TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 复制数据
    cursor.execute('''
        INSERT INTO players_new (id, name, employee_id, created_at)
        SELECT id, name, employee_id, created_at
        FROM players
    ''')

    # 删除旧表
    cursor.execute('DROP TABLE players')

    # 重命名新表
    cursor.execute('ALTER TABLE players_new RENAME TO players')

    conn.commit()
    print('✓ 表结构已更新')


def verify_cleanup(conn):
    """验证清理结果"""
    cursor = conn.cursor()

    print('\n验证清理结果...')

    # 检查是否还有重复工号
    duplicates = get_duplicate_employee_ids(conn)
    if duplicates:
        print(f'❌ 仍有 {len(duplicates)} 个重复工号:')
        for employee_id, count in duplicates:
            print(f'  工号 {employee_id}: {count} 条记录')
        return False
    else:
        print('✓ 无重复工号')

    # 统计总记录数
    cursor.execute('SELECT COUNT(*) FROM players')
    player_count = cursor.fetchone()[0]
    print(f'✓ 玩家总数: {player_count}')

    cursor.execute('SELECT COUNT(*) FROM game_records')
    game_count = cursor.fetchone()[0]
    print(f'✓ 游戏记录总数: {game_count}')

    cursor.execute('SELECT COUNT(*) FROM zombie_kills')
    kill_count = cursor.fetchone()[0]
    print(f'✓ 击杀详情总数: {kill_count}')

    return True


def main():
    """主函数"""
    if not os.path.exists(DATABASE_PATH):
        print(f'❌ 数据库文件不存在: {DATABASE_PATH}')
        return

    print('开始数据清理迁移...\n')

    # 备份数据库
    backup_path = backup_database()

    # 连接数据库
    conn = sqlite3.connect(DATABASE_PATH)

    try:
        # 清理重复玩家
        clean_duplicate_players(conn)

        # 重建表结构
        recreate_players_table(conn)

        # 验证结果
        if verify_cleanup(conn):
            print('\n✓ 迁移完成！')
        else:
            print('\n❌ 迁移验证失败，请检查数据')
            print(f'可以从备份恢复: {backup_path}')

    except Exception as e:
        print(f'\n❌ 迁移失败: {e}')
        conn.rollback()
        print(f'可以从备份恢复: {backup_path}')
        raise

    finally:
        conn.close()


if __name__ == '__main__':
    main()
