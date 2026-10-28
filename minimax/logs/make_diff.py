import difflib

old = open("logs/todo.py.before", encoding="utf-8").read()
new = open("biz/todo.py", encoding="utf-8").read()

diff = "".join(difflib.unified_diff(
    old.splitlines(True), new.splitlines(True),
    fromfile="biz/todo.py (修改前)", tofile="biz/todo.py (修改后)", n=3,
))
open("logs/patch.diff", "w", encoding="utf-8").write(diff)
print(diff)
