import telegram
from dotenv import load_dotenv
import os
import asyncio

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量获取 token 和 chat_id
TOKEN = os.getenv('TOKEN')
MYID = os.getenv('MYID')

bot = telegram.Bot(token=TOKEN)

async def main():
    await bot.send_message(chat_id=MYID, text="Hello from robot")

asyncio.run(main())