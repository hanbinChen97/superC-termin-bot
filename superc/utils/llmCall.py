import os
from openai import AzureOpenAI
import base64
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 从环境变量获取配置
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
subscription_key = os.getenv("AZURE_OPENAI_KEY")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# 打印环境变量（不打印敏感信息）
# print("环境变量检查：")
# print(f"AZURE_OPENAI_ENDPOINT: {'已设置' if endpoint else '未设置'}")
# print(f"AZURE_OPENAI_DEPLOYMENT_NAME: {'已设置' if deployment else '未设置'}")
# print(f"AZURE_OPENAI_KEY: {'已设置' if subscription_key else '未设置'}")
# print(f"AZURE_OPENAI_API_VERSION: {api_version}")

# Initialize client only when needed to avoid import-time errors
client = None

def _get_client():
    """Get or initialize the Azure OpenAI client."""
    global client
    if client is None:
        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key,
        )
    return client

def encode_image(image_path):
    """
    将图片转换为base64编码
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def recognize_captcha(image_path):
    """
    识别验证码图片
    :param image_path: 验证码图片路径
    :return: 识别结果
    """
    # 将图片转换为base64
    base64_image = encode_image(image_path)
    
    response = _get_client().chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": """你是一个专业的验证码识别助手。你的任务是：
1. 仔细分析图片中的验证码字符
2. 只返回验证码字符，不要包含任何其他解释或文字
3. 如果字符不清晰，请根据最可能的字符进行判断
4. 保持原始大小写
5. 不要添加任何空格或标点符号"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请识别这张验证码图片中的字符："
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=10,  # 验证码通常很短，限制token数量
        temperature=0.1,  # 降低随机性，使结果更稳定
        model=deployment
    )
    
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    # 测试验证码识别
    image_path = "data/test_pic.png"

    if os.path.exists(image_path):
        result = recognize_captcha(image_path)
        print(f"验证码识别结果: {result}")
    else:
        print(f"错误：找不到图片文件 {image_path}")