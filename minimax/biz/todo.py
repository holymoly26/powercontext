"""极简待办 CLI —— SDD 上下文演示用的业务工程。

规格见 docs/spec.md。
"""
import json
import os
import sys

DATA_FILE = os.environ.get(
    "TODO_DATA",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json"),
)


def load_items():
    """读取全部待办。"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_items(items):
    """写回待办列表。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def add_item(title, priority=2, due=""):
    """新增一条待办，priority 取值 1(高) / 2(中) / 3(低)。"""
    items = load_items()
    item = {
        "id": len(items) + 1,
        "title": title,
        "priority": int(priority),
        "due": due,
        "done": False,
    }
    items.append(item)
    save_items(items)
    return item


def list_items(priority=None):
    """列出待办。

    支持按 priority 筛选，返回 priority 等于指定值的待办。
    """
    items = load_items()
    if priority is not None:
        return [item for item in items if item["priority"] == priority]
    return items


def mark_done(item_id):
    """把指定 id 的待办标记为完成。"""
    items = load_items()
    for it in items:
        if it["id"] == item_id:
            it["done"] = True
            save_items(items)
            return it
    raise KeyError("no such id: %s" % item_id)


def main(argv):
    if not argv:
        print("usage: todo.py <add|list|done> ...")
        return 2

    cmd, rest = argv[0], argv[1:]

    if cmd == "add":
        title = rest[0]
        priority, due = 2, ""
        i = 1
        while i < len(rest):
            if rest[i] == "--priority":
                priority = int(rest[i + 1])
                i += 2
            elif rest[i] == "--due":
                due = rest[i + 1]
                i += 2
            else:
                i += 1
        print(json.dumps(add_item(title, priority, due), ensure_ascii=False))
        return 0

    if cmd == "list":
        priority = None
        if "--priority" in rest:
            priority = int(rest[rest.index("--priority") + 1])
        for it in list_items(priority):
            print("%d\t%s\t优先级%s\t%s" % (it["id"], it["title"], it["priority"], "已完成" if it["done"] else "待办"))
        return 0

    if cmd == "done":
        print(json.dumps(mark_done(int(rest[0])), ensure_ascii=False))
        return 0

    print("unknown command: %s" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
