import requests
import bs4
import logging
import os
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

def save_page_content(content, step_name):
    """
    保存页面内容到文件
    :param content: 页面内容
    :param step_name: 步骤名称
    """
    # 创建 pages 目录（如果不存在）
    if not os.path.exists('pages'):
        os.makedirs('pages')
    
    # 生成文件名，包含时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'pages/step_{step_name}_{timestamp}.html'
    
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

def check_availability(session):
    """
    检查是否有可用预约时间
    :param session: requests.Session 对象
    :return: (是否有可用时间, 详细信息)
    """
    url = 'https://termine.staedteregion-aachen.de/auslaenderamt/suggest'
    res = session.get(url)
    # save_page_content(res.text, '4_availability')
    
    if "Kein freier Termin verfügbar" not in res.text:
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        div = soup.find("div", {"id": "sugg_accordion"})
        if div:
            h3_tags = div.find_all("h3")
            appointments = "\n".join([h.text for h in h3_tags])
            return True, f"发现可用预约时间：\n{appointments}"
        return True, "发现可用预约时间，但无法解析具体时间"
    
    return False, "当前没有可用预约时间"

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
    return check_availability(session)

if __name__ == "__main__":
    has_appointment, message = check_appointment()
    print(message) 