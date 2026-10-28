"""按开发任务检索上下文，输出 JSON 给 AI 助手。

用法：
    python ctx/query.py --task "为 list 命令增加按优先级筛选"

输出结构（题目 2.3 要求）：
    specs / code / tests   —— 来源必须是真实文件+行号
    state                  —— 已完成 / 待办 / 已有验证结果
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import connect, log_sql  # noqa: E402
from state import load_state  # noqa: E402

STOP = set("的 了 和 在 为 对 与 及 或 把 被 用 到 从 让 使 中 上 下 一 个 是 有 要 需要 支持 实现 增加".split())

KIND_LIMIT = {"spec": 6, "code": 6, "test": 6}


def tokenize(task):
    """中英混合的粗粒度分词：中文按 2 字滑窗，英文按单词。"""
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]+", task)
    cjk = re.findall(r"[\u4e00-\u9fa5]+", task)
    for seg in cjk:
        for i in range(0, max(1, len(seg) - 1)):
            w = seg[i:i + 2]
            if w not in STOP:
                words.append(w)
    return list(dict.fromkeys(w.lower() for w in words if w))


def score(content, tokens):
    low = content.lower()
    return sum(low.count(t) for t in tokens)


SQL_ALL = "SELECT path, symbol, kind, title, content, lineno, version FROM context_docs"


def fetch_all():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(SQL_ALL)
            cols = [c[0] for c in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    log_sql(SQL_ALL, rows=len(rows))
    return rows


def build_context(task):
    tokens = tokenize(task)
    docs = fetch_all()

    ranked = []
    for d in docs:
        s = score(d["content"] + " " + d["title"] + " " + d["path"], tokens)
        if s > 0:
            ranked.append((s, d))
    ranked.sort(key=lambda x: (-x[0], x[1]["path"], x[1]["lineno"]))

    picked = {"spec": [], "code": [], "test": []}
    for s, d in ranked:
        bucket = picked.setdefault(d["kind"], [])
        if len(bucket) < KIND_LIMIT.get(d["kind"], 3):
            bucket.append({
                "source": "%s#L%d" % (d["path"], d["lineno"]),
                "symbol": d["symbol"],
                "title": d["title"],
                "score": s,
                "version": d["version"],
            })

    st = load_state()
    return {
        "task": task,
        "tokens": tokens,
        "specs": picked.get("spec", []),
        "code": picked.get("code", []),
        "tests": picked.get("test", []),
        "state": {
            "done": st.get("done", []),
            "todo": st.get("todo", []),
            "verifications": st.get("verifications", []),
        },
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, help="开发任务描述")
    args = ap.parse_args()
    print(json.dumps(build_context(args.task), ensure_ascii=False, indent=2))
