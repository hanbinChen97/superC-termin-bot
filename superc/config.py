import logging
import re

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
BASE_URL = "https://termine.staedteregion-aachen.de/auslaenderamt/"


# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
DEFAULT_SCHRITT = "-"
ENABLE_SUPABASE_LOGS = True
# 详细日志模式 - 设为False可在生产环境中减少日志输出
# VERBOSE_LOGGING = False
VERBOSE_LOGGING = True


_SCHRITT_PATTERN = re.compile(r"(Schritt\s*\d+)")
_PREVIOUS_FACTORY = logging.getLogRecordFactory()


def _inject_schritt(*factory_args, **factory_kwargs):
    record = _PREVIOUS_FACTORY(*factory_args, **factory_kwargs)
    try:
        message = record.getMessage()
    except Exception:
        message = ""

    match = _SCHRITT_PATTERN.search(message) if isinstance(message, str) else None
    record.schritt = match.group(1) if match else DEFAULT_SCHRITT
    return record


logging.setLogRecordFactory(_inject_schritt)

# 地点特有配置
LOCATIONS = {
    "superc": {
        "name": "superc",
        "selection_text": "Super C",
        "submit_text": "Ausländeramt Aachen - Außenstelle RWTH auswählen"
    },
    "infostelle": {
        "name": "infostelle",
        "selection_text": "Infostelle",
        "submit_text": "Ausländeramt Aachen - Infostelle auswählen"
    }
}
# 
