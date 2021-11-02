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


def file_rectification(
    lines:list
)->list:
    """
    Args:
        lines (list): 파일 한 줄 한 줄이 들어있는 리스트

    Returns:
        list: 파일 한 줄 한 줄이 들어있는 리스트
    """

    new_lines = []
    new_lines.append(
        "-,키워드,PC검색,모바일검색,전체,문서수,비율,-\n"
    )
    for i, line in enumerate(lines):
        if i == 0:
            continue

        single_line_li = line.split('"')
        
        sifter_1 = []
        for e in single_line_li:
            if e == ',': # 콤마
                pass
            elif e == '\n': # 개행
                pass
            elif e == '': # 공백
                pass
            else:
                sifter_1.append(e)
            # new_single_line_li 에는 콤마, 공백, 개행을 제외한 애들만 잔뜩 들어가있음.

        sifter_2 = []
        for i, e in enumerate(sifter_1):
            if i in [2, 3, 4, 5]:
                # int 으로 변환 필요)
                e = str(int(e.replace(",", "")))
                sifter_2.append(e)
            elif i in [6]:
                # float 으로 변환 필요
                try:
                    e = str(float(e))
                except ValueError:
                    pass
                sifter_2.append(e)
            elif i >= 8:
                pass
            else:
                # string 을 유지
                sifter_2.append(e)
        
        # 한 줄을 스트링으로
        new_single_line = ','.join(sifter_2)
        # 마지막으로 개행 추가
        new_single_line += '\n'

        # 1줄씩 병합
        new_lines.append(new_single_line)

    return new_lines


def run(
    kw_meta, gs_meta, 
    gs_r_meta, gs_w_meta,
    cdm, chrome_driver, chrome_download_dir
):
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
    chrome_driver.get(kw_meta['url'])
    for i, cell in enumerate(reading_cells, start=1):
        keyword = cell.value.replace(' ', '')
        if not len(keyword):
            print(f'키워드 {repr(keyword)} 가 비어 있습니다. 탐색을 중단합니다.')
            # 키워드가 비어 있으면 탐색을 중단합니다.
            break

        print(f'{i} - {keyword}')
        chrome_driver.find_element(by='id',
            value=kw_meta['키워드_input']['tag_id']
        ).send_keys(keyword)
        time.sleep(0.3)
        chrome_driver.find_element(by='xpath',
            value=kw_meta['검색_button']['xpath']).click()
        cdm.wait_for_block(id=kw_meta['blocking_tag_id'])

        if i % kw_meta['검색최대반복가능횟수'] == 0:
            chrome_driver.find_element(by='id',
                value=kw_meta['CSV추출_button']['tag_id'],
            ).click()
            cdm.wait_for_downloads_v2()
            chrome_driver.get(kw_meta['url'])

            if not _join_cnt:
                # 처음에만 저장해요
                df = get_latest_file_as_df(
                    chrome_download_dir,
                    parse_fn=file_rectification)
            else:
                df = pd.concat(
                    [df, get_latest_file_as_df(
                            chrome_download_dir,
                            parse_fn=file_rectification)], 
                    join='outer', 
                    axis=0)
            _join_cnt += 1
        
    if not _join_cnt:
        chrome_driver.find_element(by='id',
            value=kw_meta['CSV추출_button']['tag_id'],
        ).click()
        cdm.wait_for_downloads_v2()
        df = get_latest_file_as_df(
            chrome_download_dir, 
            parse_fn=file_rectification)

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



if __name__ == '__main__':

    kw_meta = read_json(filename=pathlib.Path(__file__).stem)['도구마스터키워드도구']
    gs_meta = read_json(filename=pathlib.Path(__file__).stem)['google_spreadsheet']
    gs_r_meta = gs_meta['read_keyword']
    gs_w_meta = gs_meta['write_traffic']

    cdm = ChromeDriverManager()
    cdm.set_default_download_dir(pathlib.Path(__file__).stem, join=True)
    cdm.set_chrome_window_size(
        w=kw_meta['window_size_w'], 
        h=kw_meta['window_size_h'])
    chrome_driver = cdm.get_chrome_driver()
    chrome_download_dir = cdm.get_default_download_dir()
    run(
        kw_meta, gs_meta, 
        gs_r_meta, gs_w_meta, 
        cdm, chrome_driver, chrome_download_dir
    )