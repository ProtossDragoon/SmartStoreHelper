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


def generate_list_matrix(
    cells_list_1d:list, 
    n_col:int=None, 
    n_row:int=None, 
    return_value:bool=False
)->list:
    """이 함수는 1차원 리스트 형태로 읽어들인 값을
    n_col 개의 행과 n_row 개의 열로 구성된, 행렬 모양의 2차원 리스트를 반환합니다.

    Args:
        cells_list_1d (list): 타겟 리스트
        n_col (int, optional): n_row 로부터 계산될수도 있습니다. Defaults to None.
        n_row (n_row, optional): n_col 로부터 계산될수도 있습니다. Defaults to None.
        return_value (bool, optional): 값을 리턴할 수도 있고, 셀을 리턴할 수도 있습니다.
            셀을 리턴한다면, 해당 셀의 값에 값을 대입한 후 update() 를 통해 
            클라우드의 google spreadsheet 에 덮어쓸 수 있습니다. Defaults to False.

    Yields:
        list: 행렬 모양의 리스트입니다.
    """

    if n_col is None:
        n_col = len(cells_list_1d) // n_row

    ret = []
    for i, cells in enumerate(cells_list_1d, start=1):
        if return_value:
            ret.append(cells.value)
        else:
            ret.append(cells)
        if i % n_col == 0:
            yield ret
            ret = []