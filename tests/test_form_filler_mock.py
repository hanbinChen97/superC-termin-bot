import types
from bs4 import BeautifulSoup
from superc import form_filler

# mock config.currentProfile
test_profile = types.SimpleNamespace(
    vorname="TestVorname",
    nachname="TestNachname",
    email="test@example.com",
    phone="1234567890",
    geburtsdatum_day=15,
    geburtsdatum_month=7,
    geburtsdatum_year=1999
)

form_filler.config.currentProfile = {
    "type": "database",
    "data": test_profile
}

def dummy_recognize_captcha(path):
    return "abcd"
form_filler.recognize_captcha = dummy_recognize_captcha

def dummy_save_page_content(text, step, location):
    pass
form_filler.save_page_content = dummy_save_page_content

# 读取html
with open("data/pages/superc/step_6_form_submitted_20250731_063723.html", "r", encoding="utf-8") as f:
    html = f.read()
soup = BeautifulSoup(html, "html.parser")

# mock session（不实际提交）
class DummySession:
    def post(self, url, data, headers):
        print("POST URL:", url)
        print("POST DATA:", data)
        print("POST HEADERS:", headers)
        # 返回一个dummy对象
        class DummyRes:
            def __init__(self):
                self.text = "Online-Terminanfrage erfolgreich"
                self.status_code = 200
        return DummyRes()

session = DummySession()

success, res = form_filler.fill_form(session, soup, "dummy_captcha.png", "test_location")
print("提交是否成功:", success)
if success:
    print("模拟提交成功，表单数据已生成。")
else:
    print("模拟提交失败:", res)
