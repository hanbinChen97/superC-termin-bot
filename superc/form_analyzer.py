import os
from bs4 import BeautifulSoup

def analyze_form(html_file_path):
    """
    Analyze the form in the given HTML file and extract field attributes.

    Args:
        html_file_path (str): Path to the HTML file.

    Returns:
        list: A list of dictionaries containing field attributes.
    """
    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"File not found: {html_file_path}")

    with open(html_file_path, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    form = soup.find('form')
    if not form:
        raise ValueError("No form found in the HTML file.")

    fields = []

    for input_tag in form.find_all(['input', 'textarea', 'select']):
        field = {
            'name': input_tag.get('name'),
            'type': input_tag.get('type', 'text'),
            'required': 'required' in input_tag.attrs,
            'default': input_tag.get('value', ''),
        }

        if input_tag.name == 'textarea':
            field['type'] = 'textarea'
            field['default'] = input_tag.text

        if input_tag.name == 'select':
            field['type'] = 'select'
            field['options'] = [option.text for option in input_tag.find_all('option')]

        fields.append(field)

    return fields

def generate_form_filler_code(fields):
    """
    Generate Python code to fill the form based on the analyzed fields.

    Args:
        fields (list): A list of dictionaries containing field attributes.

    Returns:
        str: Python code to fill the form.
    """
    code_lines = ["from selenium import webdriver", "from selenium.webdriver.common.by import By", "from selenium.webdriver.support.ui import Select", "", "driver = webdriver.Chrome()", "driver.get('URL_TO_FORM')", ""]

    for field in fields:
        if field['type'] == 'text' or field['type'] == 'email' or field['type'] == 'number':
            code_lines.append(f"driver.find_element(By.NAME, '{field['name']}').send_keys('{field['default']}')")
        elif field['type'] == 'textarea':
            code_lines.append(f"driver.find_element(By.NAME, '{field['name']}').send_keys('{field['default']}')")
        elif field['type'] == 'select':
            code_lines.append(f"select = Select(driver.find_element(By.NAME, '{field['name']}'))")
            code_lines.append(f"select.select_by_visible_text('{field['options'][0]}')")
        elif field['type'] == 'checkbox':
            code_lines.append(f"driver.find_element(By.NAME, '{field['name']}').click()")

    code_lines.append("# Submit the form")
    code_lines.append("driver.find_element(By.NAME, 'submit').click()")

    return '\n'.join(code_lines)

if __name__ == "__main__":
    html_file = "data/pages/superc/step_5_term_selected_20250804_064311.html"
    fields = analyze_form(html_file)

    print("Analyzed Fields:")
    for field in fields:
        print(field)

    print("\nGenerated Form Filler Code:")
    print(generate_form_filler_code(fields))
