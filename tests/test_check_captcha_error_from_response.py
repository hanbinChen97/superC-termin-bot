import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from superc.form_filler import check_captcha_error_from_response


class CheckCaptchaErrorFromResponseTests(unittest.TestCase):
    def test_step_6_error_page_detects_captcha(self) -> None:
        html_path = PROJECT_ROOT / "data/pages/superc/step_6_form_error_20251001_161712.html"
        html_content = html_path.read_text(encoding="utf-8")

        self.assertTrue(
            check_captcha_error_from_response(html_content),
            "Expected captcha error to be detected for step 6 error page.",
        )


if __name__ == "__main__":
    unittest.main()
