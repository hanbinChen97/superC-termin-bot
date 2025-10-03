# -*- coding: utf-8 -*-

import logging
import time
import os

from superc.appointment_checker import run_check
from superc.config import LOCATIONS
from superc.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger("infostelle")

if __name__ == "__main__":
    logger.info(f"启动 Infostelle 预约检查程序，进程PID: {os.getpid()}")
    infostelle_config = LOCATIONS["infostelle"]

    while True:
        try:
            has_appointment, message = run_check(infostelle_config)
            if has_appointment:
                logger.info(f"成功！ {message}")
                break # 成功预约后退出循环
            elif message == "查询完成，当前没有可用预约时间":
                logger.info(message)
            else:
                # 记录其他错误信息，以备调试
                logger.warning(f"出现未预期的消息: {message}")
        except Exception as e:
            logger.error(f"检查过程中发生未预料的错误: {e}", exc_info=True)

        logger.info("等待1分钟后重新检查...")
        time.sleep(60)
