"""读取 .env 配置。支持环境变量优先，其次读同目录上级的 .env 文件。"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, ".env")


def load_env():
    """把 .env 里的键值读进 os.environ（已存在的不覆盖）。"""
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if v and k not in os.environ:
                os.environ[k] = v


def mask(secret):
    """只显示前后各 4 位，用于安全自检。"""
    if not secret:
        return "(空)"
    if len(secret) <= 10:
        return secret[:2] + "***" + secret[-2:]
    return secret[:4] + "***" + secret[-4:] + " (长度 %d)" % len(secret)


load_env()
