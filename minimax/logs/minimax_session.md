# MiniMax 开发记录

## 会话记录 2026-10-28 11:58:26

- 模型：`MiniMax-Text-01`
- 任务：为 list 命令增加按优先级筛选
- API：HTTP 200，base_resp={"status_code": 0, "status_msg": ""}

### 使用的上下文来源

- [specs] `docs/spec.md#L14` section:SPEC-3 按优先级筛选（待实现）
- [specs] `docs/spec.md#L8` section:SPEC-2 列出全部待办
- [specs] `docs/spec.md#L30` section:SPEC-5 兼容性约束
- [code] `todo.py#L63` function:main
- [code] `todo.py#L44` function:list_items
- [tests] `tests/test_todo.py#L33` function:TodoTest.test_list_all
- [tests] `tests/test_todo.py#L50` function:TodoTest.test_filter_by_priority
- [tests] `tests/test_todo.py#L54` function:TodoTest.test_filter_returns_only_matching

### Prompt

```text
你是代码修改助手。请严格按下面的规格修改代码。

【任务】
为 list 命令增加按优先级筛选

【必须遵守的规格】
### SPEC-3 按优先级筛选（待实现） (docs/spec.md)
## SPEC-3 按优先级筛选（待实现）

`list_items(priority=n)` 必须**只返回** `priority == n` 的待办，顺序不变。

对应测试：`tests/test_todo.py::TodoTest::test_filter_by_priority`

验收标准：
- 传入 `priority=1` 时，返回结果中每一条的 `priority` 都等于 1
- 其余待办不得出现在结果中
- 不传 `priority` 时行为保持不变（仍是 SPEC-2）

### SPEC-2 列出全部待办 (docs/spec.md)
## SPEC-2 列出全部待办

`list_items()` 在不传参数时返回**全部**待办，按插入顺序排列。

对应测试：`tests/test_todo.py::TodoTest::test_list_all`

### SPEC-5 兼容性约束 (docs/spec.md)
## SPEC-5 兼容性约束

新增筛选能力**不得破坏** SPEC-1、SPEC-2、SPEC-4 的既有行为。

【需要修改的函数（当前实现）】
### main (todo.py)
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

### list_items (todo.py)
def list_items(priority=None):
    """列出待办。

    TODO(SPEC-3)：规格要求支持按 priority 筛选，此参数目前尚未生效。
    """
    return load_items()

【修改后必须通过的测试】
### test_list_all (tests/test_todo.py)
    def test_list_all(self):
        titles = [i["title"] for i in todo.list_items()]
        self.assertEqual(titles, ["买牛奶", "写周报", "遛狗"])

### test_filter_by_priority (tests/test_todo.py)
    def test_filter_by_priority(self):
        got = [i["title"] for i in todo.list_items(priority=1)]
        self.assertEqual(got, ["买牛奶", "遛狗"])

### test_filter_returns_only_matching (tests/test_todo.py)
    def test_filter_returns_only_matching(self):
        got = todo.list_items(priority=3)
        self.assertEqual([i["title"] for i in got], ["写周报"])
        self.assertTrue(all(i["priority"] == 3 for i in got))

【输出要求】
1. 只输出修改后的 `list_items` 函数完整源码（从 def 开始到函数结束），放在一个 ```python 代码块里。
2. 不要输出解释、不要输出测试代码、不要输出其他函数。
3. 保持函数名、参数名和默认值不变，确保既有行为（不传 priority 时返回全部）不受影响。

```

### 模型原始返回

```text
```python
def list_items(priority=None):
    """列出待办。

    TODO(SPEC-3)：规格要求支持按 priority 筛选，此参数目前尚未生效。
    """
    items = load_items()
    if priority is not None:
        items = [item for item in items if item["priority"] == priority]
    return items
```
```

### 提取出的代码

```python
def list_items(priority=None):
    """列出待办。

    TODO(SPEC-3)：规格要求支持按 priority 筛选，此参数目前尚未生效。
    """
    items = load_items()
    if priority is not None:
        items = [item for item in items if item["priority"] == priority]
    return items
```

### 是否写回源码

已写回 biz/todo.py

---

## 会话记录 2026-10-28 11:58:45

- 模型：`MiniMax-Text-01`
- 任务：更新 list_items 的 docstring：说明已支持按 priority 筛选，去掉 TODO 说明
- API：HTTP 200，base_resp={"status_code": 0, "status_msg": ""}

### 使用的上下文来源

- [specs] `docs/spec.md#L14` section:SPEC-3 按优先级筛选（待实现）
- [specs] `docs/spec.md#L8` section:SPEC-2 列出全部待办
- [specs] `docs/spec.md#L3` section:SPEC-1 新增待办
- [specs] `docs/spec.md#L1` section:preamble
- [specs] `docs/spec.md#L30` section:SPEC-5 兼容性约束
- [code] `todo.py#L63` function:main
- [code] `todo.py#L44` function:list_items
- [code] `todo.py#L29` function:add_item
- [code] `todo.py#L15` function:load_items
- [code] `todo.py#L23` function:save_items
- [code] `todo.py#L52` function:mark_done
- [tests] `tests/test_todo.py#L20` function:TodoTest.setUp
- [tests] `tests/test_todo.py#L50` function:TodoTest.test_filter_by_priority
- [tests] `tests/test_todo.py#L54` function:TodoTest.test_filter_returns_only_matching
- [tests] `tests/test_todo.py#L38` function:TodoTest.test_add_item
- [tests] `tests/test_todo.py#L33` function:TodoTest.test_list_all
- [tests] `tests/test_todo.py#L44` function:TodoTest.test_mark_done

### Prompt

```text
你是代码修改助手。请严格按下面的规格修改代码。

【任务】
更新 list_items 的 docstring：说明已支持按 priority 筛选，去掉 TODO 说明

【必须遵守的规格】
### SPEC-3 按优先级筛选（待实现） (docs/spec.md)
## SPEC-3 按优先级筛选（待实现）

`list_items(priority=n)` 必须**只返回** `priority == n` 的待办，顺序不变。

对应测试：`tests/test_todo.py::TodoTest::test_filter_by_priority`

验收标准：
- 传入 `priority=1` 时，返回结果中每一条的 `priority` 都等于 1
- 其余待办不得出现在结果中
- 不传 `priority` 时行为保持不变（仍是 SPEC-2）

### SPEC-2 列出全部待办 (docs/spec.md)
## SPEC-2 列出全部待办

`list_items()` 在不传参数时返回**全部**待办，按插入顺序排列。

对应测试：`tests/test_todo.py::TodoTest::test_list_all`

### SPEC-1 新增待办 (docs/spec.md)
## SPEC-1 新增待办

`add_item(title, priority=2, due="")` 追加一条待办并返回该条记录。
`priority` 取值 1（高）、2（中）、3（低），默认 2。`id` 从 1 开始递增。

### preamble (docs/spec.md)
# 待办工具规格说明

### SPEC-5 兼容性约束 (docs/spec.md)
## SPEC-5 兼容性约束

新增筛选能力**不得破坏** SPEC-1、SPEC-2、SPEC-4 的既有行为。

【需要修改的函数（当前实现）】
### main (todo.py)
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

### list_items (todo.py)
def list_items(priority=None):
    """列出待办。

    TODO(SPEC-3)：规格要求支持按 priority 筛选，此参数目前尚未生效。
    """
    return load_items()

### add_item (todo.py)
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

### load_items (todo.py)
def load_items():
    """读取全部待办。"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

### save_items (todo.py)
def save_items(items):
    """写回待办列表。"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

### mark_done (todo.py)
def mark_done(item_id):
    """把指定 id 的待办标记为完成。"""
    items = load_items()
    for it in items:
        if it["id"] == item_id:
            it["done"] = True
            save_items(items)
            return it
    raise KeyError("no such id: %s" % item_id)

【修改后必须通过的测试】
### setUp (tests/test_todo.py)
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = todo.DATA_FILE
        todo.DATA_FILE = os.path.join(self.tmp.name, "todos.json")
        todo.add_item("买牛奶", priority=1)
        todo.add_item("写周报", priority=3)
        todo.add_item("遛狗", priority=1)

### test_filter_by_priority (tests/test_todo.py)
    def test_filter_by_priority(self):
        got = [i["title"] for i in todo.list_items(priority=1)]
        self.assertEqual(got, ["买牛奶", "遛狗"])

### test_filter_returns_only_matching (tests/test_todo.py)
    def test_filter_returns_only_matching(self):
        got = todo.list_items(priority=3)
        self.assertEqual([i["title"] for i in got], ["写周报"])
        self.assertTrue(all(i["priority"] == 3 for i in got))

### test_add_item (tests/test_todo.py)
    def test_add_item(self):
        item = todo.add_item("洗车", priority=2)
        self.assertEqual(item["id"], 4)
        self.assertEqual(len(todo.load_items()), 4)

### test_list_all (tests/test_todo.py)
    def test_list_all(self):
        titles = [i["title"] for i in todo.list_items()]
        self.assertEqual(titles, ["买牛奶", "写周报", "遛狗"])

### test_mark_done (tests/test_todo.py)
    def test_mark_done(self):
        item = todo.mark_done(2)
        self.assertTrue(item["done"])
        self.assertFalse(todo.load_items()[0]["done"])

【输出要求】
1. 只输出修改后的 `list_items` 函数完整源码（从 def 开始到函数结束），放在一个 ```python 代码块里。
2. 不要输出解释、不要输出测试代码、不要输出其他函数。
3. 保持函数名、参数名和默认值不变，确保既有行为（不传 priority 时返回全部）不受影响。

```

### 模型原始返回

```text
```python
def list_items(priority=None):
    """列出待办。

    支持按 priority 筛选，返回 priority 等于指定值的待办。
    """
    items = load_items()
    if priority is not None:
        return [item for item in items if item["priority"] == priority]
    return items
```
```

### 提取出的代码

```python
def list_items(priority=None):
    """列出待办。

    支持按 priority 筛选，返回 priority 等于指定值的待办。
    """
    items = load_items()
    if priority is not None:
        return [item for item in items if item["priority"] == priority]
    return items
```

### 是否写回源码

已写回 biz/todo.py

---

