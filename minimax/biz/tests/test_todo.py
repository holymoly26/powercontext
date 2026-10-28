"""待办工具的测试。

- test_list_all / test_add_item / test_mark_done 是**回归测试**，修改前后都必须通过。
- test_filter_by_priority 是**目标测试**，修改前应当失败（SPEC-3 尚未实现）。

运行：python -m unittest discover -s biz/tests -v
"""
import os
import sys
import tempfile
import unittest

BIZ_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BIZ_DIR)

import todo  # noqa: E402


class TodoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._orig = todo.DATA_FILE
        todo.DATA_FILE = os.path.join(self.tmp.name, "todos.json")
        todo.add_item("买牛奶", priority=1)
        todo.add_item("写周报", priority=3)
        todo.add_item("遛狗", priority=1)

    def tearDown(self):
        todo.DATA_FILE = self._orig
        self.tmp.cleanup()

    # ---------- SPEC-2 回归 ----------
    def test_list_all(self):
        titles = [i["title"] for i in todo.list_items()]
        self.assertEqual(titles, ["买牛奶", "写周报", "遛狗"])

    # ---------- SPEC-1 回归 ----------
    def test_add_item(self):
        item = todo.add_item("洗车", priority=2)
        self.assertEqual(item["id"], 4)
        self.assertEqual(len(todo.load_items()), 4)

    # ---------- SPEC-4 回归 ----------
    def test_mark_done(self):
        item = todo.mark_done(2)
        self.assertTrue(item["done"])
        self.assertFalse(todo.load_items()[0]["done"])

    # ---------- SPEC-3 目标测试（修改前失败） ----------
    def test_filter_by_priority(self):
        got = [i["title"] for i in todo.list_items(priority=1)]
        self.assertEqual(got, ["买牛奶", "遛狗"])

    def test_filter_returns_only_matching(self):
        got = todo.list_items(priority=3)
        self.assertEqual([i["title"] for i in got], ["写周报"])
        self.assertTrue(all(i["priority"] == 3 for i in got))


if __name__ == "__main__":
    unittest.main()
