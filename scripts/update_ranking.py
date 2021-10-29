#-*- coding: utf-8 -*-

# 내장 라이브러리
import os
import pprint
import time
import shutil
import pathlib
import glob
import json
from datetime import date

# 서드파티
import pandas as pd

# 우리 프로젝트
from .common import read_json, get_latest_file_as_df
from storehelper.crawlutil.common import ChromeDriverManager
from storehelper.sheetutil.common import authorize, get_sheet
from storehelper.sheetutil.writer import overwrite_entire_dataframe

rk_meta = read_json(filename=pathlib.Path(__file__).stem)['랭킹도구']
gs_meta = read_json(filename=pathlib.Path(__file__).stem)['google_spreadsheet']
gs_r_meta = gs_meta['read_keyword']
gs_w_meta = gs_meta['write_ranking']
smartstore_name = read_json(filename=pathlib.Path(__file__).stem)['smartstore_name']

cdm = ChromeDriverManager()
cdm.set_default_download_dir(pathlib.Path(__file__).stem, join=True)
chrome_driver = cdm.get_chrome_driver()
chrome_download_dir = cdm.get_default_download_dir()


def run():
    chrome_driver.get(rk_meta['url'])
    chrome_driver.find_element(by='id',
        value=rk_meta['스토어명_input']['tag_id']
    ).send_keys(smartstore_name)

    gc = authorize()
    worksheet = get_sheet(gc, 
        spreadsheet_url=gs_r_meta['url'],
        spreadsheet_name=gs_r_meta['name'])
    
    r_index_start = gs_r_meta['keyword']['start_col'] + str(gs_r_meta['keyword']['start_row'])
    r_index_end   = gs_r_meta['keyword']['end_col'] + str(gs_r_meta['keyword']['end_row'])
    reading_cells = worksheet.range(f'{r_index_start}:{r_index_end}')
    print(f'range : {r_index_start}:{r_index_end}')
    print(f'total {repr(len(reading_cells))} cells')
    
    df = None
    _join_cnt = 0
    for i, cell in enumerate(reading_cells, start=1):

        if len(cell.value):
            keyword = cell.value.replace(' ', '')
            if len(keyword) <= rk_meta['검색어_input']['검색어최대길이']:
                print(f'{i} - {keyword}')
                # print(cells[i] is reading_cells)
                # # returns True : 둘은 사이는 복사관계가 아니라 동일한 객체임.
                chrome_driver.find_element(by='id',
                    value=rk_meta['검색어_input']['tag_id']
                ).send_keys(keyword)
                chrome_driver.find_element(by='xpath',
                    value=rk_meta['검색_button']['xpath']).click()
                time.sleep(2)

        if i % rk_meta['검색최대반복가능횟수'] == 0:
            chrome_driver.find_element(by='id',
                value=rk_meta['CSV추출_button']['tag_id'],
            ).click()
            cdm.wait_for_downloads_v2()
            chrome_driver.get(rk_meta['url'])
            chrome_driver.find_element(by='id',
                value=rk_meta['스토어명_input']['tag_id']
            ).send_keys(smartstore_name)

            if not _join_cnt:
                # 처음에만 저장해요
                df = get_latest_file_as_df(chrome_download_dir)
            else:
                df = pd.concat(
                    [df, get_latest_file_as_df(chrome_download_dir)], 
                    join='outer', 
                    axis=0)
            _join_cnt += 1

    if not _join_cnt:
        chrome_driver.find_element(by='id',
            value=rk_meta['CSV추출_button']['tag_id'],
        ).click()
        cdm.wait_for_downloads_v2()
        df = get_latest_file_as_df(chrome_download_dir)

    # 데이터를 구글 스프레드시트에 씁니다.
    gc = authorize()
    today = date.today()
    yy = str(today.year)[-2:]
    mm = str(today.month)
    dd = str(today.day)
    worksheet = get_sheet(gc, 
        spreadsheet_url=gs_w_meta['url'],
        spreadsheet_name=f"{gs_w_meta['name']}_{yy}_{mm}_{dd}")
    overwrite_entire_dataframe(worksheet, df)

    cdm.chrome_close_safely()


if __name__=='__main__':
    run()