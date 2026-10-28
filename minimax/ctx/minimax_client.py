"""让 MiniMax 根据上下文完成代码修改，并记录全过程。

用法：
    python ctx/minimax_client.py --task "为 list 命令增加按优先级筛选"           # 只生成，不落盘
    python ctx/minimax_client.py --task "为 list 命令增加按优先级筛选" --apply   # 生成并写回 biz/todo.py

产物：
    logs/minimax_session.md   任务 + 上下文来源 + prompt + 模型原始返回 + 最终代码
    logs/patch.diff           修改前后差异
"""
import ast
import datetime
import difflib
import json
import os
import re
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import mask  # noqa: E402
from db import connect  # noqa: E402
from query import build_context  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(ROOT, "biz", "todo.py")
LOGS = os.path.join(ROOT, "logs")
SESSION_MD = os.path.join(LOGS, "minimax_session.md")
PATCH_DIFF = os.path.join(LOGS, "patch.diff")
TARGET_FUNC = "list_items"


def fetch_docs(items):
    """按 source(path#L) + symbol 从 seekdb 取回正文。"""
    out = []
    with connect() as conn:
        with conn.cursor() as cur:
            for it in items:
                path = it["source"].split("#")[0]
                cur.execute(
                    "SELECT path, symbol, title, content, lineno FROM context_docs "
                    "WHERE path=%s AND symbol=%s",
                    (path, it["symbol"]),
                )
                row = cur.fetchone()
                if row:
                    out.append({"path": row[0], "symbol": row[1], "title": row[2],
                                "content": row[3], "lineno": row[4]})
    return out


def build_prompt(task, specs, code, tests):
    def block(docs):
        return "\n\n".join("### %s (%s)\n%s" % (d["title"] or d["symbol"], d["path"], d["content"]) for d in docs)

    return """你是代码修改助手。请严格按下面的规格修改代码。

【任务】
%s

【必须遵守的规格】
%s

【需要修改的函数（当前实现）】
%s

【修改后必须通过的测试】
%s

【输出要求】
1. 只输出修改后的 `%s` 函数完整源码（从 def 开始到函数结束），放在一个 ```python 代码块里。
2. 不要输出解释、不要输出测试代码、不要输出其他函数。
3. 保持函数名、参数名和默认值不变，确保既有行为（不传 priority 时返回全部）不受影响。
""" % (task, block(specs), block(code), block(tests), TARGET_FUNC)


def call_minimax(prompt):
    key = os.environ.get("MINIMAX_API_KEY", "")
    base = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1").rstrip("/")
    model = os.environ.get("MINIMAX_MODEL", "MiniMax-Text-01")
    r = requests.post(
        base + "/text/chatcompletion_v2",
        headers={"Authorization": "Bearer %s" % key, "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "你是严谨的 Python 工程师，只输出代码。"},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1500,
            "temperature": 0.2,
        },
        timeout=120,
    )
    data = r.json()
    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return r.status_code, data.get("base_resp", {}), text, model


def extract_code(text):
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    code = m.group(1) if m else text
    return code.strip() + "\n"


def replace_function(source, func_name, new_src):
    """用 AST 定位函数在原文中的行范围，整体替换。"""
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            start, end = node.lineno - 1, node.end_lineno
            return "\n".join(lines[:start] + new_src.rstrip("\n").splitlines() + lines[end:]) + "\n"
    raise RuntimeError("函数 %s 未找到" % func_name)


def write_log(task, ctx, prompt, status, base_resp, raw, code, applied):
    os.makedirs(LOGS, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sources = []
    for key in ("specs", "code", "tests"):
        for it in ctx.get(key, []):
            sources.append("- [%s] `%s` %s" % (key, it["source"], it["symbol"]))

    entry = """## 会话记录 %s

- 模型：`%s`
- 任务：%s
- API：HTTP %s，base_resp=%s

### 使用的上下文来源

%s

### Prompt

```text
%s
```

### 模型原始返回

```text
%s
```

### 提取出的代码

```python
%s```

### 是否写回源码

%s

---

""" % (ts, os.environ.get("MINIMAX_MODEL", ""), task, status,
       json.dumps(base_resp, ensure_ascii=False),
       "\n".join(sources), prompt, raw, code, "已写回 biz/todo.py" if applied else "未写回（仅生成）")

    header = "" if os.path.exists(SESSION_MD) else "# MiniMax 开发记录\n\n"
    with open(SESSION_MD, "a", encoding="utf-8") as f:
        f.write(header + entry)


def write_diff(old, new):
    os.makedirs(LOGS, exist_ok=True)
    diff = difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile="biz/todo.py (修改前)", tofile="biz/todo.py (修改后)", n=3,
    )
    with open(PATCH_DIFF, "w", encoding="utf-8") as f:
        f.writelines(diff)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    print("API Key:", mask(os.environ.get("MINIMAX_API_KEY", "")))

    ctx = build_context(args.task)
    specs = fetch_docs(ctx["specs"])
    codes = fetch_docs(ctx["code"])
    tests = fetch_docs(ctx["tests"])

    print("上下文：spec %d 条 / code %d 条 / test %d 条" % (len(specs), len(codes), len(tests)))

    prompt = build_prompt(args.task, specs, codes, tests)
    status, base_resp, raw, model = call_minimax(prompt)

    print("HTTP", status, "base_resp", base_resp)
    code = extract_code(raw)
    print("\n--- 模型返回的代码 ---\n" + code)

    applied = False
    if args.apply:
        source = open(TARGET, encoding="utf-8").read()
        new_source = replace_function(source, TARGET_FUNC, code)
        ast.parse(new_source)          # 语法校验，不合法会抛异常
        if not os.path.exists(os.path.join(LOGS, "todo.py.before")):
            os.makedirs(LOGS, exist_ok=True)
            open(os.path.join(LOGS, "todo.py.before"), "w", encoding="utf-8").write(source)
        write_diff(source, new_source)
        open(TARGET, "w", encoding="utf-8").write(new_source)
        applied = True
        print("\n已写回 biz/todo.py，差异见 logs/patch.diff")

    write_log(args.task, ctx, prompt, status, base_resp, raw, code, applied)
    print("日志已追加到 logs/minimax_session.md")
