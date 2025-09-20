#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for DOM Analysis functionality

Tests for the structured HTML parsing pipeline.
"""

import os
import json
import tempfile
import unittest
from pathlib import Path

# Import our DOM analysis module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from superc.dom_analysis import (
    download_html, 
    html_to_json, 
    analyze_structure, 
    extract_by_id,
    run_full_pipeline
)


class TestDOMAnalysis(unittest.TestCase):
    """Test cases for DOM analysis functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1 class="title">Test Title</h1>
            <form id="test-form" method="post">
                <input type="text" name="name" placeholder="Name" required>
                <input type="email" name="email" placeholder="Email">
                <button type="submit">Submit</button>
            </form>
            <div class="content">
                <p>Some test content</p>
            </div>
        </body>
        </html>
        """
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_html_to_json_conversion(self):
        """Test HTML to JSON conversion functionality"""
        # Create test HTML file
        html_path = os.path.join(self.test_dir, "test.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self.test_html)
        
        # Convert to JSON
        json_path = os.path.join(self.test_dir, "test.json")
        result = html_to_json(html_path, json_path)
        
        # Verify result
        self.assertTrue(result)
        self.assertTrue(os.path.exists(json_path))
        
        # Load and verify JSON structure
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Should have at least one element (html tag)
        self.assertGreater(len(data), 0)
        
        # Check structure of first element
        first_element = data[0]
        self.assertIn('id', first_element)
        self.assertIn('tag', first_element)
        self.assertIn('attrs', first_element)
        self.assertIn('text', first_element)
        self.assertIn('children', first_element)
        
        print(f"✓ HTML to JSON conversion test passed")
        print(f"  Generated {len(data)} root elements")
    
    def test_analyze_structure(self):
        """Test structure analysis functionality"""
        # Create test JSON structure
        test_structure = [
            {
                "id": 1,
                "tag": "form",
                "attrs": {"id": "test-form", "method": "post"},
                "text": "",
                "children": [
                    {
                        "id": 2,
                        "tag": "input",
                        "attrs": {"type": "text", "name": "name", "required": True},
                        "text": "",
                        "children": []
                    }
                ]
            }
        ]
        
        json_path = os.path.join(self.test_dir, "structure.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(test_structure, f)
        
        # Analyze structure
        analysis_path = os.path.join(self.test_dir, "analysis.json")
        result = analyze_structure(json_path, analysis_path, "Find form elements")
        
        # Verify result
        self.assertTrue(result)
        self.assertTrue(os.path.exists(analysis_path))
        
        # Load and verify analysis
        with open(analysis_path, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        
        self.assertIn('elements', analysis)
        self.assertIn('query', analysis)
        
        print(f"✓ Structure analysis test passed")
    
    def test_extract_by_id(self):
        """Test element extraction functionality"""
        # Create test HTML file
        html_path = os.path.join(self.test_dir, "test.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self.test_html)
        
        # Create mock analysis result
        analysis_data = {
            "elements": [
                {
                    "id": 2,  # Assuming this is a form element
                    "tag": "form",
                    "text": "",
                    "attrs": {"id": "test-form"},
                    "reason": "Main form element"
                }
            ]
        }
        
        analysis_path = os.path.join(self.test_dir, "analysis.json")
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f)
        
        # Extract content
        extraction_path = os.path.join(self.test_dir, "extracted.json")
        result = extract_by_id(html_path, analysis_path, extraction_path)
        
        # Verify result
        self.assertTrue(result)
        self.assertTrue(os.path.exists(extraction_path))
        
        # Load and verify extraction
        with open(extraction_path, 'r', encoding='utf-8') as f:
            extracted = json.load(f)
        
        self.assertIn('extracted_elements', extracted)
        
        print(f"✓ Element extraction test passed")
    
    def test_full_pipeline_with_mock_data(self):
        """Test complete pipeline with mock HTML data"""
        # Create test HTML file directly (skip download for test)
        html_path = os.path.join(self.test_dir, "raw_page.html")
        os.makedirs(os.path.dirname(html_path), exist_ok=True)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self.test_html)
        
        # Test stages 2-4 with existing HTML
        json_path = os.path.join(self.test_dir, "page_structure.json")
        analysis_path = os.path.join(self.test_dir, "analysis_result.json")
        extraction_path = os.path.join(self.test_dir, "extracted_content.json")
        
        # Stage 2: HTML to JSON
        result_json = html_to_json(html_path, json_path)
        self.assertTrue(result_json)
        
        # Stage 3: Analysis
        result_analysis = analyze_structure(json_path, analysis_path)
        self.assertTrue(result_analysis)
        
        # Stage 4: Extraction
        result_extraction = extract_by_id(html_path, analysis_path, extraction_path)
        self.assertTrue(result_extraction)
        
        print(f"✓ Full pipeline test passed")
        print(f"  Files created: {json_path}, {analysis_path}, {extraction_path}")


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)