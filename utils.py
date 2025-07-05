
# -*- coding: utf-8 -*-

import os
import logging
from datetime import datetime
from urllib.parse import urljoin

import bs4

from config import USER_AGENT

def save_page_content(content, step_name, location_name):
    """
    保存页面内容到文件
    """
    dir_path = f'pages/{location_name}'
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{dir_path}/step_{step_name}_{timestamp}.html'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f'页面内容已保存到: {filename}')

def download_captcha(session, soup, location_name):
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
        
        logging.info(f'验证码图片已保存到: {filename}')
        return True, filename
    except Exception as e:
        return False, f"下载验证码图片时发生错误：{str(e)}"
