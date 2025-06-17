import json
import logging
import os
from datetime import datetime
from urllib.parse import urljoin
from llmCall import recognize_captcha

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

def save_page_content(content, step_name):
    """
    保存页面内容到文件
    :param content: 页面内容
    :param step_name: 步骤名称
    """
    if not os.path.exists('pages/infostelle'):
        os.makedirs('pages/infostelle')
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'pages/infostelle/step_{step_name}_{timestamp}.html'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f'页面内容已保存到: {filename}')

def load_personal_info():
    """
    从 table 文件加载个人信息
    :return: 个人信息字典
    """
    try:
        with open('table', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {item['fuellen_in_name']: item['wert_zum_fuellen'] for item in data}
    except Exception as e:
        logging.error(f"加载个人信息失败: {str(e)}")
        return None

def fill_form(session, soup, captcha_image_path):
    """
    填写表单并提交
    :param session: requests.Session 对象
    :param soup: BeautifulSoup 对象
    :param captcha_image_path: 验证码图片路径
    :return: (是否成功, 响应对象或错误信息)
    """
    print("\n开始填写表单...")
    
    # 加载个人信息
    personal_info = load_personal_info()
    if not personal_info:
        return False, "无法加载个人信息"
    print(f"已加载个人信息: {personal_info}")

    # 识别验证码
    print(f"\n开始识别验证码: {captcha_image_path}")
    captcha_text = recognize_captcha(captcha_image_path)
    print(f"验证码识别结果: {captcha_text}")
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
    print(f"\n准备提交的表单数据: {form_data}")

    # 获取表单提交URL
    form = soup.find('form')
    if not form:
        return False, "无法找到表单"
    print(f"\n找到表单: {form.get('action')}")

    # 获取所有隐藏字段
    hidden_fields = {}
    for hidden_input in form.find_all('input', type='hidden'):
        hidden_fields[hidden_input.get('name')] = hidden_input.get('value')
    print(f"找到隐藏字段: {hidden_fields}")
    form_data.update(hidden_fields)

    # 拼接 action url
    submit_url = urljoin('https://termine.staedteregion-aachen.de/auslaenderamt/', form.get('action'))
    print(f"\n提交URL: {submit_url}")

    # 提交表单
    try:
        headers = {
            'User-Agent': USER_AGENT,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://termine.staedteregion-aachen.de/auslaenderamt/'
        }
        print(f"\n准备提交请求，headers: {headers}")
        res = session.post(submit_url, data=form_data, headers=headers)
        save_page_content(res.text, '6_form_submitted')
        print(f"\n表单提交响应状态码: {res.status_code}")
        
        # 检查是否提交成功
        if "Schritt 6" in res.text:
            print("预约成功！")
            return True, res
        else:
            error_message = "表单提交失败"
            if "captcha" in res.text.lower():
                error_message += "，验证码可能不正确"
            if "agreement" in res.text.lower():
                error_message += "，请确认已勾选同意条款"
            print(f"\n错误信息: {error_message}")
            print(f"响应内容: {res.text[:500]}...")
            return False, error_message
            
    except Exception as e:
        error_msg = f"提交表单时发生错误: {str(e)}"
        print(f"\n错误: {error_msg}")
        return False, error_msg 