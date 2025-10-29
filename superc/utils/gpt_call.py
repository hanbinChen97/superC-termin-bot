"""
gpt_call.py

This module provides a wrapper for calling OpenAI GPT models (e.g., GPT-4o, GPT-4o-mini) using the openai Python SDK.
It loads API credentials from environment variables and provides a simple chat interface.

Functions:
	_get_client() -> openai.OpenAI: Returns a singleton OpenAI client instance.
	gpt_chat(messages: list[dict], model: str, max_tokens: int, temperature: float) -> str: Calls the GPT chat completion API.

Environment Variables:
	OPENAI_KEY: Your OpenAI API key (required)
	OPENAI_MODEL: The model name to use (default: 'gpt-4o')
"""

import os
import base64
import openai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Get OpenAI API key and model from environment
OPENAI_KEY = os.getenv("OPENAI_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # Default to GPT-4o

if not OPENAI_KEY:
	raise ValueError("OPENAI_KEY not set in environment variables.")

openai_client = None

def _get_client():
	"""
	Get or initialize the OpenAI client.
	Input: None
	Output: openai.OpenAI instance
	"""
	global openai_client
	if openai_client is None:
		openai_client = openai.OpenAI(api_key=OPENAI_KEY)
	return openai_client

def gpt_chat(messages, model=OPENAI_MODEL, max_tokens=256, temperature=0.7):
	"""
	Call OpenAI GPT chat completion API.
    
	Args:
		messages (list[dict]): List of message dicts, e.g. [{"role": "user", "content": "Hello"}]
		model (str): Model name (default: 'gpt-4o')
		max_tokens (int): Maximum tokens in the response
		temperature (float): Sampling temperature
	Returns:
		str: Response content from the model
	"""
	client = _get_client()
	response = client.chat.completions.create(
		model=model,
		messages=messages,
		max_tokens=max_tokens,
		temperature=temperature
	)
	content = response.choices[0].message.content
	return content.strip() if content else ""

def recognize_captcha_with_gpt(image_path, model=None):
	"""
	Recognize captcha from an image using OpenAI GPT-4o vision API.
	Input:
		image_path (str): Path to the captcha image file
		model (str): Model name (default: 'gpt-4o')
	Output:
		str: Recognized captcha text
	"""
	# Read and encode image as base64
	with open(image_path, "rb") as image_file:
		base64_image = base64.b64encode(image_file.read()).decode('utf-8')

	messages = [
		{
			"role": "system",
			"content": (
				"你是一个专业的验证码识别助手。你的任务是：\n"
				"1. 仔细分析图片中的验证码字符\n"
				"2. 只返回验证码字符，不要包含任何其他解释或文字\n"
				"3. 如果字符不清晰，请根据最可能的字符进行判断\n"
				"4. 保持原始大小写\n"
				"5. 不要添加任何空格或标点符号"
			)
		},
		{
			"role": "user",
			"content": [
				{"type": "text", "text": "请识别这张验证码图片中的字符："},
				{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
			]
		}
	]
	if model is None:
		model = OPENAI_MODEL
	client = _get_client()
	response = client.chat.completions.create(
		model=model,
		messages=messages,
		max_tokens=10,
		temperature=0.1
	)
	content = response.choices[0].message.content
	return content.strip() if content else ""

if __name__ == "__main__":
	# Test captcha recognition from image
	image_path = "data/test_pic.png"
	if os.path.exists(image_path):
		try:
			captcha = recognize_captcha_with_gpt(image_path)
			print(f"验证码识别结果: {captcha}")
		except Exception as e:
			print(f"识别出错: {e}")
	else:
			print(f"错误：找不到图片文件 {image_path}")