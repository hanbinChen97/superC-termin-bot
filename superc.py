# source .venv/bin/activate && python3 superc.py 2>&1
# nohup python3 superc.py 2>&1 | tee superc.log

import logging
import time
import os
from datetime import datetime

from superc.appointment_checker import run_check
from superc.config import LOCATIONS, LOG_FORMAT

logging.basicConfig(format=LOG_FORMAT, level=logging.INFO)

if __name__ == "__main__":
    logging.info(f"启动 SuperC 预约检查程序，进程PID: {os.getpid()}")
    superc_config = LOCATIONS["superc"]

    while True:
        # 检查当前时间，如果是22点或之后则退出
        current_hour = datetime.now().hour
        if current_hour >= 22:
            logging.info("已到22点，程序自动退出")
            break
            
        try:
            has_appointment, message = run_check(superc_config)
            if has_appointment:
                logging.info(f"成功！ {message}")
                break  # 成功预约后退出循环
            elif message == "表单提交失败, zu vieler Terminanfragen":
                logging.info(message)
                break  # 成功预约后退出循环
            elif "当前没有可用预约时间" in message:
                logging.info(message)
            else:
                # 记录其他错误信息，以备调试
                logging.warning(f"出现未预期的消息: {message}")
        except Exception as e:
            logging.error(f"检查过程中发生未预料的错误: {e}", exc_info=True)

        # logging.info("等待1分钟后重新检查...")
        time.sleep(60)