USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
BASE_URL = "https://termine.staedteregion-aachen.de/auslaenderamt/"


# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
# 详细日志模式 - 设为False可在生产环境中减少日志输出
VERBOSE_LOGGING = False
# VERBOSE_LOGGING = True

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