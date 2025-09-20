#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test to demonstrate the working DOM analysis pipeline

This script shows how to use the structured HTML parsing system.
"""

import os
import json
import tempfile
from pathlib import Path

# Import our DOM analysis module directly to avoid package import issues
import sys
import os

# Add the superc directory to path
superc_path = os.path.join(os.path.dirname(__file__), '..', 'superc')
sys.path.insert(0, superc_path)

# Import directly from file to avoid package __init__.py issues
import importlib.util
spec = importlib.util.spec_from_file_location("dom_analysis", os.path.join(superc_path, "dom_analysis.py"))
dom_analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dom_analysis)

# Use functions from the module
run_full_pipeline = dom_analysis.run_full_pipeline
html_to_json = dom_analysis.html_to_json
analyze_structure = dom_analysis.analyze_structure
extract_by_id = dom_analysis.extract_by_id


def test_with_appointment_form():
    """Test the pipeline with a realistic appointment form"""
    
    # Sample HTML that mimics the Aachen appointment form
    appointment_html = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Terminvereinbarung - Ausländeramt Aachen</title>
</head>
<body>
    <div class="header">
        <h1>Terminvereinbarung</h1>
        <p>Bitte füllen Sie alle Felder aus</p>
    </div>
    
    <form id="appointment-form" method="post" action="/submit">
        <fieldset>
            <legend>Persönliche Daten</legend>
            
            <div class="form-group">
                <label for="vorname">Vorname <span class="required">*</span></label>
                <input type="text" id="vorname" name="vorname" required>
            </div>
            
            <div class="form-group">
                <label for="nachname">Nachname <span class="required">*</span></label>
                <input type="text" id="nachname" name="nachname" required>
            </div>
            
            <div class="form-group">
                <label for="email">E-Mail <span class="required">*</span></label>
                <input type="email" id="email" name="email" required>
            </div>
            
            <div class="form-group">
                <label for="phone">Telefon</label>
                <input type="tel" id="phone" name="phone">
            </div>
            
            <div class="form-group">
                <label>Geburtsdatum <span class="required">*</span></label>
                <select name="geburtsdatumDay" required>
                    <option value="">Tag</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                </select>
                <select name="geburtsdatumMonth" required>
                    <option value="">Monat</option>
                    <option value="1">Januar</option>
                    <option value="2">Februar</option>
                </select>
                <select name="geburtsdatumYear" required>
                    <option value="">Jahr</option>
                    <option value="1990">1990</option>
                    <option value="1991">1991</option>
                </select>
            </div>
        </fieldset>
        
        <fieldset>
            <legend>Sicherheit</legend>
            <div class="captcha-section">
                <label for="captcha_code">Sicherheitscode <span class="required">*</span></label>
                <img src="/captcha.png" alt="Captcha" id="captcha-image" width="120" height="40">
                <input type="text" id="captcha_code" name="captcha_code" placeholder="Code eingeben" required>
            </div>
        </fieldset>
        
        <div class="form-actions">
            <button type="submit" class="btn-primary">Termin reservieren</button>
            <button type="reset" class="btn-secondary">Zurücksetzen</button>
        </div>
        
        <!-- Honeypot field for spam protection -->
        <input type="text" name="hunangskrukka" style="display:none">
    </form>
    
    <div class="footer">
        <p>Kontakt: info@aachen.de | Tel: +49 241 432-0</p>
    </div>
</body>
</html>"""

    print("🧪 Testing DOM Analysis Pipeline with Appointment Form")
    print("=" * 60)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        base_dir = os.path.join(temp_dir, "superc")
        os.makedirs(f"{base_dir}/html_pages", exist_ok=True)
        os.makedirs(f"{base_dir}/parsed_json", exist_ok=True)
        
        # Save test HTML
        html_path = f"{base_dir}/html_pages/appointment_form.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(appointment_html)
        
        print(f"✅ Test HTML saved to: {html_path}")
        
        # Test Stage 2: HTML to JSON
        print("\n📄 Stage 2: Converting HTML to JSON...")
        json_path = f"{base_dir}/parsed_json/page_structure.json"
        
        success = html_to_json(html_path, json_path)
        if success and os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                structure_data = json.load(f)
            
            print(f"✅ JSON conversion successful!")
            print(f"   📊 Root elements: {len(structure_data)}")
            
            # Count elements by type
            def count_by_tag(data):
                counts = {}
                def traverse(elem):
                    tag = elem.get('tag', 'unknown')
                    counts[tag] = counts.get(tag, 0) + 1
                    for child in elem.get('children', []):
                        traverse(child)
                
                for elem in data:
                    traverse(elem)
                return counts
            
            tag_counts = count_by_tag(structure_data)
            important_tags = ['form', 'input', 'button', 'select', 'option', 'img', 'label']
            
            print("   🏷️  Important elements found:")
            for tag in important_tags:
                if tag in tag_counts:
                    print(f"      {tag}: {tag_counts[tag]}")
            
            # Test Stage 3: Analysis
            print("\n🤖 Stage 3: AI Structure Analysis...")
            analysis_path = f"{base_dir}/parsed_json/analysis_result.json"
            
            query = """
            Analyze this appointment form structure and identify:
            1. All input fields (name, type, required status)
            2. Form submission buttons
            3. CAPTCHA image and related input
            4. Select dropdowns for date selection
            5. Hidden fields (like honeypot)
            
            Focus on elements critical for automated form filling.
            """
            
            success = analyze_structure(json_path, analysis_path, query)
            if success:
                print("✅ Analysis completed (mock implementation)")
                
                # Test Stage 4: Extraction  
                print("\n🎯 Stage 4: Element Extraction...")
                extraction_path = f"{base_dir}/parsed_json/extracted_content.json"
                
                success = extract_by_id(html_path, analysis_path, extraction_path)
                if success:
                    print("✅ Extraction completed!")
                    
                    # Show results
                    with open(extraction_path, 'r', encoding='utf-8') as f:
                        extracted = json.load(f)
                    
                    print(f"\n📋 Pipeline Results Summary:")
                    print(f"   🗂️  Total elements mapped: {extracted.get('total_mapped_elements', 0)}")
                    print(f"   🎯 Elements extracted: {len(extracted.get('extracted_elements', []))}")
                    
                    return True
                else:
                    print("❌ Extraction failed")
            else:
                print("❌ Analysis failed")
        else:
            print("❌ JSON conversion failed")
    
    return False


def test_simple_html():
    """Test with very simple HTML to debug issues"""
    print("\n🔧 Testing with Simple HTML...")
    
    simple_html = """<html>
<body>
<h1>Test</h1>
<form>
<input type="text" name="test">
<button>Submit</button>
</form>
</body>
</html>"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        html_path = os.path.join(temp_dir, "simple.html")
        json_path = os.path.join(temp_dir, "simple.json")
        
        with open(html_path, 'w') as f:
            f.write(simple_html)
        
        success = html_to_json(html_path, json_path)
        if success and os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            print(f"✅ Simple test passed: {len(data)} elements")
            
            # Show structure
            def show_structure(elem, indent=0):
                spaces = "  " * indent
                tag = elem.get('tag', 'unknown')
                attrs = elem.get('attrs', {})
                text = elem.get('text', '')[:20]
                print(f"{spaces}<{tag}> \"{text}\" {attrs}")
                for child in elem.get('children', [])[:3]:
                    show_structure(child, indent + 1)
            
            for elem in data:
                show_structure(elem)
                break
                
            return True
        else:
            print("❌ Simple test failed")
            return False


if __name__ == "__main__":
    print("🚀 DOM Analysis Pipeline Test Suite")
    print("=" * 60)
    
    # Test simple case first
    simple_success = test_simple_html()
    
    if simple_success:
        # Test complex appointment form
        complex_success = test_with_appointment_form()
        
        if complex_success:
            print("\n🎉 All tests passed! Pipeline is working correctly.")
            print("\n💡 Next steps:")
            print("   1. Integrate with real Azure OpenAI for Stage 3")
            print("   2. Test with actual Aachen appointment website")
            print("   3. Connect to existing appointment booking system")
        else:
            print("\n⚠️  Complex test failed, but basic functionality works.")
    else:
        print("\n❌ Basic functionality needs debugging.")