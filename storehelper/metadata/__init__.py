# 내장 라이브러리
import os

# 우리 프로젝트
from storehelper.metadata import tool

tool.assert_json(
    os.path.join('.', 'storehelper', 'metadata', 'template.json')
)