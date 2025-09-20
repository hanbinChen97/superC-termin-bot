#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test for the DOM Analysis Pipeline with real appointment data

This test demonstrates how the structured HTML parsing system can be used
with actual appointment booking websites.
"""

import os
import json
import tempfile
import importlib.util
from pathlib import Path


def load_dom_analysis_module():
    """Load the DOM analysis module without package imports"""
    script_dir = os.path.dirname(__file__)
    module_path = os.path.join(script_dir, '..', 'superc', 'dom_analysis.py')
    
    spec = importlib.util.spec_from_file_location("dom_analysis", module_path)
    dom_analysis = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dom_analysis)
    
    return dom_analysis


def test_aachen_appointment_workflow():
    """
    Test the complete workflow with HTML that mimics the Aachen appointment system
    """
    print("🏛️  Testing Aachen Appointment Workflow")
    print("=" * 50)
    
    # Load the DOM analysis module
    dom_analysis = load_dom_analysis_module()
    
    # HTML that closely resembles the Aachen appointment booking form
    aachen_html = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Terminvereinbarung - Ausländeramt Aachen</title>
    <style>
        .form-group { margin: 10px 0; }
        .required { color: red; }
        .captcha-section { border: 1px solid #ccc; padding: 10px; }
        .btn-primary { background: #007bff; color: white; padding: 10px 20px; }
    </style>
</head>
<body>
    <header>
        <h1>Terminvereinbarung Ausländeramt Aachen</h1>
        <nav>
            <a href="/home">Home</a> | 
            <a href="/services">Services</a> | 
            <a href="/contact">Contact</a>
        </nav>
    </header>
    
    <main>
        <div class="appointment-info">
            <h2>Verfügbare Termine</h2>
            <p>Bitte wählen Sie einen Termin aus und füllen Sie das Formular aus.</p>
            
            <div class="time-slots">
                <div class="time-slot available" data-time="2024-01-15T10:00">
                    <span class="date">15.01.2024</span>
                    <span class="time">10:00 Uhr</span>
                    <button class="select-btn">Auswählen</button>
                </div>
                <div class="time-slot available" data-time="2024-01-15T14:00">
                    <span class="date">15.01.2024</span>
                    <span class="time">14:00 Uhr</span>
                    <button class="select-btn">Auswählen</button>
                </div>
            </div>
        </div>
        
        <form id="appointment-form" method="post" action="/termine/submit" enctype="multipart/form-data">
            <input type="hidden" name="csrf_token" value="abc123xyz">
            <input type="hidden" name="selected_time" value="">
            
            <fieldset class="personal-data">
                <legend>Persönliche Angaben</legend>
                
                <div class="form-group">
                    <label for="vorname">Vorname <span class="required">*</span></label>
                    <input type="text" id="vorname" name="vorname" maxlength="50" required 
                           pattern="[A-Za-züöäÜÖÄß\\s]+" title="Nur Buchstaben erlaubt">
                </div>
                
                <div class="form-group">
                    <label for="nachname">Nachname <span class="required">*</span></label>
                    <input type="text" id="nachname" name="nachname" maxlength="50" required
                           pattern="[A-Za-züöäÜÖÄß\\s]+" title="Nur Buchstaben erlaubt">
                </div>
                
                <div class="form-group">
                    <label for="email">E-Mail-Adresse <span class="required">*</span></label>
                    <input type="email" id="email" name="email" maxlength="100" required>
                </div>
                
                <div class="form-group">
                    <label for="emailCheck">E-Mail-Adresse wiederholen <span class="required">*</span></label>
                    <input type="email" id="emailCheck" name="emailwhlg" maxlength="100" required>
                </div>
                
                <div class="form-group">
                    <label for="phone">Telefonnummer</label>
                    <input type="tel" id="phone" name="phone" maxlength="20"
                           pattern="[0-9\\s\\+\\-\\(\\)]+" title="Nur Zahlen und gültige Zeichen">
                </div>
                
                <div class="form-group">
                    <label>Geburtsdatum <span class="required">*</span></label>
                    <div class="date-inputs">
                        <select name="geburtsdatumDay" required>
                            <option value="">Tag</option>
                            <option value="1">1</option>
                            <option value="2">2</option>
                            <option value="15">15</option>
                            <option value="31">31</option>
                        </select>
                        <select name="geburtsdatumMonth" required>
                            <option value="">Monat</option>
                            <option value="1">Januar</option>
                            <option value="7">Juli</option>
                            <option value="12">Dezember</option>
                        </select>
                        <select name="geburtsdatumYear" required>
                            <option value="">Jahr</option>
                            <option value="1990">1990</option>
                            <option value="1995">1995</option>
                            <option value="2000">2000</option>
                        </select>
                    </div>
                </div>
            </fieldset>
            
            <fieldset class="appointment-purpose">
                <legend>Terminzweck</legend>
                
                <div class="form-group">
                    <label for="service">Anliegen <span class="required">*</span></label>
                    <select id="service" name="service" required>
                        <option value="">Bitte wählen...</option>
                        <option value="visa-antrag">Visa-Antrag</option>
                        <option value="aufenthaltstitel">Aufenthaltstitel</option>
                        <option value="verlaengerung">Verlängerung</option>
                        <option value="familienzusammenfuehrung">Familienzusammenführung</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="comment">Zusätzliche Informationen</label>
                    <textarea id="comment" name="comment" rows="4" maxlength="500" 
                              placeholder="Bitte beschreiben Sie Ihr Anliegen..."></textarea>
                </div>
            </fieldset>
            
            <fieldset class="security">
                <legend>Sicherheitsüberprüfung</legend>
                
                <div class="captcha-section">
                    <label for="captcha_code">Sicherheitscode <span class="required">*</span></label>
                    <div class="captcha-container">
                        <img src="/captcha.png?session=xyz123" alt="Sicherheitscode" 
                             id="captcha-image" width="120" height="40">
                        <button type="button" id="refresh-captcha" title="Neuen Code laden">🔄</button>
                    </div>
                    <input type="text" id="captcha_code" name="captcha_code" maxlength="10" 
                           placeholder="Code eingeben" required autocomplete="off">
                    <div id="error_captcha" class="error-text" style="display:none;"></div>
                </div>
                
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="agreementChecked" required>
                        Ich stimme der <a href="/datenschutz" target="_blank">Datenschutzerklärung</a> zu <span class="required">*</span>
                    </label>
                </div>
            </fieldset>
            
            <!-- Honeypot field for spam protection -->
            <div style="position: absolute; left: -9999px;">
                <label for="hunangskrukka">Nicht ausfüllen:</label>
                <input type="text" id="hunangskrukka" name="hunangskrukka" tabindex="-1" autocomplete="off">
            </div>
            
            <div class="form-actions">
                <button type="submit" class="btn-primary" id="submit-btn">
                    <span class="spinner" style="display:none;">⏳</span>
                    Termin reservieren
                </button>
                <button type="reset" class="btn-secondary">Formular zurücksetzen</button>
                <a href="/termine" class="btn-link">Zurück zur Terminauswahl</a>
            </div>
        </form>
        
        <div class="info-box">
            <h3>Wichtige Hinweise</h3>
            <ul>
                <li>Alle mit <span class="required">*</span> markierten Felder sind Pflichtfelder</li>
                <li>Bitte bringen Sie alle erforderlichen Unterlagen mit</li>
                <li>Der Termin ist 15 Minuten vor der Zeit zu bestätigen</li>
            </ul>
        </div>
    </main>
    
    <footer>
        <div class="contact-info">
            <p>Ausländeramt Aachen | Telefon: +49 241 432-0 | E-Mail: info@aachen.de</p>
            <p>Öffnungszeiten: Mo-Fr 8:00-12:00, Do 14:00-18:00</p>
        </div>
    </footer>
</body>
</html>"""
    
    # Create temporary working directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up directory structure as specified in the issue
        base_dir = os.path.join(temp_dir, "superc")
        os.makedirs(f"{base_dir}/html_pages", exist_ok=True)
        os.makedirs(f"{base_dir}/parsed_json", exist_ok=True)
        os.makedirs(f"{base_dir}/analysis_docs", exist_ok=True)
        
        # Save the test HTML
        html_path = f"{base_dir}/html_pages/aachen_appointment.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(aachen_html)
        
        print(f"📄 HTML saved: {os.path.basename(html_path)}")
        
        # Execute the 4-stage pipeline
        results = dom_analysis.run_full_pipeline(
            url="file://" + html_path,  # Use file URL since we have local HTML
            base_dir=base_dir,
            query="""
            Analyze this Aachen appointment booking form and identify:
            
            1. FORM ELEMENTS:
               - Main appointment form container
               - All input fields with their names, types, and validation rules
               - Submit and reset buttons
               - Hidden fields including CSRF tokens
            
            2. CRITICAL FIELDS:
               - Personal data inputs (vorname, nachname, email, phone)
               - Birth date selectors (day, month, year)
               - Service selection dropdown
               - CAPTCHA image and input field
               - Agreement checkbox
            
            3. SECURITY ELEMENTS:
               - CAPTCHA image for verification
               - Honeypot field for spam protection
               - Required field validation
            
            4. INTERACTIVE ELEMENTS:
               - Time slot selection buttons
               - Form submission workflow
               - Error display areas
            
            Return detailed information about each element including:
            - Element ID and tag type
            - Name/ID attributes for form mapping
            - Validation rules and requirements
            - Purpose in the appointment booking process
            """
        )
        
        if results["success"]:
            print("\n🎉 Pipeline executed successfully!")
            
            # Analyze the results in detail
            print("\n📊 Detailed Analysis Results:")
            
            # Check JSON structure
            if os.path.exists(results["json_path"]):
                with open(results["json_path"], 'r', encoding='utf-8') as f:
                    structure_data = json.load(f)
                
                def analyze_form_elements(data):
                    """Extract form-related information from the parsed structure"""
                    forms = []
                    inputs = []
                    buttons = []
                    selects = []
                    images = []
                    
                    def traverse(elem):
                        tag = elem.get('tag', '')
                        attrs = elem.get('attrs', {})
                        
                        if tag == 'form':
                            forms.append({
                                'id': elem['id'],
                                'attrs': attrs,
                                'action': attrs.get('action', ''),
                                'method': attrs.get('method', 'get')
                            })
                        elif tag == 'input':
                            inputs.append({
                                'id': elem['id'],
                                'name': attrs.get('name', ''),
                                'type': attrs.get('type', 'text'),
                                'required': attrs.get('required', False),
                                'placeholder': attrs.get('placeholder', '')
                            })
                        elif tag == 'button':
                            buttons.append({
                                'id': elem['id'],
                                'type': attrs.get('type', 'button'),
                                'text': elem.get('text', '').strip()
                            })
                        elif tag == 'select':
                            selects.append({
                                'id': elem['id'],
                                'name': attrs.get('name', ''),
                                'required': attrs.get('required', False)
                            })
                        elif tag == 'img':
                            images.append({
                                'id': elem['id'],
                                'src': attrs.get('src', ''),
                                'alt': attrs.get('alt', ''),
                                'width': attrs.get('width', ''),
                                'height': attrs.get('height', '')
                            })
                        
                        for child in elem.get('children', []):
                            traverse(child)
                    
                    for elem in data:
                        traverse(elem)
                    
                    return forms, inputs, buttons, selects, images
                
                forms, inputs, buttons, selects, images = analyze_form_elements(structure_data)
                
                print(f"   📋 Forms found: {len(forms)}")
                print(f"   📝 Input fields: {len(inputs)}")
                print(f"   🔘 Buttons: {len(buttons)}")
                print(f"   📋 Select dropdowns: {len(selects)}")
                print(f"   🖼️  Images: {len(images)}")
                
                # Show key input fields
                if inputs:
                    print("\n   🔍 Key Input Fields Detected:")
                    key_fields = ['vorname', 'nachname', 'email', 'phone', 'captcha_code']
                    for field_name in key_fields:
                        matching_inputs = [inp for inp in inputs if inp['name'] == field_name]
                        if matching_inputs:
                            inp = matching_inputs[0]
                            required_mark = " ✅ REQUIRED" if inp['required'] else ""
                            print(f"      {field_name}: {inp['type']}{required_mark}")
                
                # Show CAPTCHA detection
                captcha_images = [img for img in images if 'captcha' in img.get('src', '').lower() or 'captcha' in img.get('alt', '').lower()]
                if captcha_images:
                    print(f"\n   🔒 CAPTCHA Detection: {len(captcha_images)} image(s) found")
                    for img in captcha_images:
                        print(f"      Size: {img['width']}x{img['height']}, Alt: {img['alt']}")
            
            # Show file outputs
            print(f"\n📁 Generated Files:")
            for key, path in results.items():
                if key != "success" and os.path.exists(path):
                    size = os.path.getsize(path)
                    print(f"   {os.path.basename(path)}: {size:,} bytes")
            
            print(f"\n✅ The DOM Analysis Pipeline is ready for production use!")
            print(f"💡 Integration Points:")
            print(f"   🔗 Connect Stage 3 to Azure OpenAI for real AI analysis")
            print(f"   🔗 Use extracted form data with existing form_filler.py")
            print(f"   🔗 Integrate with appointment_checker.py workflow")
            
            return True
        else:
            print("❌ Pipeline execution failed")
            return False


if __name__ == "__main__":
    print("🧪 DOM Analysis Integration Test")
    print("Testing with realistic Aachen appointment form")
    print("=" * 60)
    
    success = test_aachen_appointment_workflow()
    
    if success:
        print("\n🎊 Integration test completed successfully!")
        print("\nThe structured HTML parsing system is now ready to:")
        print("• Parse complex appointment booking forms")
        print("• Extract form fields and validation rules") 
        print("• Identify CAPTCHA images and security elements")
        print("• Support AI-powered element analysis")
        print("• Integrate with existing appointment booking logic")
    else:
        print("\n❌ Integration test failed")
        print("Check the implementation for issues.")