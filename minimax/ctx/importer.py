"""把工程资料切块导入 seekdb。

用法：
    python ctx/importer.py --root biz
"""
import argparse
import ast
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import connect  # noqa: E402

# 文件 -> 资料类型
KIND_BY_DIR = {"docs": "spec", "tests": "test", "test": "test"}


def kind_of(rel_path):
    parts = rel_path.replace("\\", "/").split("/")
    for p in parts[:-1]:
        if p in KIND_BY_DIR:
            return KIND_BY_DIR[p]
    return "code"


def chunk_markdown(text):
    """按二级标题切分，标题名作为唯一符号，避免同一文件被覆盖。"""
    blocks = []
    cur_title, buf, start = "", [], 1
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            if buf:
                blocks.append((cur_title, "\n".join(buf).strip(), start))
            cur_title, buf, start = line[3:].strip(), [line], lineno
        else:
            buf.append(line)
    if buf:
        blocks.append((cur_title, "\n".join(buf).strip(), start))

    out = []
    for title, content, lineno in blocks:
        if not content:
            continue
        symbol = "section:%s" % (title or "preamble")
        out.append((symbol, title or "preamble", content, lineno))
    return out


def chunk_python(text):
    """按顶层函数和方法切分，符号名唯一。"""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [("", "", text, 1)]

    lines = text.splitlines()

    def seg(node):
        return "\n".join(lines[node.lineno - 1: node.end_lineno])

    out = []

    def visit(body, prefix=""):
        for node in body:
            if isinstance(node, ast.FunctionDef):
                out.append(("function:%s%s" % (prefix, node.name), node.name, seg(node), node.lineno))
            elif isinstance(node, ast.ClassDef):
                visit(node.body, prefix + node.name + ".")

    visit(tree.body)
    return out or [("", "", text, 1)]


def iter_docs(root):
    for dirpath, _, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.endswith((".md", ".py")):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            with open(full, "r", encoding="utf-8") as f:
                text = f.read()
            kind = kind_of(rel)
            chunks = chunk_markdown(text) if fn.endswith(".md") else chunk_python(text)
            for symbol, title, content, lineno in chunks:
                yield dict(path=rel, symbol=symbol, kind=kind,
                           title=title, content=content, lineno=lineno)


UPSERT = """
INSERT INTO context_docs (path, symbol, kind, title, content, lineno, version)
VALUES (%(path)s, %(symbol)s, %(kind)s, %(title)s, %(content)s, %(lineno)s, 1)
ON DUPLICATE KEY UPDATE
    content = VALUES(content), title = VALUES(title),
    lineno = VALUES(lineno), version = version + 1
"""


def import_docs(root):
    docs = list(iter_docs(root))
    with connect() as conn:
        with conn.cursor() as cur:
            for d in docs:
                cur.execute(UPSERT, d)
    return len(docs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="biz", help="资料根目录")
    ap.add_argument("--reset", action="store_true", help="先清空表")
    args = ap.parse_args()

    if args.reset:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE context_docs")
        print("table truncated")

    n = import_docs(args.root)
    print("imported %d documents from %s" % (n, args.root))
