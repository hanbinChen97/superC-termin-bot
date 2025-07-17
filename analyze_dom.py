#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DOM结构分析工具
运行一轮完整的预约检查流程，保存每个步骤的网页内容，然后分析HTML结构
用于改进DOM解析逻辑，替代简单的字符串搜索
"""

import requests
import bs4
import logging
import os
import json
from urllib.parse import urljoin
from datetime import datetime

from config import BASE_URL, USER_AGENT, LOCATIONS
from utils import save_page_content, download_captcha


class DOMAnalyzer:
    """DOM结构分析器"""
    
    def __init__(self, location_name="superc"):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.location_config = LOCATIONS[location_name]
        self.location_name = location_name
        self.saved_pages = []
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 创建保存目录
        self.pages_dir = f'pages/{self.location_name}/analysis'
        if not os.path.exists(self.pages_dir):
            os.makedirs(self.pages_dir)
    
    def save_step_content(self, content, step_name, description=""):
        """保存步骤内容并记录文件路径"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{self.pages_dir}/step_{step_name}_{timestamp}.html'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.saved_pages.append({
            'step': step_name,
            'description': description,
            'filename': filename,
            'timestamp': timestamp
        })
        
        logging.info(f'步骤 {step_name} ({description}) 页面已保存到: {filename}')
        return filename
    
    def step1_get_initial_page(self):
        """步骤1: 获取初始页面 (Schritt 1 & 2)"""
        logging.info("=== 步骤1: 获取初始页面 ===")
        
        url = urljoin(BASE_URL, 'select2?md=1')
        res = self.session.get(url)
        
        self.save_step_content(res.text, "1_initial", "获取初始页面")
        
        if res.status_code == 200:
            logging.info("✓ 成功获取初始页面")
            return True, res
        else:
            logging.error(f"✗ 获取初始页面失败，状态码: {res.status_code}")
            return False, res
    
    def step2_select_location_type(self, res):
        """步骤2: 选择预约地点类型"""
        logging.info("=== 步骤2: 选择预约地点类型 ===")
        
        soup = bs4.BeautifulSoup(res.content, 'html.parser')
        selection_text = self.location_config["selection_text"]
        
        header = soup.find("h3", string=lambda s: selection_text in s if s else False)
        if not header:
            logging.error(f"✗ 无法找到包含 '{selection_text}' 的选项")
            return False, f"无法找到包含 '{selection_text}' 的选项"
        
        next_sibling = header.find_next_sibling()
        if not next_sibling:
            logging.error("✗ 无法找到预约选项的同级元素")
            return False, "无法找到预约选项的同级元素"
        
        li_elements = next_sibling.find_all("li")
        if not li_elements:
            logging.error("✗ 无法找到预约选项列表")
            return False, "无法找到预约选项列表"
        
        cnc_id = li_elements[0].get("id").split("-")[-1]
        url = urljoin(BASE_URL, f"location?mdt=89&select_cnc=1&cnc-{cnc_id}=1")
        
        logging.info(f"✓ 成功构建地点类型URL: {url}")
        return True, url
    
    def step3_get_location_info(self, url):
        """步骤3: 获取位置信息 (Schritt 3)"""
        logging.info("=== 步骤3: 获取位置信息 ===")
        
        res = self.session.get(url)
        self.save_step_content(res.text, "3_location_info", "获取位置信息")
        
        soup = bs4.BeautifulSoup(res.content, 'html.parser')
        loc = soup.find('input', {'name': 'loc'})
        
        if not loc:
            logging.error("✗ 无法在页面上找到位置信息 'loc'")
            return False, "无法在页面上找到位置信息 'loc'"
        
        logging.info(f"✓ 成功获取位置信息: {loc.get('value')}")
        return True, (loc.get('value'), res, url)
    
    def step4_submit_location(self, url, loc):
        """步骤4: 提交位置信息"""
        logging.info("=== 步骤4: 提交位置信息 ===")
        
        payload = {
            'loc': str(loc),
            'gps_lat': '55.77858',
            'gps_long': '65.07867',
            'select_location': self.location_config["submit_text"]
        }
        
        res = self.session.post(url, data=payload)
        self.save_step_content(res.text, "4_location_submitted", "提交位置信息")
        
        logging.info("✓ 成功提交位置信息")
        return True, res
    
    def step5_check_appointments(self):
        """步骤5: 检查预约时间可用性 (Schritt 4)"""
        logging.info("=== 步骤5: 检查预约时间可用性 ===")
        
        url = urljoin(BASE_URL, 'suggest')
        res = self.session.get(url)
        self.save_step_content(res.text, "5_availability_check", "检查预约时间可用性")
        
        # 分析页面内容
        soup = bs4.BeautifulSoup(res.text, 'html.parser')
        
        # 检查是否有"无可用时间"的消息
        no_appointment_indicators = [
            "Kein freier Termin verfügbar",
            "keine Termine",
            "nicht verfügbar"
        ]
        
        has_no_appointments = False
        for indicator in no_appointment_indicators:
            if indicator in res.text:
                has_no_appointments = True
                logging.info(f"✓ 检测到无可用预约提示: {indicator}")
                break
        
        # 检查是否有预约时间容器
        details_container = soup.find("details", {"id": "details_suggest_times"})
        if not details_container:
            details_container = soup.find("div", {"id": "sugg_accordion"})
        
        has_appointment_container = bool(details_container)
        
        if has_appointment_container:
            forms = details_container.find_all("form", {"class": "suggestion_form"})
            appointment_forms_count = len(forms)
            logging.info(f"✓ 发现预约时间容器，包含 {appointment_forms_count} 个预约表单")
        else:
            appointment_forms_count = 0
            logging.info("✓ 未发现预约时间容器")
        
        return True, {
            'response': res,
            'has_no_appointments': has_no_appointments,
            'has_appointment_container': has_appointment_container,
            'appointment_forms_count': appointment_forms_count,
            'soup': soup
        }
    
    def step6_select_appointment(self, analysis_result):
        """步骤6: 选择预约时间 (如果有可用时间)"""
        logging.info("=== 步骤6: 选择预约时间 ===")
        
        if analysis_result['has_no_appointments'] or analysis_result['appointment_forms_count'] == 0:
            logging.info("✓ 无可用预约时间，跳过选择步骤")
            return True, None
        
        soup = analysis_result['soup']
        details_container = soup.find("details", {"id": "details_suggest_times"})
        if not details_container:
            details_container = soup.find("div", {"id": "sugg_accordion"})
        
        first_available_form = details_container.find("form", {"class": "suggestion_form"})
        
        if not first_available_form:
            logging.warning("✗ 有可用时间但无法找到具体的预约表单")
            return False, "有可用时间但无法找到具体的预约表单"
        
        # 提取表单数据但不提交（避免实际预约）
        form_data = {inp.get('name'): inp.get('value') 
                    for inp in first_available_form.find_all("input", {"type": "hidden"})}
        
        # 获取时间信息用于日志
        summary_tag = details_container.find("summary")
        date_display = summary_tag.text.strip() if summary_tag else "未知日期"
        
        time_button = first_available_form.find("button", {"type": "submit"})
        time_info = time_button.get('title') if time_button else "未知时间"
        
        logging.info(f"✓ 找到可用时间: {date_display} {time_info}")
        logging.info("⚠️  已模拟选择预约时间，但未实际提交（避免真实预约）")
        
        return True, {
            'form_data': form_data,
            'date_display': date_display,
            'time_info': time_info
        }
    
    def step7_get_form_page(self, appointment_info):
        """步骤7: 获取表单页面 (如果有预约可选择)"""
        if not appointment_info:
            logging.info("=== 步骤7: 跳过表单页面获取 (无可用预约) ===")
            return True, None
        
        logging.info("=== 步骤7: 模拟获取表单页面 ===")
        
        # 这里应该提交预约选择，但为了避免实际预约，我们跳过
        # 在实际场景中，这里会提交 appointment_info['form_data']
        logging.info("⚠️  已跳过实际的表单页面获取（避免真实预约）")
        logging.info("   在真实场景中，这里会提交预约选择并获取最终表单页面")
        
        return True, None
    
    def analyze_saved_pages(self):
        """分析保存的页面内容"""
        logging.info("\n" + "="*50)
        logging.info("开始分析保存的页面内容")
        logging.info("="*50)
        
        analysis_results = {}
        
        for page_info in self.saved_pages:
            logging.info(f"\n--- 分析 {page_info['step']} ({page_info['description']}) ---")
            
            try:
                with open(page_info['filename'], 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = bs4.BeautifulSoup(content, 'html.parser')
                
                # 基本页面信息
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "无标题"
                
                # 查找主要内容区域
                main_content = soup.find('main') or soup.find('div', class_='content') or soup.find('body')
                
                # 查找步骤指示器
                step_indicators = []
                for text in soup.find_all(string=lambda s: s and 'Schritt' in s):
                    step_indicators.append(text.strip())
                
                # 查找表单
                forms = soup.find_all('form')
                form_info = []
                for form in forms:
                    inputs = form.find_all('input')
                    form_info.append({
                        'action': form.get('action', '无action'),
                        'method': form.get('method', 'GET'),
                        'input_count': len(inputs),
                        'input_names': [inp.get('name') for inp in inputs if inp.get('name')]
                    })
                
                # 查找错误和状态消息
                error_indicators = []
                status_messages = []
                
                # 常见的错误和状态消息关键词
                error_keywords = ['error', 'fehler', 'kein', 'nicht', 'failed', 'problem']
                status_keywords = ['success', 'erfolgreich', 'schritt', 'complete', 'fertig']
                
                for text in soup.find_all(string=True):
                    if text and text.strip():
                        text_lower = text.strip().lower()
                        for keyword in error_keywords:
                            if keyword in text_lower:
                                error_indicators.append(text.strip())
                                break
                        for keyword in status_keywords:
                            if keyword in text_lower:
                                status_messages.append(text.strip())
                                break
                
                # 查找预约相关元素
                appointment_elements = soup.find_all(id=lambda x: x and ('suggest' in x or 'termin' in x or 'appointment' in x))
                
                page_analysis = {
                    'title': title_text,
                    'step_indicators': step_indicators,
                    'forms_count': len(forms),
                    'forms_info': form_info,
                    'error_indicators': error_indicators[:5],  # 限制数量
                    'status_messages': status_messages[:5],   # 限制数量
                    'appointment_elements': [elem.name + '#' + str(elem.get('id')) for elem in appointment_elements],
                    'content_length': len(content)
                }
                
                analysis_results[page_info['step']] = page_analysis
                
                # 打印分析结果
                print(f"  标题: {title_text}")
                print(f"  步骤指示器: {step_indicators}")
                print(f"  表单数量: {len(forms)}")
                if form_info:
                    print(f"  表单详情: {form_info[0] if form_info else '无'}")
                print(f"  错误指示器: {error_indicators[:3]}")
                print(f"  状态消息: {status_messages[:3]}")
                print(f"  预约相关元素: {[elem.name + '#' + str(elem.get('id')) for elem in appointment_elements]}")
                print(f"  内容长度: {len(content)} 字符")
                
            except Exception as e:
                logging.error(f"分析页面 {page_info['step']} 时出错: {e}")
                analysis_results[page_info['step']] = {'error': str(e)}
        
        # 保存分析结果
        analysis_file = f'{self.pages_dir}/analysis_results.json'
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'location': self.location_name,
                'pages_analyzed': len(self.saved_pages),
                'results': analysis_results
            }, f, ensure_ascii=False, indent=2)
        
        logging.info(f"\n分析结果已保存到: {analysis_file}")
        
        return analysis_results
    
    def generate_dom_recommendations(self, analysis_results):
        """基于分析结果生成DOM解析建议"""
        logging.info("\n" + "="*50)
        logging.info("生成DOM解析建议")
        logging.info("="*50)
        
        recommendations = []
        
        # 分析步骤指示器模式
        step_patterns = set()
        for step, analysis in analysis_results.items():
            if 'step_indicators' in analysis:
                step_patterns.update(analysis['step_indicators'])
        
        if step_patterns:
            recommendations.append({
                'category': '步骤检测',
                'suggestion': '使用以下选择器检测页面步骤',
                'implementation': '''
def check_step_completion(html_content, step_number):
    soup = BeautifulSoup(html_content, 'html.parser')
    step_text = f"Schritt {step_number}"
    
    # 方法1: 查找标题元素
    headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    for header in headers:
        if step_text in header.get_text():
            return True
    
    # 方法2: 查找包含步骤文本的任何元素
    step_element = soup.find(string=lambda text: 
        text and step_text in text.strip() if text else False)
    return bool(step_element)
                ''',
                'detected_patterns': list(step_patterns)
            })
        
        # 分析错误消息模式
        error_patterns = set()
        for step, analysis in analysis_results.items():
            if 'error_indicators' in analysis:
                error_patterns.update(analysis['error_indicators'])
        
        if error_patterns:
            recommendations.append({
                'category': '错误检测',
                'suggestion': '使用以下方法检测错误消息',
                'implementation': '''
def check_no_appointments_available(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 检查常见错误消息
    error_texts = ["Kein freier Termin verfügbar", "keine Termine"]
    for error_text in error_texts:
        if soup.find(string=lambda text: 
            text and error_text in text.strip() if text else False):
            return True
    
    # 检查错误消息容器
    error_selectors = ['.error', '.alert', '.warning', '.notification']
    for selector in error_selectors:
        elements = soup.select(selector)
        for element in elements:
            if any(error_text in element.get_text() for error_text in error_texts):
                return True
    
    return False
                ''',
                'detected_patterns': list(error_patterns)[:10]
            })
        
        # 分析表单模式
        form_patterns = {}
        for step, analysis in analysis_results.items():
            if 'forms_info' in analysis and analysis['forms_info']:
                form_patterns[step] = analysis['forms_info']
        
        if form_patterns:
            recommendations.append({
                'category': '表单检测',
                'suggestion': '使用以下方法检测和处理表单',
                'implementation': '''
def find_appointment_forms(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找预约时间容器
    containers = [
        soup.find("details", {"id": "details_suggest_times"}),
        soup.find("div", {"id": "sugg_accordion"})
    ]
    
    for container in containers:
        if container:
            forms = container.find_all("form", {"class": "suggestion_form"})
            return forms
    
    return []
                ''',
                'detected_patterns': form_patterns
            })
        
        # 保存建议
        recommendations_file = f'{self.pages_dir}/dom_recommendations.json'
        with open(recommendations_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'location': self.location_name,
                'recommendations': recommendations
            }, f, ensure_ascii=False, indent=2)
        
        # 打印建议
        for rec in recommendations:
            print(f"\n{rec['category']}:")
            print(f"  建议: {rec['suggestion']}")
            print(f"  检测到的模式: {rec['detected_patterns']}")
            print(f"  实现建议: {rec['implementation']}")
        
        logging.info(f"\nDOM解析建议已保存到: {recommendations_file}")
        
        return recommendations
    
    def run_analysis(self):
        """运行完整的分析流程"""
        logging.info("开始运行一轮完整的预约流程分析")
        logging.info(f"分析地点: {self.location_name}")
        
        try:
            # 步骤1: 获取初始页面
            success, res = self.step1_get_initial_page()
            if not success:
                return False, "步骤1失败"
            
            # 步骤2: 选择预约地点类型
            success, url = self.step2_select_location_type(res)
            if not success:
                return False, f"步骤2失败: {url}"
            
            # 步骤3: 获取位置信息
            success, result = self.step3_get_location_info(url)
            if not success:
                return False, f"步骤3失败: {result}"
            loc, res, url = result
            
            # 步骤4: 提交位置信息
            success, res = self.step4_submit_location(url, loc)
            if not success:
                return False, "步骤4失败"
            
            # 步骤5: 检查预约时间可用性
            success, analysis_result = self.step5_check_appointments()
            if not success:
                return False, "步骤5失败"
            
            # 步骤6: 选择预约时间（模拟）
            success, appointment_info = self.step6_select_appointment(analysis_result)
            if not success:
                return False, f"步骤6失败: {appointment_info}"
            
            # 步骤7: 获取表单页面（模拟）
            success, form_info = self.step7_get_form_page(appointment_info)
            if not success:
                return False, "步骤7失败"
            
            # 分析保存的页面
            analysis_results = self.analyze_saved_pages()
            
            # 生成DOM解析建议
            recommendations = self.generate_dom_recommendations(analysis_results)
            
            logging.info("\n✓ 分析流程完成！")
            logging.info(f"✓ 共保存 {len(self.saved_pages)} 个页面")
            logging.info(f"✓ 生成 {len(recommendations)} 条DOM解析建议")
            
            return True, {
                'saved_pages': len(self.saved_pages),
                'analysis_results': analysis_results,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logging.error(f"分析过程中发生错误: {e}", exc_info=True)
            return False, f"分析失败: {str(e)}"


def main():
    """主函数"""
    print("DOM结构分析工具")
    print("="*50)
    
    # 选择分析的地点
    location = "superc"  # 可以改为 "infostelle"
    
    analyzer = DOMAnalyzer(location)
    success, result = analyzer.run_analysis()
    
    if success:
        print(f"\n✓ 分析完成！")
        print(f"  保存页面数: {result['saved_pages']}")
        print(f"  建议数量: {len(result['recommendations'])}")
        print(f"  结果保存在: pages/{location}/analysis/")
    else:
        print(f"\n✗ 分析失败: {result}")


if __name__ == "__main__":
    main()