#-*- coding: utf-8 -*-

"""
<TODO>
창의 최소크기와 최대크기 지정
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

# 서드파티
import pandas as pd

# 우리 프로젝트
from storehelper.crawlutil.common import ChromeDriverManager
from storehelper.sheetutil.common import authorize, get_sheet
from storehelper.sheetutil.writer import overwrite_entire_dataframe


cdm = ChromeDriverManager()
cdm.set_default_download_dir(pathlib.Path(__file__).stem, join=True)
chrome_driver = cdm.get_chrome_driver()
chrome_download_dir = cdm.get_default_download_dir()


def get_latest_file():
    """크롬 다운로드 경로로부터 최신 csv 파일을 읽어와
    dataframe 객체로 리턴합니다.

    Returns:
        DataFrame: 데이터프레임 객체 csv
    """
    query = os.path.join(chrome_download_dir,'*.csv') # 출력파일 이름으로 설정해주고 싶지만 한글 안먹음
    files = glob.glob(query)
    print(f'searching files...\n\t{repr(files)}')
    files.sort(key=lambda x: os.path.getmtime(x))
    file = files[-1]
    print(f'selected {file}')
    df = pd.read_csv(file)

    return df


def read_json():
    """파일 이름과 동일한 파일명의 json 파일을 읽어들입니다.
    """
    filename = pathlib.Path(__file__).stem
    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 
        f"{filename}.json")
    print(path)
    with open(path, 'r') as f:
        di = json.load(f)
    return di


def run():
    rk_meta = read_json()['랭킹도구']
    gs_meta = read_json()['google_spreadsheet']
    gs_r_meta = gs_meta['read_keyword']
    gs_w_meta = gs_meta['write_ranking']
    smartstore_name = read_json()['smartstore_name']

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
                df = get_latest_file()

            df = pd.concat([df, get_latest_file()], join='outer', axis=0)
            _join_cnt += 1

    if not _join_cnt:
        chrome_driver.find_element(by='id',
            value=rk_meta['CSV추출_button']['tag_id'],
        ).click()
        cdm.wait_for_downloads_v2()
        df = get_latest_file()

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