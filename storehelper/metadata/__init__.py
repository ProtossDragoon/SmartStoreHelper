# 내장 라이브러리
import os

# 우리 프로젝트
from storehelper.metadata import tool

tool.assert_json(
    os.path.join('.', 'storehelper', 'metadata', 'template.json')
)
# FIXME
_CHROME_DRIVER, _CHROME_DOWNLOAD_DIR, _CHROME_OPTIONS, _CHROME_DRIVER_PATH = tool.get_chrome_driver()