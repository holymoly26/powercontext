"""seekdb / OceanBase 连接封装（MySQL 协议，默认 2881 端口）。

依赖：pip install pymysql
"""
import os

import pymysql


def connect():
    return pymysql.connect(
        host=os.environ.get("SEEKDB_HOST", "127.0.0.1"),
        port=int(os.environ.get("SEEKDB_PORT", "2881")),
        user=os.environ.get("SEEKDB_USER", "root"),
        password=os.environ.get("SEEKDB_PASSWORD", ""),
        database=os.environ.get("SEEKDB_DB", "sdd"),
        charset="utf8mb4",
        autocommit=True,
    )


def ping():
    """连通性检查，返回数据库版本。"""
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            return cur.fetchone()[0]


if __name__ == "__main__":
    print("connected:", ping())
