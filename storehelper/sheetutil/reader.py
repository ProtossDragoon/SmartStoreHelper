#-*- coding: utf-8 -*-

# 내장 라이브러리
import os

# 서드파티 라이브러리
import pandas as pd

# 우리 프로젝트
from storehelper.sheetutil import common


def get_data(gc, spreadsheet_url, spreadsheet_name):
    worksheet = common.get_sheet(gc, spreadsheet_url, spreadsheet_name)
    data = worksheet.get_all_values()
    return data

def get_data_with_df(gc, spreadsheet_url, spreadsheet_name):
    data = get_data(gc, spreadsheet_url, spreadsheet_name)
    df = pd.DataFrame(data)
    return df