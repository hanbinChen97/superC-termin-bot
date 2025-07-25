import json
import logging
from urllib.parse import urljoin

from .llmCall import recognize_captcha
from .utils import save_page_content
from .config import USER_AGENT, BASE_URL
from . import config

def load_personal_info():
    """
    从 currentProfile 加载个人信息
    :return: 个人信息字典
    """
    if not config.currentProfile:
        logging.error("currentProfile 未设置")
        return None
    
    try:
        profile_data = config.currentProfile["data"]
        profile_type = config.currentProfile["type"]
        
        if profile_type == "user_defined":
            # 用户定义文件格式: [{fuellen_in_name: "", wert_zum_fuellen: ""}, ...]
            return {item['fuellen_in_name']: item['wert_zum_fuellen'] for item in profile_data}
        elif profile_type == "profile_dataclass":
            # Profile数据类格式: 直接使用 to_form_data() 方法
            return profile_data.to_form_data()
        elif profile_type == "database":
            # 数据库格式: AppointmentProfile 对象
            return {
                "vorname": profile_data.vorname,
                "nachname": profile_data.nachname,
                "email": profile_data.email,
                "phone": profile_data.phone,
                "geburtsdatum_day": str(profile_data.geburtsdatum_day),
                "geburtsdatum_month": str(profile_data.geburtsdatum_month),
                "geburtsdatum_year": str(profile_data.geburtsdatum_year),
                # 可以根据需要添加更多字段映射
            }
        else:
            logging.error(f"未知的profile类型: {profile_type}")
            return None
            
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
        
        # 检查是否提交成功
        if "Schritt 6" in res.text:
            logging.info("预约成功！")
            return True, res
        elif "zu vieler Terminanfragen" in res.text:
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