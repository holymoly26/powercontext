# 规有所依 —— SDD 上下文管理系统（MiniMax × OceanBase）

为 AI 开发助手提供"当前任务该看哪些规格、改哪些代码、跑哪些测试"的上下文模块，
并用 MiniMax 完成一次真实代码修改，用 seekdb 存储工程资料，用 PowerContext 保存任务状态。

## 材料索引

| 材料 | 位置 |
|---|---|
| 完整源码 | `minimax/`（`biz/`、`ctx/`、`schema.sql`） |
| 运行说明 | 本文件 |
| 验证样例 | [`docs/验证样例.md`](docs/验证样例.md) |
| 一页技术说明 | [`docs/技术说明.md`](docs/技术说明.md) |
| 代码与测试 | `logs/todo.py.before`、`logs/patch.diff`、`logs/test_before.log`、`logs/test_after.log` |
| 技术使用记录 | `logs/minimax_session.md`、`logs/powercontext.log`、`logs/sql_query.log` |

---

## 目录结构

```
minimax-ctx/
├─ schema.sql              seekdb 建表语句
├─ requirements.txt
├─ biz/                    业务工程（被改造的对象）
│  ├─ todo.py              待办 CLI
│  ├─ docs/spec.md         规格（SPEC-1 ~ SPEC-5）
│  └─ tests/test_todo.py   3 个回归测试 + 2 个目标测试
├─ ctx/                    上下文模块
│  ├─ db.py                seekdb 连接
│  ├─ importer.py          切块入库（md 按标题、py 按函数）
│  ├─ query.py             按任务检索 → 输出 JSON 上下文
│  ├─ state.py             任务状态读写（file 实现，可换 PowerContext）
│  └─ minimax_client.py    MiniMax 调用（待补）
└─ logs/                   证据日志
```

---

## 快速开始

```bash
pip install -r requirements.txt
```

**1. 建表 + 导入工程资料**（一条命令，不需要 mysql 客户端）

```bash
python ctx/importer.py --root biz --reset --init-db
```

`--init-db` 会直接执行 `schema.sql` 建库建表（也可用 `mysql -h127.0.0.1 -P2881 -uroot < schema.sql`）。
所有 SQL 会记录到 `logs/sql_query.log`。

**3. 查询上下文**

```bash
python ctx/query.py --task "为 list 命令增加按优先级筛选"
```

输出示例：

```json
{
  "task": "为 list 命令增加按优先级筛选",
  "specs": [{"source": "docs/spec.md#L12", "title": "SPEC-3 按优先级筛选（待实现）", ...}],
  "code":  [{"source": "todo.py#L46", "symbol": "function:list_items", ...}],
  "tests": [{"source": "tests/test_todo.py#L50", "symbol": "function:test_filter_by_priority", ...}],
  "state": {"done": [], "todo": [], "verifications": []}
}
```

**4. 跑测试（修改前，目标测试应当失败）**

```bash
python -m unittest discover -s biz/tests -v
```

期望：`test_filter_by_priority`、`test_filter_returns_only_matching` **FAIL**，
其余 3 个回归测试 **OK**。

**5. 用 MiniMax 完成修改**（见 `ctx/minimax_client.py`）

**6. 再跑测试（修改后，全部通过）**

**7. 状态复用**

```bash
python ctx/state.py todo "实现 list_items 的 priority 筛选"
python ctx/state.py show
python ctx/query.py --task "继续完成优先级筛选"
```

`state` 字段会出现在上下文输出里，且进程重启后依然存在。

---

## 六个验收项对照

| 验收项 | 本项目对应 |
|---|---|
| 能够运行 | 上面 1~7 步，仅依赖 seekdb 容器 + pymysql |
| MiniMax 实际参与 | `logs/minimax_session.md` 记录任务/上下文/返回补丁，与 `git diff` 对应 |
| 上下文正确 | `query.py` 输出带真实 `path#L行号`，来自 seekdb 实时查询；改 `spec.md` 后重新 import，score 与内容同步变化 |
| 数据库实际参与 | `sdd.context_docs` 表；`logs/sql_query.log` 记录实际执行的查询 |
| 状态能够复用 | `ctx/state.py`（file）→ 后续替换为 PowerContext 实现 |
| 代码修改有效 | 步骤 4 FAIL → 步骤 6 PASS，日志记录命令与退出码 |

---

## 证据清单（logs/）

| 文件 | 内容 | 对应验收项 |
|---|---|---|
| `todo.py.before` | 修改前的源码快照 | 代码与测试 |
| `patch.diff` | 修改前后统一差异 | 代码与测试 |
| `test_before.log` | 修改前测试：3 OK / **2 FAIL** | 代码修改有效（改前） |
| `test_after.log` | 修改后测试：5 OK / exit=0 | 代码修改有效（改后） |
| `minimax_session.md` | 2 次 MiniMax 会话：任务、上下文来源、prompt、原始返回、提取代码 | MiniMax 实际参与 |

## PowerContext 接入

版本：`powercontext 1.4.1`（PyPI），接入方式：**HTTP API**。

```bash
python -m pip install "powercontext[cli,server]" jsonschema
powercontext server run          # 默认监听 http://127.0.0.1:8000
```

模块 `ctx/pc_state.py` 调用三个接口：

| 接口 | 用途 |
|---|---|
| `POST /v1/scopes` | 创建/复用 Scope（id 缓存在 `.pc_scope`） |
| `POST /v1/memory/remember` | 写入任务状态（done / todo / verifications 三类，带前缀区分） |
| `POST /v1/memory/search` | 重启后按前缀检索，还原三类状态 |

`ctx/state.py` 自动选择后端：PowerContext 可用就用它，否则回退本地 JSON
（`STATE_BACKEND=file` 可强制走文件）。所有调用记录写入 `logs/powercontext.log`。

## 进度

- [x] `ctx/minimax_client.py`：MiniMax 调用，已实测 HTTP 200
- [x] 改前 2 FAIL → MiniMax 改代码 → 改后 5 OK
- [x] 规格变更传播验证（version 3→4，新内容可检索）
- [x] 任务状态跨进程复用（写入 → 新进程读取 → 出现在上下文 state 字段）
- [x] **PowerContext 接入**：服务重启后状态仍可读回（`logs/powercontext.log`）
- [ ] 复制到参赛仓库 `minimax/` 目录，基于 `powercontext` 的 `2026-competition-ecosystem` 分支
- [ ] 补写验证样例文档、一页技术说明


