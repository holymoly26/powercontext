"""seekdb / OceanBase 连接封装（MySQL 协议，默认 2881 端口）。

依赖：pip install pymysql

提供：
    connect()      连接（默认库 sdd）
    ping()         连通性检查
    init_schema()  直接执行 schema.sql 建库建表（不需要 mysql 客户端）
    log_sql()      把执行的 SQL 追加到 logs/sql_query.log（技术使用记录）
"""
import datetime
import os
import re

import pymysql

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQL_LOG = os.path.join(ROOT, "logs", "sql_query.log")
SCHEMA_FILE = os.path.join(ROOT, "schema.sql")

DB_NAME = os.environ.get("SEEKDB_DB", "sdd")


def _params():
    return dict(
        host=os.environ.get("SEEKDB_HOST", "127.0.0.1"),
        port=int(os.environ.get("SEEKDB_PORT", "2881")),
        user=os.environ.get("SEEKDB_USER", "root"),
        password=os.environ.get("SEEKDB_PASSWORD", ""),
        charset="utf8mb4",
        autocommit=True,
    )


def connect():
    return pymysql.connect(database=DB_NAME, **_params())


def connect_server():
    """不指定库的连接，用于建库。"""
    return pymysql.connect(**_params())


def log_sql(sql, rows=None, ok=True):
    """把 SQL 与影响行数追加到 logs/sql_query.log。"""
    os.makedirs(os.path.dirname(SQL_LOG), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    one_line = re.sub(r"\s+", " ", sql).strip()
    if len(one_line) > 300:
        one_line = one_line[:297] + "..."
    flag = "OK" if ok else "FAIL"
    extra = "" if rows is None else " rows=%s" % rows
    with open(SQL_LOG, "a", encoding="utf-8") as f:
        f.write("%s [%s]%s %s\n" % (ts, flag, extra, one_line))


def init_schema():
    """执行 schema.sql：建库 + 建表（幂等）。返回执行的语句数。"""
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        raw = f.read()

    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    statements = [s.strip() for s in "\n".join(lines).split(";") if s.strip()]

    conn = connect_server()
    try:
        with conn.cursor() as cur:
            for stmt in statements:
                try:
                    cur.execute(stmt)
                    log_sql(stmt, rows=cur.rowcount)
                except Exception as e:
                    log_sql(stmt, ok=False)
                    raise RuntimeError("执行失败：%s\n%s" % (e, stmt)) from e
    finally:
        conn.close()
    return len(statements)


def ping():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            v = cur.fetchone()[0]
    log_sql("SELECT VERSION()", rows=1)
    return v


if __name__ == "__main__":
    print("connected:", ping())
