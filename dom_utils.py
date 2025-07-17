# -*- coding: utf-8 -*-

import bs4
import logging


def check_no_appointments_available(html_content):
    """
    使用DOM解析检查是否没有可用预约时间
    相比简单的字符串搜索，这种方法更加健壮，能够避免因页面结构微调或动态内容而产生的误报
    
    :param html_content: HTML响应内容
    :return: True如果没有可用预约时间，False如果有可用时间或无法确定
    """
    try:
        soup = bs4.BeautifulSoup(html_content, 'html.parser')
        
        # 方法1: 查找包含特定文本的元素
        no_appointment_text = soup.find(string=lambda text: 
            text and 'Kein freier Termin verfügbar' in text.strip() if text else False)
        
        if no_appointment_text:
            logging.debug("通过文本内容检测到无可用预约时间")
            return True
            
        # 方法2: 查找可能的错误或通知元素
        # 检查常见的通知、警告或错误消息容器
        notification_selectors = [
            '.notification', '.alert', '.warning', '.error',
            '.message', '.info', '[class*="termin"]', '[class*="appointment"]'
        ]
        
        for selector in notification_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element.get_text() and 'Kein freier Termin' in element.get_text():
                    logging.debug(f"通过CSS选择器 {selector} 检测到无可用预约时间")
                    return True
        
        # 方法3: 检查是否存在预约时间容器
        # 如果页面中存在预约时间容器，说明有可用时间
        appointment_containers = soup.find("details", {"id": "details_suggest_times"})
        if not appointment_containers:
            appointment_containers = soup.find("div", {"id": "sugg_accordion"})
            
        if appointment_containers:
            # 进一步检查容器内是否真的有预约表单
            forms = appointment_containers.find_all("form", {"class": "suggestion_form"})
            if forms:
                logging.debug("检测到预约时间容器且包含预约表单")
                return False
                
        # 默认情况：如果无法明确判断，返回原始字符串搜索结果作为后备
        return 'Kein freier Termin verfügbar' in html_content
        
    except Exception as e:
        logging.warning(f"DOM解析检查预约可用性时发生错误: {e}")
        # 出错时回退到原始字符串搜索
        return 'Kein freier Termin verfügbar' in html_content


def check_step_completion(html_content, step_number):
    """
    使用DOM解析检查是否到达了指定的步骤
    
    :param html_content: HTML响应内容
    :param step_number: 要检查的步骤编号 (如 6)
    :return: True如果到达了指定步骤，False否则
    """
    try:
        soup = bs4.BeautifulSoup(html_content, 'html.parser')
        step_text = f"Schritt {step_number}"
        
        # 方法1: 查找包含步骤文本的标题元素
        step_headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for header in step_headers:
            if header.get_text() and step_text in header.get_text():
                logging.debug(f"通过标题元素检测到{step_text}")
                return True
                
        # 方法2: 查找包含步骤文本的任何元素
        step_element = soup.find(string=lambda text: 
            text and step_text in text.strip() if text else False)
            
        if step_element:
            logging.debug(f"通过文本内容检测到{step_text}")
            return True
            
        # 方法3: 查找可能的进度指示器或步骤导航
        progress_selectors = [
            '.step', '.progress', '.wizard', '.breadcrumb',
            '[class*="step"]', '[class*="progress"]'
        ]
        
        for selector in progress_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element.get_text() and step_text in element.get_text():
                    logging.debug(f"通过CSS选择器 {selector} 检测到{step_text}")
                    return True
        
        # 后备方案：原始字符串搜索
        return step_text in html_content
        
    except Exception as e:
        logging.warning(f"DOM解析检查步骤完成时发生错误: {e}")
        # 出错时回退到原始字符串搜索
        return f"Schritt {step_number}" in html_content


def check_rate_limit_error(html_content):
    """
    使用DOM解析检查是否出现了请求过多的错误
    
    :param html_content: HTML响应内容
    :return: True如果检测到频率限制错误，False否则
    """
    try:
        soup = bs4.BeautifulSoup(html_content, 'html.parser')
        rate_limit_text = "zu vieler Terminanfragen"
        
        # 方法1: 查找包含特定文本的元素
        rate_limit_element = soup.find(string=lambda text: 
            text and rate_limit_text in text.strip() if text else False)
            
        if rate_limit_element:
            logging.debug("通过文本内容检测到频率限制错误")
            return True
            
        # 方法2: 查找可能的错误消息容器
        error_selectors = [
            '.error', '.alert', '.warning', '.notification',
            '.message', '[class*="error"]', '[class*="alert"]'
        ]
        
        for selector in error_selectors:
            elements = soup.select(selector)
            for element in elements:
                if element.get_text() and rate_limit_text in element.get_text():
                    logging.debug(f"通过CSS选择器 {selector} 检测到频率限制错误")
                    return True
        
        # 后备方案：原始字符串搜索
        return rate_limit_text in html_content
        
    except Exception as e:
        logging.warning(f"DOM解析检查频率限制错误时发生错误: {e}")
        # 出错时回退到原始字符串搜索
        return "zu vieler Terminanfragen" in html_content