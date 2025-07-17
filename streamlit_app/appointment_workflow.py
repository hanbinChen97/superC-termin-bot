# -*- coding: utf-8 -*-

import requests
import bs4
import logging
from urllib.parse import urljoin
import sys
import os

# Add parent directory to path to import from main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import BASE_URL, USER_AGENT, LOCATIONS


def setup_session_and_config(location_name="superc"):
    """
    设置会话和位置配置
    """
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    location_config = LOCATIONS[location_name]
    return session, location_config


def get_initial_page(session, steps):
    """
    步骤1&2: 获取初始页面 (Schritt 1 & 2)
    """
    try:
        url = urljoin(BASE_URL, 'select2?md=1')
        res = session.get(url)
        steps.append({
            "step": "1-2",
            "title": "获取初始页面",
            "status": "success" if res.status_code == 200 else "error",
            "message": f"成功获取初始页面 (状态码: {res.status_code})" if res.status_code == 200 else f"获取失败 (状态码: {res.status_code})",
            "url": url
        })
        return True, res
    except Exception as e:
        steps.append({
            "step": "1-2", 
            "title": "获取初始页面",
            "status": "error",
            "message": f"请求失败: {str(e)}",
            "url": url
        })
        return False, str(e)


def select_location_type(session, location_config, res, steps):
    """
    步骤3: 根据文本选择预约地点类型 (z.B. Super C oder Infostelle)
    """
    try:
        selection_text = location_config["selection_text"]
        soup = bs4.BeautifulSoup(res.content, 'html.parser')
        header = soup.find("h3", string=lambda s: selection_text in s if s else False)
        
        if not header:
            steps.append({
                "step": "3",
                "title": "选择地点类型",
                "status": "error", 
                "message": f"无法找到包含 '{selection_text}' 的选项",
                "details": f"查找的文本: {selection_text}"
            })
            return False, f"无法找到包含 '{selection_text}' 的选项"
        
        next_sibling = header.find_next_sibling()
        if not next_sibling:
            steps.append({
                "step": "3",
                "title": "选择地点类型", 
                "status": "error",
                "message": "无法找到预约选项的同级元素",
                "details": f"找到头部元素但没有同级选项"
            })
            return False, "无法找到预约选项的同级元素"
        
        li_elements = next_sibling.find_all("li")
        if not li_elements:
            steps.append({
                "step": "3",
                "title": "选择地点类型",
                "status": "error", 
                "message": "无法找到预约选项列表",
                "details": "同级元素中没有 li 标签"
            })
            return False, "无法找到预约选项列表"
        
        cnc_id = li_elements[0].get("id").split("-")[-1]
        url = urljoin(BASE_URL, f"location?mdt=89&select_cnc=1&cnc-{cnc_id}=1")
        
        steps.append({
            "step": "3",
            "title": "选择地点类型",
            "status": "success",
            "message": f"成功选择 {selection_text}",
            "details": f"构建的URL: {url}",
            "url": url
        })
        return True, url
        
    except Exception as e:
        steps.append({
            "step": "3",
            "title": "选择地点类型",
            "status": "error",
            "message": f"处理失败: {str(e)}",
            "details": f"选择文本: {selection_text}"
        })
        return False, str(e)


def get_location_info(session, url, steps):
    """
    步骤3: 获取并确认位置信息 (Schritt 3)
    """
    try:
        res = session.get(url)
        soup = bs4.BeautifulSoup(res.content, 'html.parser')
        loc = soup.find('input', {'name': 'loc'})
        
        if not loc:
            steps.append({
                "step": "3",
                "title": "获取位置信息",
                "status": "error",
                "message": "无法在页面上找到位置信息 'loc'",
                "url": url
            })
            return False, "无法在页面上找到位置信息 'loc'"
        
        loc_value = loc.get('value')
        steps.append({
            "step": "3",
            "title": "获取位置信息", 
            "status": "success",
            "message": f"成功获取位置信息",
            "details": f"位置ID: {loc_value}",
            "url": url
        })
        return True, (loc_value, res)
        
    except Exception as e:
        steps.append({
            "step": "3",
            "title": "获取位置信息",
            "status": "error", 
            "message": f"请求失败: {str(e)}",
            "url": url
        })
        return False, str(e)


def submit_location(session, location_config, url, loc, steps):
    """
    步骤4: 提交位置信息并检查可用性
    """
    try:
        submit_text = location_config["submit_text"]
        payload = {
            'loc': str(loc),
            'gps_lat': '55.77858',
            'gps_long': '65.07867',
            'select_location': submit_text
        }
        res = session.post(url, data=payload)
        
        steps.append({
            "step": "4",
            "title": "提交位置信息",
            "status": "success" if res.status_code == 200 else "error",
            "message": f"成功提交位置信息" if res.status_code == 200 else f"提交失败 (状态码: {res.status_code})",
            "details": f"提交文本: {submit_text}",
            "payload": payload
        })
        return True, res
        
    except Exception as e:
        steps.append({
            "step": "4", 
            "title": "提交位置信息",
            "status": "error",
            "message": f"提交失败: {str(e)}",
            "details": f"提交文本: {submit_text}"
        })
        return False, str(e)


def check_availability(session, steps):
    """
    步骤4: 检查是否有可用预约时间 (不进行预约)
    """
    try:
        url = urljoin(BASE_URL, 'suggest')
        res = session.get(url)
        
        if "Kein freier Termin verfügbar" in res.text:
            steps.append({
                "step": "4",
                "title": "检查预约可用性",
                "status": "info",
                "message": "当前没有可用预约时间",
                "details": "网站显示: Kein freier Termin verfügbar",
                "url": url
            })
            return False, "查询完成，当前没有可用预约时间"

        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        details_container = soup.find("details", {"id": "details_suggest_times"})
        if not details_container:
            details_container = soup.find("div", {"id": "sugg_accordion"})

        if not details_container:
            steps.append({
                "step": "4",
                "title": "检查预约可用性",
                "status": "warning",
                "message": "在预约页面找不到时间容器",
                "details": "页面结构可能已改变",
                "url": url
            })
            return False, "在预约页面找不到时间容器"

        # 查找可用时间
        forms = details_container.find_all("form", {"class": "suggestion_form"})
        available_times = []
        
        for form in forms:
            # 提取日期信息
            summary_tag = form.find_previous("summary")
            date_display = summary_tag.text.strip() if summary_tag else "未知日期"
            
            # 提取时间信息
            time_button = form.find("button", {"type": "submit"})
            time_info = time_button.get('title') if time_button else "未知时间"
            
            available_times.append(f"{date_display} - {time_info}")

        if available_times:
            steps.append({
                "step": "4",
                "title": "检查预约可用性",
                "status": "success",
                "message": f"发现 {len(available_times)} 个可用预约时间",
                "details": "可用时间:\n" + "\n".join(available_times[:5]),  # 显示前5个
                "available_count": len(available_times),
                "url": url
            })
            return True, f"发现 {len(available_times)} 个可用预约时间"
        else:
            steps.append({
                "step": "4", 
                "title": "检查预约可用性",
                "status": "info",
                "message": "有时间容器但没有找到具体的可用时间",
                "details": "页面结构可能已改变或时间已被占用",
                "url": url
            })
            return False, "有时间容器但没有找到具体的可用时间"
            
    except Exception as e:
        steps.append({
            "step": "4",
            "title": "检查预约可用性", 
            "status": "error",
            "message": f"检查失败: {str(e)}",
            "url": url
        })
        return False, str(e)


def run_workflow(location_name="superc"):
    """
    运行完整的预约检查流程 (步骤1-4)
    """
    steps = []  # 初始化步骤记录
    
    # 设置会话和配置
    session, location_config = setup_session_and_config(location_name)
    
    # 步骤1-2: 获取初始页面
    success, res = get_initial_page(session, steps)
    if not success:
        return False, "获取初始页面失败", steps

    # 步骤3: 选择地点类型
    success, url = select_location_type(session, location_config, res, steps)
    if not success:
        return False, "选择地点类型失败", steps

    # 步骤3: 获取位置信息
    success, result = get_location_info(session, url, steps)
    if not success:
        return False, "获取位置信息失败", steps
    loc, res = result

    # 步骤4: 提交位置信息
    success, res = submit_location(session, location_config, url, loc, steps)
    if not success:
        return False, "提交位置信息失败", steps

    # 步骤4: 检查预约可用性
    success, message = check_availability(session, steps)
    
    return True, message, steps