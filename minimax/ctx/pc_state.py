"""用 PowerContext 保存/复用任务状态。

接口与 state.py 保持一致：
    load_state() -> {"done": [...], "todo": [...], "verifications": [...], "backend": "powercontext"}
    append(bucket, text)

底层调用 PowerContext Server（默认 http://127.0.0.1:8000）：
    POST /v1/scopes             创建（或复用）Scope
    POST /v1/memory/remember    写入 Memory
    POST /v1/memory/search      按前缀检索，还原三类状态

所有调用追加到 logs/powercontext.log，作为技术使用记录。
"""
import datetime
import json
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.environ.get("POWERCONTEXT_URL", "http://127.0.0.1:8000").rstrip("/")
SCOPE_CACHE = os.path.join(ROOT, ".pc_scope")
PC_LOG = os.path.join(ROOT, "logs", "powercontext.log")

PREFIX = {"done": "DONE: ", "todo": "TODO: ", "verifications": "VERIFY: "}
KIND = {"done": "state", "todo": "next_step", "verifications": "fact"}
BUCKETS = ("done", "todo", "verifications")


def _log(method, path, status, detail=""):
    os.makedirs(os.path.dirname(PC_LOG), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PC_LOG, "a", encoding="utf-8") as f:
        f.write("%s %s %s%s -> HTTP %s %s\n" % (ts, method, BASE, path, status, detail))


def _post(path, payload):
    r = requests.post(BASE + path, json=payload, timeout=20)
    _log("POST", path, r.status_code, payload.get("kind", ""))
    r.raise_for_status()
    return r.json()


def available():
    try:
        return requests.get(BASE + "/health/live", timeout=3).status_code == 200
    except Exception:
        return False


def ensure_scope():
    """复用或创建 Scope，返回 scope_id。"""
    if os.path.exists(SCOPE_CACHE):
        sid = open(SCOPE_CACHE, encoding="utf-8").read().strip()
        if sid:
            return sid
    data = _post("/v1/scopes", {
        "title": "minimax-sdd-context",
        "summary": "SDD 上下文管理系统的任务状态",
        "idempotency_key": "minimax-sdd-context",
    })
    sid = data["scope_id"]
    with open(SCOPE_CACHE, "w", encoding="utf-8") as f:
        f.write(sid)
    return sid


def append(bucket, text):
    """把一条状态写入 PowerContext。"""
    sid = ensure_scope()
    try:
        _post("/v1/memory/remember", {
            "scope_id": sid,
            "kind": KIND[bucket],
            "text": PREFIX[bucket] + text,
            "reason": "SDD 任务状态记录",
        })
    except requests.HTTPError:
        _post("/v1/memory/remember", {
            "scope_id": sid,
            "kind": "state",
            "text": PREFIX[bucket] + text,
            "reason": "SDD 任务状态记录（kind 回退）",
        })
    return load_state()


def load_state():
    """从 PowerContext 读回三类状态。"""
    sid = ensure_scope()
    out = {k: [] for k in BUCKETS}
    out["backend"] = "powercontext"
    seen = set()

    for bucket in BUCKETS:
        try:
            data = _post("/v1/memory/search", {
                "scope_id": sid,
                "query": PREFIX[bucket].strip(),
                "limit": 50,
            })
        except requests.HTTPError:
            continue
        for hit in data.get("hits", []):
            mem = hit.get("memory") or {}
            text = mem.get("text") or ""
            aid = (mem.get("artifact") or {}).get("artifact_id")
            if aid in seen:
                continue
            if text.startswith(PREFIX[bucket]):
                seen.add(aid)
                out[bucket].append(text[len(PREFIX[bucket]):])
    return out
