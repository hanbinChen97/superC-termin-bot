"""
SuperC 预约机器人 - 入口

Usage:
    python superc.py              # 数据库模式（连接 Supabase）
    python superc.py --local      # 本地模式（读取 data/local_user.yaml）

    uv run superc.py --local
    nohup uv run superc.py >> superc.log 2>&1 &
"""

import argparse
import logging
import os

from superc.utils.logging_utils import setup_logging


def parse_args():
    parser = argparse.ArgumentParser(description="SuperC 预约检查程序")
    parser.add_argument(
        "--local", "-l",
        action="store_true",
        help="本地模式：从 data/local_user.yaml 读取用户信息，不连接数据库",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 本地模式下禁用 Supabase 日志
    if args.local:
        from superc import config
        config.ENABLE_SUPABASE_LOGS = False

    setup_logging()
    logger = logging.getLogger("main")

    mode_label = "[本地模式]" if args.local else ""
    logger.info(f"启动 SupaC 预约检查程序{mode_label}，进程PID: {os.getpid()}")

    from superc.runner import run
    run(local_mode=args.local)


if __name__ == "__main__":
    main()
