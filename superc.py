'''
python3 superc.py
nohup python3 superc.py > superc.log 2>&1 &
'''

import requests
import bs4
import logging
import os
from datetime import datetime
from urllib.parse import urljoin
from form_filler import fill_form
import time

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

def save_page_content(content, step_name):
    """
    保存页面内容到文件
    :param content: 页面内容
    :param step_name: 步骤名称
    """
    # 创建 pages/superc 目录（如果不存在）
    if not os.path.exists('pages/superc'):
        os.makedirs('pages/superc')
    
    # 生成文件名，包含时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'pages/superc/step_{step_name}_{timestamp}.html'
    
    # 保存文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f'页面内容已保存到: {filename}')

def get_initial_page(session):
    """
    获取初始页面
    :param session: requests.Session 对象
    :return: (是否成功, 响应对象)
    """
    url = 'https://termine.staedteregion-aachen.de/auslaenderamt/select2?md=1'
    res = session.get(url)

    # Schritt 2von 6: Aufenthaltsangelegenheiten
    # if "Schritt 2" in res.text:
    #     print("成功进入 Schritt 2 von 6")
    # else:
    #     print("未进入 Schritt 2 von 6")

    # save_page_content(res.text, '1_initial')
    return True, res

def select_rwth_student(session, res):
    """
    选择 RWTH Studenten 选项
    :param session: requests.Session 对象
    :param res: 初始页面的响应对象
    :return: (是否成功, URL或错误信息)
    """
    soup = bs4.BeautifulSoup(res.content, 'html.parser')
    header = soup.find("h3", string=lambda s: "Super C" in s if s else False)
    if not header:
        return False, "无法找到 Super C 选项"
    
    next_sibling = header.find_next_sibling()
    if not next_sibling:
        return False, "无法找到预约选项"
    
    li_elements = next_sibling.find_all("li")
    if not li_elements:
        return False, "无法找到预约选项列表"
    
    cnc_id = li_elements[0].get("id").split("-")[-1]
    url = f"https://termine.staedteregion-aachen.de/auslaenderamt/location?mdt=89&select_cnc=1&cnc-{cnc_id}=1"
    return True, url

def get_location_info(session, url):
    """
    获取位置信息
    :param session: requests.Session 对象
    :param url: 位置选择页面的URL
    :return: (是否成功, (位置ID, 响应对象))
    """
    res = session.get(url)

    # if "Schritt 3" in res.text:
    #     print("成功进入 Schritt 3 von 6")

    # save_page_content(res.text, '2_location')
    
    soup = bs4.BeautifulSoup(res.content, 'html.parser')
    loc = soup.find('input', {'name': 'loc'})
    if not loc:
        return False, "无法找到位置信息"
    
    return True, (loc.get('value'), res)

def submit_location(session, url, loc):
    """
    提交位置信息
    :param session: requests.Session 对象
    :param url: 位置选择页面的URL
    :param loc: 位置ID
    :return: (是否成功, 响应对象)
    """
    payload = {
        'loc': str(loc),
        'gps_lat': '55.77858',
        'gps_long': '65.07867',
        'select_location': 'Ausländeramt Aachen - Außenstelle RWTH auswählen'
    }
    res = session.post(url, data=payload)
    # save_page_content(res.text, '3_location_submitted')
    return True, res

def download_captcha(session, soup):
    """
    下载验证码图片
    :param session: requests.Session 对象
    :param soup: BeautifulSoup 对象
    :return: (是否成功, 图片路径或错误信息)
    """
    # 查找验证码图片链接
    captcha_div = soup.find("div", {"id": "captcha_image_audio_div"})
    if not captcha_div:
        return False, "无法找到验证码图片区域"
    
    # 获取音频源URL，从中提取ID
    audio_source = captcha_div.find("source", {"id": "captcha_image_source_wav"})
    if not audio_source:
        return False, "无法找到验证码音频源"
    
    audio_url = audio_source.get("src")
    if not audio_url:
        return False, "无法获取验证码音频URL"
    
    # 从音频URL中提取ID
    captcha_id = audio_url.split("id=")[-1]
    
    # 构造验证码图片URL
    img_url = f"https://termine.staedteregion-aachen.de/auslaenderamt/app/securimage/securimage_show.php?id={captcha_id}"
    
    # 下载图片
    try:
        img_response = session.get(img_url)
        if img_response.status_code != 200:
            return False, f"下载验证码图片失败，状态码：{img_response.status_code}"
        
        # 创建 captcha 目录（如果不存在）
        if not os.path.exists('pages/superc/captcha'):
            os.makedirs('pages/superc/captcha')
        
        # 生成文件名，包含时间戳
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'pages/superc/captcha/captcha_{timestamp}.png'
        
        # 保存图片
        with open(filename, 'wb') as f:
            f.write(img_response.content)
        
        logging.info(f'验证码图片已保存到: {filename}')
        return True, filename
    except Exception as e:
        return False, f"下载验证码图片时发生错误：{str(e)}"

def check_availability(session):
    """
    检查是否有可用预约时间，并自动选择第一个可用时间
    :param session: requests.Session 对象
    :return: (是否成功, 详细信息)
    """
    url = 'https://termine.staedteregion-aachen.de/auslaenderamt/suggest'
    res = session.get(url)
    # save_page_content(res.text, '4_availability')
    soup = bs4.BeautifulSoup(res.text, 'html.parser')

    details_container = soup.find("details", {"id": "details_suggest_times"})
    
    if "Kein freier Termin verfügbar" in res.text:
        return False, "查询完成，当前没有可用预约时间"

    if details_container is None:
        return False, "Error, we are not in processing."

    if details_container is not None:
        logging.info("发现可用预约时间")

        first_available_form = details_container.find("form", {"class": "suggestion_form"})
        
        if first_available_form is None:
            return False, "没找到表格" 

        if first_available_form:
            form_data = {}
            # 提取隐藏字段的逻辑不变
            for input_field in first_available_form.find_all("input", {"type": "hidden"}):
                form_data[input_field.get('name')] = input_field.get('value')
            
            # 提取时间的逻辑不变
            time_button = first_available_form.find("button", {"type": "submit"})
            
            if time_button is None:
                return False, "没找到button" 

            time_info = time_button.get('title') if time_button else "未知时间"
            
            # 提交请求的逻辑不变
            logging.info(f"找到可用时间: {time_info}, 正在提交...")
            logging.info(f"提交的表单数据: {form_data}")
            
            submit_url = 'https://termine.staedteregion-aachen.de/auslaenderamt/suggest'
            submit_res = session.post(submit_url, data=form_data)
            # Schritt 5 Terminvorschläge zeit
            if "Schritt 5" in submit_res.text:
                logging.info("成功进入 Schritt 5 von 6")
                logging.info("有时间：" + time_info)
            else:
                logging.info("没选中时间。")

            save_page_content(submit_res.text, '5_term_selected')

            submit_soup = bs4.BeautifulSoup(submit_res.text, 'html.parser')
            success, result = download_captcha(session, submit_soup)

            if success:
                return True, (submit_res.text, result)
            else:
                return True, (submit_res.text, result)
            h3_tags = div.find_all("h3")
            appointments = "\n".join([h.text for h in h3_tags])
            return True, f"发现可用预约时间：\n{appointments}"

        return True, "发现可用预约时间，但无法解析具体时间"
    

def check_appointment():
    """
    检查 SuperC 外管局是否有可用的预约时间
    返回: (是否有可用时间, 详细信息)
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    # 第一步：获取初始页面
    success, res = get_initial_page(session)
    if not success:
        return False, "获取初始页面失败"

    # 第二步：选择 RWTH Studenten
    success, url = select_rwth_student(session, res)
    if not success:
        return False, url

    # 第三步：获取位置信息
    success, result = get_location_info(session, url)
    if not success:
        return False, result
    loc, res = result

    # 第四步：提交位置信息
    success, res = submit_location(session, url, loc)
    if not success:
        return False, "提交位置信息失败"

    # 第五步：检查是否有可用时间
    success, result = check_availability(session)
    if not success:
        return False, result

    if isinstance(result, tuple) and len(result) == 2:
        html, captcha_path = result
        soup = bs4.BeautifulSoup(html, 'html.parser')
        success, submit_result = fill_form(session, soup, captcha_path)
        if success:
            return True, "预约成功！"
        else:
            return False, submit_result

    return success, result

if __name__ == "__main__":
    logging.info(f"当前进程PID: {os.getpid()}")

    while True:
        has_appointment, message = check_appointment()
     
        if has_appointment:
            break

        logging.info(f'{message}')
        logging.info("等待1分钟后重新检查...")
        time.sleep(60)  # 等待60秒
    