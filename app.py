from flask import Flask
from flask_apscheduler import APScheduler
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
from superc import check_appointment

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

@app.route('/')
def home():
    return 'Aachen Termin Bot is running'

@app.route('/status')
def status():
    return 'OK'

@scheduler.task('interval', id='check_appointments', minutes=3, misfire_grace_time=900)
def check_appointments():
    """
    每三分钟检查一次预约状态
    """
    try:
        has_appointment, message = check_appointment()
        if has_appointment:
            logging.info(f"发现可用预约时间: {message}")
        else:
            logging.info(f"当前没有可用预约时间: {message}")
    except Exception as e:
        logging.error(f"检查预约时发生错误: {str(e)}")

if __name__ == '__main__':
    logging.info("启动 Aachen Termin Bot 服务器...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)