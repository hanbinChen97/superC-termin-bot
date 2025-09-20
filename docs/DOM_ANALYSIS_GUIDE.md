# DOM Analysis Pipeline - Usage Guide

## Overview

The DOM Analysis Pipeline provides structured HTML parsing with AI analysis capabilities for the Aachen Termin Bot. It implements a 4-stage workflow to convert raw HTML into actionable data for automated form filling.

## Architecture

```
Stage 1: HTML Download    → raw_page.html
Stage 2: HTML → JSON      → page_structure.json  
Stage 3: AI Analysis      → analysis_result.json
Stage 4: Element Extract  → extracted_content.json
```

## Quick Start

```python
from superc.dom_analysis import run_full_pipeline

# Run complete pipeline
results = run_full_pipeline(
    url="https://termine.staedteregion-aachen.de/auslaenderamt/",
    base_dir="superc",
    query="Find all form elements for appointment booking"
)

if results["success"]:
    print("Pipeline completed successfully!")
    print(f"JSON structure: {results['json_path']}")
    print(f"AI analysis: {results['analysis_path']}")
    print(f"Extracted data: {results['extraction_path']}")
```

## Individual Stage Usage

### Stage 1: HTML Download
```python
from superc.dom_analysis import download_html

success = download_html(
    url="https://example.com/appointment-form",
    save_path="superc/html_pages/raw_page.html"
)
```

### Stage 2: HTML → JSON Conversion
```python
from superc.dom_analysis import html_to_json

success = html_to_json(
    html_path="superc/html_pages/raw_page.html",
    json_save_path="superc/parsed_json/page_structure.json"
)
```

### Stage 3: AI Structure Analysis
```python
from superc.dom_analysis import analyze_structure

query = """
Find all form elements including:
- Input fields (name, type, validation)
- Submit buttons
- CAPTCHA images
- Required fields
"""

success = analyze_structure(
    json_path="superc/parsed_json/page_structure.json",
    output_path="superc/parsed_json/analysis_result.json",
    query=query
)
```

### Stage 4: Element Extraction
```python
from superc.dom_analysis import extract_by_id

success = extract_by_id(
    html_path="superc/html_pages/raw_page.html",
    analysis_path="superc/parsed_json/analysis_result.json",
    output_path="superc/parsed_json/extracted_content.json"
)
```

## Data Formats

### JSON Structure Format
```json
[
  {
    "id": 1,
    "tag": "form",
    "attrs": {"id": "appointment-form", "method": "post"},
    "text": "",
    "parent_id": null,
    "children": [
      {
        "id": 2,
        "tag": "input",
        "attrs": {"type": "text", "name": "vorname", "required": true},
        "text": "",
        "parent_id": 1,
        "children": []
      }
    ]
  }
]
```

### AI Analysis Result Format
```json
{
  "query": "Find form elements",
  "total_elements": 150,
  "analysis_timestamp": "2024-01-01T00:00:00Z",
  "elements": [
    {
      "id": 2,
      "tag": "input",
      "text": "",
      "attrs": {"name": "vorname", "type": "text", "required": true},
      "reason": "User first name input field, required for appointment"
    }
  ]
}
```

### Extracted Content Format
```json
{
  "extraction_timestamp": "2024-01-01T00:00:00Z",
  "source_html": "superc/html_pages/raw_page.html",
  "analysis_source": "superc/parsed_json/analysis_result.json",
  "total_mapped_elements": 150,
  "extracted_elements": [
    {
      "id": 2,
      "tag": "input",
      "reason": "User first name input field",
      "html_snippet": "<input type=\"text\" name=\"vorname\" required>",
      "text_content": "",
      "attributes": {
        "name": "vorname",
        "type": "text",
        "required": true
      }
    }
  ]
}
```

## Integration with Existing System

### With Form Filler
```python
from superc.dom_analysis import extract_by_id
from superc.form_filler import fill_form_with_captcha_retry

# Extract form structure
extract_by_id(html_path, analysis_path, extraction_path)

# Use extracted data to inform form filling
with open(extraction_path, 'r') as f:
    extracted_data = json.load(f)

# Map extracted fields to profile data
field_mapping = {}
for element in extracted_data['extracted_elements']:
    if element['tag'] == 'input':
        field_mapping[element['attributes']['name']] = element['id']

# Use mapping in form filling process
```

### With Appointment Checker
```python
from superc.dom_analysis import run_full_pipeline
from superc.appointment_checker import run_check

# Analyze the appointment page structure
results = run_full_pipeline(
    url=appointment_url,
    query="Find appointment time slots and booking form"
)

# Use analysis results to enhance appointment checking
```

## Configuration

### Element Focus Configuration
The analysis focuses on elements defined in `superc/analysis_docs/element_focus.md`:

- **Form Elements**: `form`, `input`, `button`, `select`
- **Navigation**: `a`, `nav`  
- **Content**: `h1-h3`, `div`, `span`
- **Security**: `img` (CAPTCHA), validation fields

### AI Analysis Queries
Common query patterns:

```python
# Form detection
query = "Find all form elements for user input"

# CAPTCHA detection  
query = "Identify CAPTCHA images and related input fields"

# Appointment slots
query = "Find available appointment time slots and selection buttons"

# Validation
query = "Identify required fields and validation rules"
```

## Error Handling

The pipeline includes comprehensive error handling:

```python
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO)

# Check results
results = run_full_pipeline(url, base_dir)
if not results["success"]:
    logging.error("Pipeline failed - check logs for details")
```

## Testing

Run the test suite:
```bash
python tests/test_dom_analysis.py
python tests/test_pipeline_demo.py  
python tests/test_final_demo.py
```

## Files and Directories

```
superc/
├── dom_analysis.py           # Main pipeline implementation
├── html_pages/               # Stage 1: Downloaded HTML files  
├── parsed_json/              # Stage 2-4: JSON data and results
└── analysis_docs/            # AI analysis configuration
    └── element_focus.md      # Element identification guidelines
```

## Performance Notes

- HTML parsing: ~100-500ms for typical appointment pages
- JSON conversion: ~50-200ms 
- AI analysis: Variable (depends on Azure OpenAI response time)
- Element extraction: ~10-50ms

## Limitations

- AI analysis currently uses mock implementation (ready for Azure OpenAI)
- Complex nested forms may require custom parsing rules
- Large pages (>1MB HTML) may have slower processing times

## Future Enhancements

1. **Real AI Integration**: Connect Stage 3 to Azure OpenAI API
2. **Caching**: Add intelligent caching for repeated page analysis  
3. **Validation**: Enhanced form validation rule detection
4. **Performance**: Optimize parsing for large documents
5. **Templates**: Pre-built analysis templates for common sites