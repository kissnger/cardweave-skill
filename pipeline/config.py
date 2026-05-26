"""
Cardweave 管道配置统一读取器
各 pipeline 脚本 import 此模块获取默认输出路径。

用法:
    from config import get_output_dir, resolve_output_dir
    out = get_output_dir(cli_arg="-o 传入的路径")   # 优先 CLI，其次 rules 文件
"""

import os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # pipeline/
ROOT = HERE.parent                               # repo root (~/.hermes/skills/creative/cardweave-skill/)
CONFIG_FILE = ROOT / "config" / "curation.yaml"


def _load_yaml():
    """简单 YAML 解析器，只读 output.base_dir"""
    if not CONFIG_FILE.exists():
        return {}
    import re
    text = CONFIG_FILE.read_text()
    m = re.search(r'^output:\s*\n\s+base_dir:\s*["\']?([^\s"\'#]+)', text, re.MULTILINE)
    return {"base_dir": m.group(1)} if m else {}


def get_output_dir(cli_arg=None):
    """
    返回输出基目录的 Path。
    - cli_arg: 从命令行 -o 传入的值（相对路径/绝对路径/None）
    - 如果 cli_arg 为空或 None，则从 curation.yaml output.base_dir 读取
    - 相对路径相对于 pipeline/ 目录
    - 绝对路径直接使用
    """
    raw = cli_arg if cli_arg else _load_yaml().get("base_dir")
    if not raw:
        print("[config.py 错误] 未指定输出目录。请用 -o 或在 config/curation.yaml 设置 output.base_dir", file=sys.stderr)
        sys.exit(1)

    p = Path(raw)
    if p.is_absolute():
        return p.resolve()
    # 相对路径：相对于 repo 根目录（即 ROOT）
    return (ROOT / p).resolve()


if __name__ == "__main__":
    # 测试
    print(f"配置文件: {CONFIG_FILE}")
    print(f"默认输出: {get_output_dir()}")
    print(f"CLI 覆盖: {get_output_dir('../output')}")
