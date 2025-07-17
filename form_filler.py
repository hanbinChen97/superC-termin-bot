import json
import logging
from urllib.parse import urljoin

from llmCall import recognize_captcha
from utils import save_page_content
from config import USER_AGENT, PERSONAL_INFO_FILE, BASE_URL
from dom_utils import check_step_completion, check_rate_limit_error

def load_personal_info():
    """
    从 table 文件加载个人信息
    :return: 个人信息字典
    """
    try:
        with open(PERSONAL_INFO_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {item['fuellen_in_name']: item['wert_zum_fuellen'] for item in data}
    except Exception as e:
        logging.error(f"加载个人信息失败: {str(e)}")
        return None

def fill_form(session, soup, captcha_image_path, location_name):
    """
    填写表单并提交
    :param session: requests.Session 对象
    :param soup: BeautifulSoup 对象
    :param captcha_image_path: 验证码图片路径
    :param location_name: 地点名称，用于保存文件
    :return: (是否成功, 响应对象或错误信息)
    """
    logging.info("\n开始填写表单...")
    
    # 加载个人信息
    personal_info = load_personal_info()
    if not personal_info:
        return False, "无法加载个人信息"
    logging.info(f"已加载个人信息: {personal_info}")

    # 识别验证码
    logging.info(f"\n开始识别验证码: {captcha_image_path}")
    captcha_text = recognize_captcha(captcha_image_path)
    logging.info(f"验证码识别结果: {captcha_text}")
    if not captcha_text:
        return False, "验证码识别失败"

    # 准备表单数据
    form_data = personal_info.copy()
    # comment= ''
    form_data['comment'] = ''
    form_data['captcha_code'] = captcha_text
    form_data['agreementChecked'] = 'on'
    form_data['hunangskrukka'] = ''
    # submit=Reservieren
    form_data['submit'] = 'Reservieren'
    logging.info(f"\n准备提交的表单数据: {form_data}")

    # 获取表单提交URL
    form = soup.find('form')
    if not form:
        return False, "无法找到表单"

    # 获取所有隐藏字段
    hidden_fields = {}
    for hidden_input in form.find_all('input', type='hidden'):
        hidden_fields[hidden_input.get('name')] = hidden_input.get('value')
    form_data.update(hidden_fields)

    # 拼接 action url
    submit_url = urljoin('https://termine.staedteregion-aachen.de/auslaenderamt/', form.get('action'))
    logging.info(f"\n提交URL: {submit_url}")

    # 提交表单
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://termine.staedteregion-aachen.de/auslaenderamt/'
        }
        logging.info(f"\n准备提交请求，headers: {headers}")
        res = session.post(submit_url, data=form_data, headers=headers)
        save_page_content(res.text, '6_form_submitted', location_name)
        logging.info(f"\n表单提交响应状态码: {res.status_code}")
        
        # 使用DOM解析检查是否提交成功，而不是简单的字符串搜索
        if check_step_completion(res.text, 6):
            logging.info("预约成功！")
            return True, res
        elif check_rate_limit_error(res.text):
            error_message = "表单提交失败, zu vieler Terminanfragen"
            return False, error_message
        else:
            error_message = "表单提交失败"
            print(f"\n错误信息: {error_message}")
            print(f"响应内容: {res.text[:500]}...")
            return False, error_message
            
    except Exception as e:
        error_msg = f"提交表单时发生错误: {str(e)}"
        logging.info(f"\n错误: {error_msg}")
        return False, error_msg 