from flask import Flask
from flask_apscheduler import APScheduler
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from superc import check_appointment
import telegram
from dotenv import load_dotenv
import asyncio

# 加载环境变量
load_dotenv()

# 获取 Telegram 配置
TOKEN = os.getenv('TOKEN')
MYID = os.getenv('MYID')
bot = telegram.Bot(token=TOKEN)

# 配置日志
log_directory = 'logs'
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_filename = f"{log_directory}/aachen_termin_bot_{datetime.now().strftime('%Y-%m-%d')}.log"
handler = RotatingFileHandler(log_filename, maxBytes=10485760, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

# 添加控制台输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

# 创建Flask应用
app = Flask(__name__)

# 配置调度器
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

def is_peak_time():
    """
    判断当前是否在高峰时段（早上6点到8点）
    """
    current_hour = datetime.now().hour
    return 6 <= current_hour < 8

@app.route('/')
def home():
    return 'Aachen Termin Bot is running'

@app.route('/status')
def status():
    return 'OK'

@scheduler.task('interval', id='check_appointments', minutes=1, misfire_grace_time=900)
def check_appointments():
    """
    检查预约状态
    高峰时段（6:00-8:00）：每分钟检查一次
    其他时段：每5分钟检查一次
    """
    if not is_peak_time():
        return
        
    try:
        has_appointment, message = check_appointment()
        if has_appointment:
            logging.info(f"发现可用预约时间: {message}")
            # 发送 Telegram 通知
            asyncio.run(bot.send_message(chat_id=MYID, text=f"发现可用预约时间！\n{message}\n请访问 https://termine.staedteregion-aachen.de/auslaenderamt/select2?md=1 进行操作"))
        else:
            logging.info(f"当前没有可用预约时间: {message}")
    except Exception as e:
        logging.error(f"检查预约时发生错误: {str(e)}")
        # 发送错误通知
        asyncio.run(bot.send_message(chat_id=MYID, text=f"检查预约时发生错误: {str(e)}"))

@scheduler.task('interval', id='check_appointments_normal', minutes=5, misfire_grace_time=900)
def check_appointments_normal():
    """
    非高峰时段的预约检查
    """
    if is_peak_time():
        return
        
    try:
        has_appointment, message = check_appointment()
        if has_appointment:
            logging.info(f"发现可用预约时间: {message}")
            # 发送 Telegram 通知
            asyncio.run(bot.send_message(chat_id=MYID, text=f"发现可用预约时间！\n{message}\n请访问 https://termine.staedteregion-aachen.de/auslaenderamt/select2?md=1 进行操作"))
        else:
            logging.info(f"当前没有可用预约时间: {message}")
    except Exception as e:
        logging.error(f"检查预约时发生错误: {str(e)}")
        # 发送错误通知
        asyncio.run(bot.send_message(chat_id=MYID, text=f"检查预约时发生错误: {str(e)}"))

if __name__ == '__main__':
    logging.info("启动 Aachen Termin Bot 服务器...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8318)), debug=False)