"""키워드를 미친듯이 만들어냅니다.
이 파일이 하는 일은 정확히 다음과 같습니다.
네이버 스마트스토어에 무알콜칵테일을 판매한다고 생각해 봅시다.
사람들은, "캠핑용 무알콜 칵테일" 을 검색하기도 할테지만 "맛있는 무알콜 칵테일" 을 검색하기도 할 것입니다.
"캠핑용 맛있는 무알콜 칵테일" 을 검색하기도 하겠지요.
이 파일은 핵심(backbone)키워드와 보조키워드로 이루어져 있습니다.
핵심 키워드가 "무알콜", "칵테일" 이라면, 보조키워드는 "맛있는, 캠핑용" 입니다.
핵심 키워드를 모두 포함하는 선에서, 보조키워드를 0개~n개 랜덤한 위치에 삽입하며 모든 경우의 수를 만들어냅니다.
그리고 생성된 키워드를 스프레드시트의 시트 이름이 {광고그룹} 인 곳에 작성합니다.
"""

# 내장 라이브러리
import os
import pprint
import time
import shutil
import pathlib
import glob
import json
from datetime import date
from itertools import product, permutations, combinations_with_replacement
from gspread.exceptions import APIError

# 서드파티
import numpy as np
import pandas as pd

# 우리 프로젝트
from .common import read_json, get_latest_file_as_df
from storehelper.crawlutil.common import ChromeDriverManager
from storehelper.sheetutil.common import authorize, get_sheet, remove_sheet
from storehelper.sheetutil.reader import generate_list_matrix
from storehelper.sheetutil.writer import overwrite_entire_dataframe


def run(
    gs_meta, 
    gs_r_meta, gs_w_meta, 
    cdm, chrome_driver, chrome_download_dir
):
    # 데이터를 구글 스프레드시트서 읽어옵니다.
    gc = authorize()
    ws_r = get_sheet(gc, 
        spreadsheet_url=gs_r_meta['url'],
        spreadsheet_name=gs_r_meta['name'])    

    # --
    r_backbone_index_start = (
        gs_r_meta['seed_backbone']['range']['start_col']
        + str(gs_r_meta['seed_backbone']['range']['start_row']))
    r_backbone_index_end   = (
        gs_r_meta['seed_backbone']['range']['end_col'] + 
        str(gs_r_meta['seed_backbone']['range']['end_row']))
    r_backbone_range = f'{r_backbone_index_start}:{r_backbone_index_end}'
    r_backbone_cells = ws_r.range(r_backbone_range)
    n_r_backbone_rows = (
        gs_r_meta['seed_backbone']['range']['end_row'] - 
        gs_r_meta['seed_backbone']['range']['start_row'])
    n_r_backbone_cols = len(r_backbone_cells) // n_r_backbone_rows
    print(f'range : {r_backbone_index_start}:{r_backbone_index_end}')
    print(f'total {repr(len(r_backbone_cells))} cells')

    # --
    r_combination_index_start = \
            gs_r_meta['seed_combination']['range']['start_col'] \
        + str(gs_r_meta['seed_combination']['range']['start_row'])
    r_combination_index_end   = \
            gs_r_meta['seed_combination']['range']['end_col'] \
        + str(gs_r_meta['seed_combination']['range']['end_row'])
    r_combination_range = f'{r_combination_index_start}:{r_combination_index_end}'
    r_combination_cells = ws_r.range(r_combination_range)
    n_r_combination_rows = (
        gs_r_meta['seed_combination']['range']['end_row'] - 
        gs_r_meta['seed_combination']['range']['start_row'])
    n_r_combination_cols = len(r_combination_cells) // n_r_combination_rows
    print(f'range : {r_combination_index_start}:{r_combination_index_end}')
    print(f'total {repr(len(r_combination_cells))} cells')    

    # --
    r_groupname_index_start = \
            gs_r_meta['seed_groupname']['range']['start_col'] \
        + str(gs_r_meta['seed_groupname']['range']['start_row'])
    r_groupname_index_end   = \
            gs_r_meta['seed_groupname']['range']['end_col'] \
        + str(gs_r_meta['seed_groupname']['range']['end_row'])
    r_groupname_range = f'{r_groupname_index_start}:{r_groupname_index_end}'
    r_groupname_cells = ws_r.range(r_groupname_range)
    n_r_groupname_rows = (
        gs_r_meta['seed_groupname']['range']['end_row'] - 
        gs_r_meta['seed_groupname']['range']['start_row'])
    n_r_groupname_cols = len(r_groupname_cells) // n_r_groupname_rows
    print(f'range : {r_groupname_index_start}:{r_groupname_index_end}')
    print(f'total {repr(len(r_groupname_cells))} cells')

    _END_SIGNAL = '_PROD_END'
    _remove_blank = lambda x:len(x)!=0


    for adgroup in np.unique(np.array([e.value for e in r_groupname_cells])):
        # 시작하기 전에 작성할 시트를 제거 (초기화) 합니다.
        print(f'[Info] 스프레드시트에서 {adgroup} 시트를 제거합니다.')
        remove_sheet(gc,
            spreadsheet_url=gs_w_meta['url'],
            spreadsheet_name=f"{str(adgroup)}")


    # 키워드를 조합합니다.
    for adgroup, backbone_set, subkeyword_set in zip(
        generate_list_matrix(r_groupname_cells, n_col=1, return_value=True),
        generate_list_matrix(r_backbone_cells, n_row=n_r_backbone_rows, return_value=True),
        generate_list_matrix(r_combination_cells, n_row=n_r_combination_rows, return_value=True)):

        powerlink_contents_single_case = []

        # subkeyword_set 로 모든 조합을 뽑아내하기 전에, blank 셀은 고려 안 함
        subkeyword_set = list(filter(_remove_blank, subkeyword_set))
        
        # backbone 을 삽입하기 전에, blank 셀은 고려 안 함
        backbone_set = list(filter(_remove_blank, backbone_set))

        if len(subkeyword_set) == 0:
            # 선택적 키워드가 등록되어 있지 않은 경우
            continue
        if len(backbone_set) == 0:
            # backbone 키워드가 등록되어 있지 않은 경우
            continue

        print(f'[Info] 핵심 키워드 {backbone_set} 과 {len(subkeyword_set)} 개의 보조키워드가 감지되었습니다.')

        # 선택적 키워드가 1개 이상인 경우~ 모두 다 들어간 경우
        for L in range(1, len(subkeyword_set)):
            for perm in permutations(subkeyword_set, r=L): # 길이가 L 인 순열
                perm = list(perm)
                perm.append(_END_SIGNAL)
                # print(perm)
            
                # perm 에서 들어갈 위치를 len(backbone_set) 개 찾기
                for where_to_insert in product(perm.copy(), repeat=len(backbone_set)): # 중복순열
                    # perm 을 보존해 두기
                    perm_cache = perm.copy()
                    for backbone_idx, e in enumerate(where_to_insert):
                        idx = perm.index(e)
                        perm.insert(idx, backbone_set[backbone_idx])
                    # len(backbone_set) 개의 백본 키워드를 모두 삽입함
                    powerlink_contents_single_case.append(perm)
                    # perm 을 복원해 주기
                    perm = perm_cache

        # 잡문자 제거
        powerlink_contents_single_case = [e[:-1] for e in powerlink_contents_single_case]

        # 선택적 키워드가 들어가지 않고 backbone 키워드만 들어간 경우
        for prod in product(backbone_set, repeat=len(backbone_set)):
            prod = list(prod)
            powerlink_contents_single_case.append(prod)

        # 리스트를 스트링으로 변환
        powerlink_contents_single_case = [[' '.join(e)] for e in powerlink_contents_single_case]

        print(f'[Info] 핵심 키워드 {backbone_set} 으로 총 {len(powerlink_contents_single_case)} 개의 파워링크 키워드를 생성했습니다.')

        # 데이터를 구글 스프레드시트에 씁니다.
        _FLAG = True
        while _FLAG:
            try:
                ws_w = get_sheet(gc, 
                    spreadsheet_url=gs_w_meta['url'],
                    spreadsheet_name=f"{adgroup[0]}")
                # 덮어쓰지 않고 아래에 추가합니다.
                ws_w.append_rows(powerlink_contents_single_case)
                _FLAG = False
                if not _FLAG: # 작성 성공
                    print(f'[Info] 시트 {repr(adgroup[0])} 에 키워드 추가를 완료했습니다.')
                    pass
            except APIError:
                print('분당 api 사용 한도를 초과했습니다. 잠시 후 다시 시도합니다.')
                time.sleep(5)

    cdm.chrome_close_safely()


if __name__ == '__main__':
    gs_meta = read_json(filename=pathlib.Path(__file__).stem)['google_spreadsheet']
    gs_r_meta = gs_meta['read_keyword']
    gs_w_meta = gs_meta['write_keyword']

    cdm = ChromeDriverManager()
    cdm.set_default_download_dir(pathlib.Path(__file__).stem, join=True)
    chrome_driver = cdm.get_chrome_driver()
    chrome_download_dir = cdm.get_default_download_dir()
    run(
        gs_meta, 
        gs_r_meta, gs_w_meta, 
        cdm, chrome_driver, chrome_download_dir
    )