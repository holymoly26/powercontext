"""任务状态读写。

双后端：
    powercontext —— 写入 PowerContext Server（默认，需服务在跑）
    file         —— 本地 JSON，作为兜底

切换：设置环境变量 STATE_BACKEND=file 可强制走文件后端。

用法：
    python ctx/state.py show
    python ctx/state.py done "实现 list_items 的 priority 筛选"
    python ctx/state.py todo "补充回归测试"
    python ctx/state.py verify "目标测试 2 项由 FAIL 转 PASS"
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pc_state  # noqa: E402

STATE_FILE = os.environ.get(
    "STATE_FILE",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json"),
)

EMPTY = {"done": [], "todo": [], "verifications": []}


def backend():
    if os.environ.get("STATE_BACKEND", "").lower() == "file":
        return "file"
    return "powercontext" if pc_state.available() else "file"


# ---------------- 文件后端 ----------------

def _file_load():
    if not os.path.exists(STATE_FILE):
        return dict(EMPTY)
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k, v in EMPTY.items():
        data.setdefault(k, list(v))
    return data


def _file_save(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------------- 对外接口 ----------------

def load_state():
    if backend() == "powercontext":
        try:
            return pc_state.load_state()
        except Exception as e:
            print("[warn] PowerContext 读取失败，回退文件后端: %s" % e, file=sys.stderr)
    st = _file_load()
    st["backend"] = "file"
    return st


def save_state(state):
    _file_save(state)
    return state


def append(bucket, text):
    if backend() == "powercontext":
        try:
            return pc_state.append(bucket, text)
        except Exception as e:
            print("[warn] PowerContext 写入失败，回退文件后端: %s" % e, file=sys.stderr)
    st = _file_load()
    st[bucket].append(text)
    _file_save(st)
    st["backend"] = "file"
    return st


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps(load_state(), ensure_ascii=False, indent=2))
        sys.exit(0)

    cmd = sys.argv[1]
    mapping = {"done": "done", "todo": "todo", "verify": "verifications"}
    if cmd == "show":
        print(json.dumps(load_state(), ensure_ascii=False, indent=2))
    elif cmd == "backend":
        print(backend())
    elif cmd in mapping:
        print(json.dumps(append(mapping[cmd], sys.argv[2]), ensure_ascii=False, indent=2))
    else:
        print("usage: state.py [show|backend|done|todo|verify] [text]")
        sys.exit(2)
