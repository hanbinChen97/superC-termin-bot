"""


uv run python -m db.utils

"""

import os
import logging
from datetime import datetime
from typing import Union, Tuple, Any
from urllib.parse import urljoin

import bs4
import httpx

# 使用相对导入
from ..config import USER_AGENT


logger = logging.getLogger(__name__)

def validate_page_step(html_content: Union[str, httpx.Response, Any], expected_step: str) -> bool:
    """
    通过DOM解析验证页面步骤，而不是字符串比较
    
    Args:
        html_content: HTML内容（字符串或响应对象）
        expected_step: 期望的步骤编号（如 "2", "3"）
    
    Returns:
        bool: 是否找到预期的步骤标题
    """
    if hasattr(html_content, 'content'):
        content = html_content.content
    elif hasattr(html_content, 'text'):
        content = html_content.text
    else:
        content = html_content
    
    soup = bs4.BeautifulSoup(content, 'html.parser')
    
    # 查找包含步骤信息的h1标签
    h1_element = soup.find('h1')
    
    if h1_element:
        h1_text = h1_element.get_text()
        # 检查是否包含预期的步骤编号
        return f"Schritt {expected_step}" in h1_text
    
    return False

def save_page_content(content: str, step_name: str, location_name: str) -> None:
    """
    保存页面内容到文件
    """
    dir_path = f'data/pages/{location_name}'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{dir_path}/step_{step_name}_{timestamp}.html'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f'页面内容已保存到: {filename}')

def download_captcha(session: httpx.Client, soup: bs4.BeautifulSoup, location_name: str) -> Tuple[bool, str]:
    """
    下载验证码图片
    """
    captcha_div = soup.find("div", {"id": "captcha_image_audio_div"})
    if not captcha_div:
        return False, "无法找到验证码图片区域"
    
    audio_source = captcha_div.find("source", {"id": "captcha_image_source_wav"})
    if not audio_source:
        return False, "无法找到验证码音频源"
    
    audio_url = audio_source.get("src")
    if not audio_url:
        return False, "无法获取验证码音频URL"
    
    captcha_id = audio_url.split("id=")[-1]
    img_url = f"https://termine.staedteregion-aachen.de/auslaenderamt/app/securimage/securimage_show.php?id={captcha_id}"
    
    try:
        img_response = session.get(img_url)
        if img_response.status_code != 200:
            return False, f"下载验证码图片失败，状态码：{img_response.status_code}"
        
        dir_path = f'pages/{location_name}/captcha'
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{dir_path}/captcha_{timestamp}.png'
        
        with open(filename, 'wb') as f:
            f.write(img_response.content)
        
        logger.info(f'验证码图片已保存到: {filename}')
        return True, filename
    except Exception as e:
        return False, f"下载验证码图片时发生错误：{str(e)}"
