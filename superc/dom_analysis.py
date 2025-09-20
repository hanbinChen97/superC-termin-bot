#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Structured HTML Parsing Workflow

This module implements a 4-stage pipeline:
1. HTML Download - Download raw HTML content
2. HTML → JSON Conversion - Parse HTML to structured JSON with unique IDs  
3. AI Analysis - Analyze JSON structure to identify elements of interest
4. Element Extraction - Extract specific content based on AI analysis

Author: Generated for Issue #15
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
import lxml

# Import configuration safely
try:
    from .config import USER_AGENT
except ImportError:
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

# Note: Azure OpenAI integration available in llmCall.py when needed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def download_html(url: str, save_path: str) -> bool:
    """
    Stage 1: Download HTML content using httpx and save to file
    
    Args:
        url: Target URL to download
        save_path: Path where to save the HTML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Downloading HTML from: {url}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Download HTML with proper headers
        headers = {
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        with httpx.Client(headers=headers, timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            
            # Save to file with UTF-8 encoding
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
        logger.info(f"HTML saved successfully to: {save_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download HTML: {e}")
        return False


def html_to_json(html_path: str, json_save_path: str) -> bool:
    """
    Stage 2: Convert HTML to structured JSON with unique IDs
    
    Args:
        html_path: Path to HTML file
        json_save_path: Path where to save the JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Converting HTML to JSON: {html_path} -> {json_save_path}")
        
        # Read HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Parse with BeautifulSoup using lxml
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Counter for unique IDs
        id_counter = {'count': 0}
        
        def safe_parse_element(element, parent_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
            """Safely parse HTML elements into structured data"""
            try:
                # Increment ID counter
                current_id = id_counter['count'] + 1
                id_counter['count'] = current_id
                
                # Determine element type
                is_tag = hasattr(element, 'name') and element.name is not None
                
                if is_tag:
                    # It's a tag element
                    tag_name = element.name
                    
                    # Extract text safely
                    text_content = ""
                    try:
                        if hasattr(element, 'get_text') and callable(element.get_text):
                            text_content = element.get_text(strip=True)
                        else:
                            text_content = ''.join(element.strings).strip()
                    except Exception:
                        try:
                            text_content = str(element).strip()
                        except Exception:
                            text_content = ""
                    
                    # Extract attributes safely
                    attrs = {}
                    try:
                        if hasattr(element, 'attrs') and element.attrs:
                            attrs = dict(element.attrs)
                    except Exception:
                        attrs = {}
                    
                    # Create element data
                    elem_data = {
                        'id': current_id,
                        'tag': tag_name,
                        'attrs': attrs,
                        'text': text_content,
                        'parent_id': parent_id,
                        'children': []
                    }
                    
                    # Process children safely
                    if hasattr(element, 'children'):
                        try:
                            children_list = list(element.children)  # Convert generator to list first
                            for child in children_list:
                                # Skip pure whitespace text nodes
                                if hasattr(child, 'strip') and not child.strip():
                                    continue
                                child_data = safe_parse_element(child, current_id)
                                if child_data:
                                    elem_data['children'].append(child_data)
                        except Exception as e:
                            logger.warning(f"Error processing children of {tag_name}: {e}")
                    
                    return elem_data
                
                else:
                    # It's a text node
                    text_content = str(element).strip()
                    if not text_content:
                        return None
                        
                    return {
                        'id': current_id,
                        'tag': 'text',
                        'attrs': {},
                        'text': text_content,
                        'parent_id': parent_id,
                        'children': []
                    }
                    
            except Exception as e:
                logger.warning(f"Error parsing element: {e}")
                return None
        
        # Parse root elements
        structured_data = []
        for element in soup.children:
            if hasattr(element, 'name') and element.name:
                elem_data = safe_parse_element(element)
                if elem_data:
                    structured_data.append(elem_data)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(json_save_path), exist_ok=True)
        
        # Save to JSON
        with open(json_save_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"JSON structure saved successfully to: {json_save_path}")
        logger.info(f"Total elements parsed: {id_counter['count']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert HTML to JSON: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def analyze_structure(json_path: str, output_path: str, query: str = None) -> bool:
    """
    Stage 3: Analyze JSON structure using AI to identify elements of interest
    
    Args:
        json_path: Path to structured JSON file
        output_path: Path where to save analysis results
        query: Optional specific query for AI analysis
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Analyzing structure: {json_path} -> {output_path}")
        
        # Read JSON structure
        with open(json_path, 'r', encoding='utf-8') as f:
            structure_data = json.load(f)
            
        # Default query if none provided
        if not query:
            query = """
            请分析这个HTML结构，找到以下类型的元素：
            1. 表单相关元素 (form, input, button, select)
            2. 导航和链接元素 (nav, a, button)
            3. 内容展示元素 (h1, h2, h3, div, span)
            4. 验证码相关元素 (img, captcha相关的input)
            
            请返回这些元素的ID、标签类型、文本内容和重要属性。
            """
        
        # Prepare data for AI analysis
        analysis_prompt = f"""
        分析以下HTML结构数据：
        
        查询要求：{query}
        
        HTML结构数据：
        {json.dumps(structure_data, ensure_ascii=False, indent=2)[:5000]}...
        
        请以JSON格式返回分析结果，包含：
        - elements: 找到的元素列表
        - each element should have: id, tag, text, attrs, reason (为什么选择这个元素)
        """
        
        # Note: Using placeholder for AI call - in real implementation, 
        # this would call the existing Azure OpenAI integration
        logger.warning("AI analysis not implemented - returning mock results")
        
        # Mock analysis result for now
        analysis_result = {
            "query": query,
            "total_elements": len(structure_data),
            "analysis_timestamp": "2024-01-01T00:00:00Z",
            "elements": [
                {
                    "id": 1,
                    "tag": "form",
                    "text": "",
                    "attrs": {"method": "post", "action": "/submit"},
                    "reason": "Main form element for user input"
                }
            ]
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save analysis results
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Analysis results saved to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to analyze structure: {e}")
        return False


def extract_by_id(html_path: str, analysis_path: str, output_path: str) -> bool:
    """
    Stage 4: Extract specific content from HTML based on AI analysis results
    
    Args:
        html_path: Path to original HTML file
        analysis_path: Path to AI analysis results
        output_path: Path where to save extracted content
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Extracting content based on analysis: {html_path} + {analysis_path} -> {output_path}")
        
        # Read HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Read analysis results
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
            
        # Parse HTML again to create ID mapping using the same robust approach
        soup = BeautifulSoup(html_content, 'lxml')
        id_to_element = {}
        id_counter = {'count': 0}
        
        def map_elements(element):
            """Recreate the ID mapping from Stage 2 using the same logic"""
            try:
                current_id = id_counter['count'] + 1
                id_counter['count'] = current_id
                id_to_element[current_id] = element
                
                if hasattr(element, 'children'):
                    try:
                        children_list = list(element.children)  # Convert generator to list first
                        for child in children_list:
                            if hasattr(child, 'strip') and not child.strip():
                                continue
                            map_elements(child)
                    except Exception as e:
                        logger.warning(f"Error mapping children: {e}")
            except Exception as e:
                logger.warning(f"Error mapping element: {e}")
        
        # Map all elements using the same approach as Stage 2
        for element in soup.children:
            if hasattr(element, 'name') and element.name:
                map_elements(element)
        
        # Extract content for each element identified by AI
        extracted_content = {
            "extraction_timestamp": "2024-01-01T00:00:00Z",
            "source_html": html_path,
            "analysis_source": analysis_path,
            "total_mapped_elements": len(id_to_element),
            "extracted_elements": []
        }
        
        for element_info in analysis_data.get('elements', []):
            element_id = element_info['id']
            if element_id in id_to_element:
                html_element = id_to_element[element_id]
                
                # Extract element safely
                try:
                    text_content = ""
                    if hasattr(html_element, 'get_text'):
                        try:
                            text_content = html_element.get_text(strip=True)
                        except:
                            text_content = str(html_element).strip()
                    
                    attrs = {}
                    if hasattr(html_element, 'attrs') and html_element.attrs:
                        attrs = dict(html_element.attrs)
                    
                    extracted_element = {
                        "id": element_id,
                        "tag": element_info['tag'],
                        "reason": element_info.get('reason', ''),
                        "html_snippet": str(html_element)[:500] + "..." if len(str(html_element)) > 500 else str(html_element),
                        "text_content": text_content,
                        "attributes": attrs
                    }
                    
                    extracted_content["extracted_elements"].append(extracted_element)
                    logger.info(f"Extracted element ID {element_id}: {element_info['tag']}")
                    
                except Exception as e:
                    logger.warning(f"Error extracting element ID {element_id}: {e}")
            else:
                logger.warning(f"Element ID {element_id} not found in mapping")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save extracted content
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(extracted_content, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Extracted content saved to: {output_path}")
        logger.info(f"Total elements mapped: {len(id_to_element)}, extracted: {len(extracted_content['extracted_elements'])}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to extract content: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def run_full_pipeline(url: str, base_dir: str = "superc", query: str = None) -> Dict[str, str]:
    """
    Run the complete 4-stage pipeline
    
    Args:
        url: URL to analyze
        base_dir: Base directory for saving files
        query: Optional query for AI analysis
        
    Returns:
        Dict containing paths to all generated files
    """
    logger.info(f"Starting full pipeline for URL: {url}")
    
    # Define file paths
    html_path = f"{base_dir}/html_pages/raw_page.html"
    json_path = f"{base_dir}/parsed_json/page_structure.json"
    analysis_path = f"{base_dir}/parsed_json/analysis_result.json"
    extraction_path = f"{base_dir}/parsed_json/extracted_content.json"
    
    results = {
        "html_path": html_path,
        "json_path": json_path,
        "analysis_path": analysis_path,
        "extraction_path": extraction_path,
        "success": False
    }
    
    try:
        # Stage 1: Download HTML
        if not download_html(url, html_path):
            return results
            
        # Stage 2: Convert to JSON
        if not html_to_json(html_path, json_path):
            return results
            
        # Stage 3: AI Analysis
        if not analyze_structure(json_path, analysis_path, query):
            return results
            
        # Stage 4: Extract content
        if not extract_by_id(html_path, analysis_path, extraction_path):
            return results
            
        results["success"] = True
        logger.info("Full pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        
    return results


if __name__ == "__main__":
    # Example usage
    test_url = "https://httpbin.org/html"  # Simple test page
    results = run_full_pipeline(test_url)
    
    if results["success"]:
        print("Pipeline completed successfully!")
        print(f"Files generated:")
        for key, path in results.items():
            if key != "success":
                print(f"  {key}: {path}")
    else:
        print("Pipeline failed. Check logs for details.")