import types
from bs4 import BeautifulSoup
import copy

# mock profile 数据
test_profile = {
    "vorname": "TestVorname",
    "nachname": "TestNachname",
    "email": "test@example.com",
    "phone": "1234567890",
    "geburtsdatumDay": "15",
    "geburtsdatumMonth": "7",
    "geburtsdatumYear": "1999",
    "emailCheck": "test@example.com",
    "captcha_code": "TEST123"  # 真正的验证码
}

# 读取html
with open("data/pages/superc/step_6_form_submitted_20250731_063723.html", "r", encoding="utf-8") as f:
    html = f.read()
soup = BeautifulSoup(html, "html.parser")

# 字段映射: input 的 name/id -> profile key
input_map = {
    "vorname": "vorname",
    "nachname": "nachname",
    "email": "email",
    "emailwhlg": "emailCheck",
    "geburtsdatumDay": "geburtsdatumDay",
    "geburtsdatumMonth": "geburtsdatumMonth",
    "geburtsdatumYear": "geburtsdatumYear",
    "phone": "phone",
    "captcha_code": "captcha_code"  # 正确映射 captcha_code 到验证码
    # 注意：hunangskrukka 不在映射中，保持为空（蜜罐字段）
}

# 填写 input 框
def fill_inputs(soup, profile):
    for input_tag in soup.find_all("input"):
        key = None
        # 优先用 id，其次 name
        if input_tag.get("id") and input_tag.get("id") in input_map:
            key = input_map[input_tag.get("id")]
        elif input_tag.get("name") and input_tag.get("name") in input_map:
            key = input_map[input_tag.get("name")]
        if key and key in profile:
            input_tag["value"] = str(profile[key])
    return soup

soup_filled = fill_inputs(soup, test_profile)

# 保存新 HTML
with open("data/pages/superc/step_6_form_filled_mock.html", "w", encoding="utf-8") as f:
    f.write(str(soup_filled))

print("已保存: data/pages/superc/step_6_form_filled_mock.html")
