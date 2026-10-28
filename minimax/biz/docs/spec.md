# 待办工具规格说明

## SPEC-1 新增待办

`add_item(title, priority=2, due="")` 追加一条待办并返回该条记录。
`priority` 取值 1（高）、2（中）、3（低），默认 2。`id` 从 1 开始递增。

## SPEC-2 列出全部待办

`list_items()` 在不传参数时返回**全部**待办，按插入顺序排列。

对应测试：`tests/test_todo.py::TodoTest::test_list_all`

## SPEC-3 按优先级筛选（待实现）

`list_items(priority=n)` 必须**只返回** `priority == n` 的待办，顺序不变。

对应测试：`tests/test_todo.py::TodoTest::test_filter_by_priority`

验收标准：
- 传入 `priority=1` 时，返回结果中每一条的 `priority` 都等于 1
- 其余待办不得出现在结果中
- 不传 `priority` 时行为保持不变（仍是 SPEC-2）

## SPEC-4 标记完成

`mark_done(item_id)` 把对应待办置为 `done=True` 并返回该条记录；
`item_id` 不存在时抛出 `KeyError`。

## SPEC-5 兼容性约束

新增筛选能力**不得破坏** SPEC-1、SPEC-2、SPEC-4 的既有行为。
