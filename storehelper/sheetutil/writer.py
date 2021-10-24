#-*- coding: utf-8 -*-

# 내장 라이브러리
import os

# 서드파티 라이브러리
import pandas as pd
from gspread_dataframe import set_with_dataframe

# 우리 프로젝트
from storehelper.metadata.tool import get_json_meatadata
from storehelper.sheetutil import common


def overwrite_entire_dataframe(worksheet, df):
    # 코드 스니펫으로만 사용하고 메인 api 로 사용하지는 말것.
    # FIXME : 원시적인 방법으로 일단 데이터 냅다 가져오기
    range_of_cells = worksheet.range('A1:AA1000') #-> Select the range you want to clear
    for cell in range_of_cells:
        cell.value = '' # 다 지워줌
    # 이 내용을 써준다.
    worksheet.update_cells(range_of_cells)
    set_with_dataframe(worksheet, df)