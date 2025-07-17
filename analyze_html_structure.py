#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML结构分析工具 - 离线版本
分析保存的HTML文件以及生成的示例HTML内容，提供DOM解析改进建议
"""

import os
import json
import logging
from datetime import datetime
from bs4 import BeautifulSoup


class HTMLStructureAnalyzer:
    """HTML结构分析器"""
    
    def __init__(self):
        self.analysis_results = {}
        self.recommendations = []
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # 创建输出目录
        self.output_dir = 'pages/analysis'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def create_sample_html_files(self):
        """创建示例HTML文件用于分析"""
        sample_files = {
            'step1_initial_page.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Terminvergabe - Ausländeramt Aachen</title>
</head>
<body>
    <h1>Terminvergabe</h1>
    <h2>Schritt 1: Auswahl des Dienstleistungsbereichs</h2>
    <div class="content">
        <h3>Für welchen Bereich möchten Sie einen Termin vereinbaren?</h3>
        <ul>
            <li id="cnc-1"><a href="#">Super C</a></li>
            <li id="cnc-2"><a href="#">Infostelle</a></li>
        </ul>
    </div>
</body>
</html>
            ''',
            
            'step3_location_info.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Terminvergabe - Standort auswählen</title>
</head>
<body>
    <h1>Terminvergabe</h1>
    <h2>Schritt 3: Standort auswählen</h2>
    <form method="post">
        <input type="hidden" name="loc" value="12345">
        <div class="location-info">
            <h3>Ausländeramt Aachen - Außenstelle RWTH</h3>
            <p>Adresse: Super C, Templergraben 57</p>
        </div>
        <button type="submit" name="select_location">Standort auswählen</button>
    </form>
</body>
</html>
            ''',
            
            'step4_no_appointments.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Terminvergabe - Kein Termin verfügbar</title>
</head>
<body>
    <h1>Terminvergabe</h1>
    <h2>Schritt 4: Terminauswahl</h2>
    <div class="message error">
        <p>Kein freier Termin verfügbar</p>
        <p>Bitte versuchen Sie es zu einem späteren Zeitpunkt erneut.</p>
    </div>
    <div class="notification">
        <span class="icon warning"></span>
        <span>Derzeit keine Termine verfügbar</span>
    </div>
</body>
</html>
            ''',
            
            'step4_appointments_available.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Terminvergabe - Termine verfügbar</title>
</head>
<body>
    <h1>Terminvergabe</h1>
    <h2>Schritt 4: Terminauswahl</h2>
    <div id="sugg_accordion">
        <details id="details_suggest_times" open>
            <summary>Mittwoch, 27.08.2025</summary>
            <div class="time-slots">
                <form class="suggestion_form" action="/suggest" method="post">
                    <input type="hidden" name="date" value="2025-08-27">
                    <input type="hidden" name="time" value="09:00">
                    <button type="submit" title="09:00 - 09:30">09:00 Uhr</button>
                </form>
                <form class="suggestion_form" action="/suggest" method="post">
                    <input type="hidden" name="date" value="2025-08-27">
                    <input type="hidden" name="time" value="10:00">
                    <button type="submit" title="10:00 - 10:30">10:00 Uhr</button>
                </form>
            </div>
        </details>
    </div>
</body>
</html>
            ''',
            
            'step5_appointment_selected.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Terminvergabe - Schritt 5</title>
</head>
<body>
    <h1>Terminvergabe</h1>
    <h2>Schritt 5: Persönliche Daten</h2>
    <div class="progress">
        <span class="step completed">1</span>
        <span class="step completed">2</span>
        <span class="step completed">3</span>
        <span class="step completed">4</span>
        <span class="step active">5</span>
        <span class="step">6</span>
    </div>
    <form action="/form" method="post">
        <div class="appointment-summary">
            <h3>Ihr gewählter Termin:</h3>
            <p>Mittwoch, 27.08.2025 um 09:00 Uhr</p>
        </div>
        <div class="form-fields">
            <input type="text" name="vorname" placeholder="Vorname">
            <input type="text" name="nachname" placeholder="Nachname">
        </div>
    </form>
</body>
</html>
            ''',
            
            'step6_form_success.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Terminvergabe - Erfolgreich</title>
</head>
<body>
    <h1>Terminvergabe</h1>
    <h2>Schritt 6: Bestätigung</h2>
    <div class="success-message">
        <div class="alert success">
            <h3>Ihr Termin wurde erfolgreich gebucht!</h3>
            <p>Sie erhalten eine Bestätigungs-E-Mail.</p>
        </div>
    </div>
    <div class="appointment-details">
        <h3>Termindetails:</h3>
        <p>Datum: Mittwoch, 27.08.2025</p>
        <p>Uhrzeit: 09:00 - 09:30 Uhr</p>
        <p>Standort: Super C, Templergraben 57</p>
    </div>
</body>
</html>
            ''',
            
            'error_rate_limit.html': '''
<!DOCTYPE html>
<html>
<head>
    <title>Terminvergabe - Fehler</title>
</head>
<body>
    <h1>Terminvergabe</h1>
    <div class="error-container">
        <div class="alert error">
            <h3>Fehler</h3>
            <p>zu vieler Terminanfragen</p>
            <p>Bitte warten Sie einige Minuten und versuchen Sie es erneut.</p>
        </div>
    </div>
</body>
</html>
            '''
        }
        
        # 创建示例文件
        for filename, content in sample_files.items():
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            logging.info(f"创建示例文件: {filepath}")
        
        return sample_files.keys()
    
    def analyze_html_file(self, filepath, step_name="unknown"):
        """分析单个HTML文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            analysis = {
                'filepath': filepath,
                'file_size': len(content),
                'title': '',
                'headers': [],
                'step_indicators': [],
                'forms': [],
                'error_messages': [],
                'success_messages': [],
                'appointment_elements': [],
                'key_selectors': []
            }
            
            # 提取标题
            title = soup.find('title')
            if title:
                analysis['title'] = title.get_text().strip()
            
            # 提取所有标题元素
            for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                analysis['headers'].append({
                    'tag': header.name,
                    'text': header.get_text().strip(),
                    'class': header.get('class', [])
                })
            
            # 查找步骤指示器
            for text in soup.find_all(string=True):
                if text and 'Schritt' in text.strip():
                    analysis['step_indicators'].append(text.strip())
            
            # 分析表单
            for form in soup.find_all('form'):
                form_analysis = {
                    'action': form.get('action', ''),
                    'method': form.get('method', 'GET'),
                    'class': form.get('class', []),
                    'inputs': []
                }
                
                for input_elem in form.find_all('input'):
                    form_analysis['inputs'].append({
                        'type': input_elem.get('type', 'text'),
                        'name': input_elem.get('name', ''),
                        'value': input_elem.get('value', ''),
                        'class': input_elem.get('class', [])
                    })
                
                analysis['forms'].append(form_analysis)
            
            # 查找错误消息
            error_keywords = [
                'kein freier termin verfügbar', 'kein termin', 'nicht verfügbar',
                'zu vieler terminanfragen', 'fehler', 'error'
            ]
            
            for text in soup.find_all(string=True):
                if text and text.strip():
                    text_lower = text.strip().lower()
                    for keyword in error_keywords:
                        if keyword in text_lower:
                            analysis['error_messages'].append(text.strip())
                            break
            
            # 查找成功消息
            success_keywords = [
                'erfolgreich', 'bestätigung', 'gebucht', 'success', 'schritt 6'
            ]
            
            for text in soup.find_all(string=True):
                if text and text.strip():
                    text_lower = text.strip().lower()
                    for keyword in success_keywords:
                        if keyword in text_lower:
                            analysis['success_messages'].append(text.strip())
                            break
            
            # 查找预约相关元素
            appointment_selectors = [
                'details[id*="suggest"]', 'div[id*="suggest"]', 'div[id*="accordion"]',
                '.suggestion_form', '.time-slots', '.appointment'
            ]
            
            for selector in appointment_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    analysis['appointment_elements'].append({
                        'selector': selector,
                        'tag': elem.name,
                        'id': elem.get('id', ''),
                        'class': elem.get('class', []),
                        'text_preview': elem.get_text()[:100] + '...' if len(elem.get_text()) > 100 else elem.get_text()
                    })
            
            # 识别关键CSS选择器
            key_elements = [
                '.error', '.alert', '.warning', '.success', '.notification',
                '.message', '.step', '.progress', '[class*="termin"]',
                '[class*="appointment"]', '[id*="suggest"]'
            ]
            
            for selector in key_elements:
                elements = soup.select(selector)
                if elements:
                    analysis['key_selectors'].append({
                        'selector': selector,
                        'count': len(elements),
                        'sample_text': elements[0].get_text().strip()[:50] if elements[0].get_text().strip() else ''
                    })
            
            return analysis
            
        except Exception as e:
            logging.error(f"分析文件 {filepath} 时出错: {e}")
            return {'error': str(e), 'filepath': filepath}
    
    def analyze_all_files(self):
        """分析所有HTML文件"""
        # 创建示例文件
        sample_files = self.create_sample_html_files()
        
        # 分析示例文件
        for filename in sample_files:
            filepath = os.path.join(self.output_dir, filename)
            step_name = filename.replace('.html', '')
            analysis = self.analyze_html_file(filepath, step_name)
            self.analysis_results[step_name] = analysis
            logging.info(f"已分析文件: {filename}")
        
        # 分析现有的保存文件
        existing_files = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    existing_files.append(filepath)
        
        for filepath in existing_files:
            if 'analysis' not in filepath:  # 跳过分析目录中的文件
                filename = os.path.basename(filepath)
                analysis = self.analyze_html_file(filepath, filename)
                self.analysis_results[f"existing_{filename}"] = analysis
                logging.info(f"已分析现有文件: {filepath}")
    
    def generate_dom_parsing_recommendations(self):
        """基于分析结果生成DOM解析建议"""
        self.recommendations = []
        
        # 1. 步骤检测建议
        step_patterns = set()
        for key, analysis in self.analysis_results.items():
            if 'step_indicators' in analysis:
                step_patterns.update(analysis['step_indicators'])
        
        if step_patterns:
            self.recommendations.append({
                'category': '步骤检测改进',
                'description': '检测页面当前所在的步骤',
                'current_approach': '简单字符串搜索: "Schritt 6" in res.text',
                'improved_approach': '''
def check_step_completion(html_content, step_number):
    \"\"\"
    使用DOM解析检查是否到达了指定的步骤
    \"\"\"
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        step_text = f"Schritt {step_number}"
        
        # 方法1: 查找标题元素中的步骤信息
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for header in headers:
            if step_text in header.get_text():
                return True
                
        # 方法2: 查找进度指示器
        progress_elements = soup.select('.step, .progress, [class*="step"]')
        for element in progress_elements:
            if step_text in element.get_text():
                return True
                
        # 方法3: 查找包含步骤文本的任何元素
        step_element = soup.find(string=lambda text: 
            text and step_text in text.strip() if text else False)
        return bool(step_element)
        
    except Exception:
        # 后备方案
        return step_text in html_content
                ''',
                'detected_patterns': list(step_patterns),
                'benefits': [
                    '更准确的步骤检测',
                    '对HTML结构变化的抗干扰性',
                    '支持多种步骤指示器格式'
                ]
            })
        
        # 2. 预约可用性检测建议
        error_patterns = set()
        for key, analysis in self.analysis_results.items():
            if 'error_messages' in analysis:
                error_patterns.update(analysis['error_messages'])
        
        appointment_selectors = set()
        for key, analysis in self.analysis_results.items():
            if 'appointment_elements' in analysis:
                for elem in analysis['appointment_elements']:
                    appointment_selectors.add(elem['selector'])
        
        self.recommendations.append({
            'category': '预约可用性检测改进',
            'description': '检测是否有可用的预约时间',
            'current_approach': '简单字符串搜索: "Kein freier Termin verfügbar" in res.text',
            'improved_approach': '''
def check_no_appointments_available(html_content):
    \"\"\"
    使用DOM解析检查是否没有可用预约时间
    \"\"\"
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 方法1: 查找错误消息元素
        error_selectors = ['.error', '.alert', '.warning', '.message']
        error_texts = ['Kein freier Termin verfügbar', 'keine Termine']
        
        for selector in error_selectors:
            elements = soup.select(selector)
            for element in elements:
                element_text = element.get_text()
                if any(error_text in element_text for error_text in error_texts):
                    return True
        
        # 方法2: 检查预约时间容器是否存在
        appointment_containers = [
            soup.find("details", {"id": "details_suggest_times"}),
            soup.find("div", {"id": "sugg_accordion"})
        ]
        
        for container in appointment_containers:
            if container:
                # 检查容器中是否有预约表单
                forms = container.find_all("form", {"class": "suggestion_form"})
                if forms:
                    return False  # 有表单说明有可用时间
        
        # 方法3: 文本搜索作为后备
        return any(error_text in html_content for error_text in error_texts)
        
    except Exception:
        return 'Kein freier Termin verfügbar' in html_content
            ''',
            'detected_patterns': list(error_patterns),
            'detected_selectors': list(appointment_selectors),
            'benefits': [
                '精确定位错误消息',
                '区分不同类型的通知',
                '更可靠的预约状态检测'
            ]
        })
        
        # 3. 错误处理改进建议
        key_selectors = set()
        for key, analysis in self.analysis_results.items():
            if 'key_selectors' in analysis:
                for selector_info in analysis['key_selectors']:
                    key_selectors.add(selector_info['selector'])
        
        self.recommendations.append({
            'category': '错误处理改进',
            'description': '检测各种错误状态（如请求频率限制）',
            'current_approach': '简单字符串搜索特定错误消息',
            'improved_approach': '''
def check_rate_limit_error(html_content):
    \"\"\"
    检查是否出现了请求过多的错误
    \"\"\"
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        rate_limit_text = "zu vieler Terminanfragen"
        
        # 方法1: 查找错误消息容器
        error_selectors = ['.error', '.alert', '.warning', '[class*="error"]']
        for selector in error_selectors:
            elements = soup.select(selector)
            for element in elements:
                if rate_limit_text in element.get_text():
                    return True
        
        # 方法2: 通用文本搜索
        rate_element = soup.find(string=lambda text: 
            text and rate_limit_text in text.strip() if text else False)
        return bool(rate_element)
        
    except Exception:
        return rate_limit_text in html_content
            ''',
            'detected_selectors': list(key_selectors),
            'benefits': [
                '准确识别不同类型的错误',
                '更好的错误分类',
                '增强的错误恢复机制'
            ]
        })
        
        # 4. 表单处理改进建议
        form_patterns = {}
        for key, analysis in self.analysis_results.items():
            if 'forms' in analysis and analysis['forms']:
                form_patterns[key] = analysis['forms']
        
        if form_patterns:
            self.recommendations.append({
                'category': '表单处理改进',
                'description': '更好地处理表单提交和验证',
                'current_approach': '基本的表单字段填写',
                'improved_approach': '''
def extract_form_data(soup, form_selector="form"):
    \"\"\"
    智能提取表单数据
    \"\"\"
    form = soup.select_one(form_selector)
    if not form:
        return None
    
    form_data = {}
    
    # 提取隐藏字段
    for hidden in form.find_all('input', {'type': 'hidden'}):
        name = hidden.get('name')
        value = hidden.get('value')
        if name:
            form_data[name] = value
    
    # 提取其他输入字段
    for input_elem in form.find_all('input'):
        if input_elem.get('type') != 'hidden':
            name = input_elem.get('name')
            if name:
                form_data[name] = ''  # 待填写
    
    return {
        'action': form.get('action', ''),
        'method': form.get('method', 'POST'),
        'data': form_data
    }
                ''',
                'detected_patterns': form_patterns,
                'benefits': [
                    '自动化表单字段检测',
                    '更好的表单验证',
                    '减少硬编码字段名称'
                ]
            })
    
    def print_analysis_summary(self):
        """打印分析摘要"""
        print("\n" + "="*60)
        print("HTML结构分析摘要")
        print("="*60)
        
        print(f"\n总共分析了 {len(self.analysis_results)} 个HTML文件:")
        
        for key, analysis in self.analysis_results.items():
            if 'error' in analysis:
                print(f"  ❌ {key}: 分析失败 - {analysis['error']}")
            else:
                print(f"  ✅ {key}:")
                print(f"     标题: {analysis.get('title', 'N/A')}")
                print(f"     步骤指示器: {len(analysis.get('step_indicators', []))}")
                print(f"     表单数量: {len(analysis.get('forms', []))}")
                print(f"     错误消息: {len(analysis.get('error_messages', []))}")
                print(f"     成功消息: {len(analysis.get('success_messages', []))}")
                print(f"     预约元素: {len(analysis.get('appointment_elements', []))}")
        
        print(f"\n生成了 {len(self.recommendations)} 条DOM解析改进建议")
    
    def print_recommendations(self):
        """打印DOM解析建议"""
        print("\n" + "="*60)
        print("DOM解析改进建议")
        print("="*60)
        
        for i, rec in enumerate(self.recommendations, 1):
            print(f"\n{i}. {rec['category']}")
            print(f"   描述: {rec['description']}")
            print(f"   当前方法: {rec['current_approach']}")
            print(f"   改进方法: [见代码示例]")
            
            if 'detected_patterns' in rec and rec['detected_patterns']:
                patterns = list(rec['detected_patterns'])[:3] if len(rec['detected_patterns']) > 3 else list(rec['detected_patterns'])
                print(f"   检测到的模式: {patterns}...")  
            
            if 'detected_selectors' in rec and rec['detected_selectors']:
                selectors = list(rec['detected_selectors'])
                print(f"   检测到的选择器: {selectors}")
            
            if 'benefits' in rec:
                print(f"   优势:")
                for benefit in rec['benefits']:
                    print(f"     • {benefit}")
    
    def save_results(self):
        """保存分析结果"""
        # 保存完整分析结果
        results_file = os.path.join(self.output_dir, 'html_analysis_results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_files_analyzed': len(self.analysis_results),
                'analysis_results': self.analysis_results,
                'recommendations': self.recommendations
            }, f, ensure_ascii=False, indent=2)
        
        # 保存DOM解析代码建议
        code_file = os.path.join(self.output_dir, 'improved_dom_utils.py')
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write('# -*- coding: utf-8 -*-\n\n')
            f.write('"""\n')
            f.write('改进的DOM解析工具\n')
            f.write('基于HTML结构分析生成的建议代码\n')
            f.write('"""\n\n')
            f.write('import bs4\n')
            f.write('import logging\n\n')
            
            for rec in self.recommendations:
                f.write(f"# {rec['category']}\n")
                f.write(f"# {rec['description']}\n")
                f.write(rec['improved_approach'])
                f.write('\n\n')
        
        logging.info(f"分析结果已保存到: {results_file}")
        logging.info(f"改进代码已保存到: {code_file}")
        
        return results_file, code_file
    
    def run_complete_analysis(self):
        """运行完整分析"""
        logging.info("开始HTML结构分析")
        
        # 分析所有文件
        self.analyze_all_files()
        
        # 生成建议
        self.generate_dom_parsing_recommendations()
        
        # 打印结果
        self.print_analysis_summary()
        self.print_recommendations()
        
        # 保存结果
        results_file, code_file = self.save_results()
        
        print(f"\n✅ 分析完成！")
        print(f"   分析结果: {results_file}")
        print(f"   改进代码: {code_file}")
        
        return {
            'analysis_results': self.analysis_results,
            'recommendations': self.recommendations,
            'files_saved': [results_file, code_file]
        }


def main():
    """主函数"""
    print("HTML结构分析工具")
    print("="*60)
    print("此工具将分析HTML页面结构并提供DOM解析改进建议")
    
    analyzer = HTMLStructureAnalyzer()
    result = analyzer.run_complete_analysis()
    
    return result


if __name__ == "__main__":
    main()