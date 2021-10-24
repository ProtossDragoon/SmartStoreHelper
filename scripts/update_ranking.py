#-*- coding: utf-8 -*-

# 내장 라이브러리
import os
import pprint
import time
import shutil
import pathlib
import glob

# 서드파티
import pandas as pd

# 우리 프로젝트
from storehelper.sheetutil.common import authorize, get_sheet
from storehelper.sheetutil.writer import overwrite_entire_dataframe
from storehelper.crawlutil.common import chrome_driver, chrome_close_safely, wait_for_downloads_v2
from storehelper.crawlutil.common import get_chrome_default_download_dir, set_with_join_chrome_default_download_dir

set_with_join_chrome_default_download_dir(pathlib.Path(__file__).stem)
chrome_download_dir = get_chrome_default_download_dir()


def get_ranking_search_engine(name):
    return {
        "랭킹도구":{
            "url":"http://dogumaster.com/biz/rank",
            "스토어명":{
                "input_tag_name":"query",
                "input_tag_id":"input_mall",
            },
            "검색어":{
                "input_tag_name":"query",
                "input_tag_id":"input_query",
            },
            "CSV추출":{
                "button_tag_id":"btn_csv"
            },
            "엑셀추출":{
                "button_tag_id":"btn_excel"
            },
            "검색어최대길이":15,
            "최대반복가능횟수":100,
            "출력파일이름":"랭킹도구마스터",
        },
    }.get(name)


def run():
    smartstore_name = "헬로콕"    
    search_engine_meta = get_ranking_search_engine("랭킹도구")
    chrome_driver.get(search_engine_meta['url'])
    chrome_driver.find_element(by='id',
        value=search_engine_meta["스토어명"]["input_tag_id"]
    ).send_keys(smartstore_name)

    gc = authorize()
    worksheet = get_sheet(gc, 
        spreadsheet_url="https://docs.google.com/spreadsheets/d/1_5cFQJFzAS8WkUBM1JrFFmm9gvH-Cz9RcxBUvGxdZ7Y/edit?usp=sharing",
        spreadsheet_name="시트1")
    cells = worksheet.range('B2:B999')
    print(f'total {repr(len(cells))} cells')

    for i, cell in enumerate(cells):
        if i >= search_engine_meta["최대반복가능횟수"]:
            break
        if len(cell.value):
            keyword = cell.value.replace(" ", "")
            if len(keyword) <= search_engine_meta["검색어최대길이"]:
                print(f'{i} - {keyword}')
                # print(cells[i] is cell)
                # # returns True : 둘은 사이는 복사관계가 아니라 동일한 객체임.
                chrome_driver.find_element(by='id',
                    value=search_engine_meta["검색어"]["input_tag_id"]
                ).send_keys(keyword)
                chrome_driver.find_element(by='xpath',
                    value='//*[@id="input_submit"]').click()
                time.sleep(2)

        break
            
    chrome_driver.find_element(by='id',
        value=search_engine_meta["CSV추출"]["button_tag_id"],
    ).click()
    wait_for_downloads_v2()

    # 최신 파일을 가져옵니다.
    query = os.path.join(chrome_download_dir,'*.csv') # 출력파일 이름으로 설정해주고 싶지만 한글 안먹음
    files = glob.glob(query)
    print(f'searching files...\n\t{repr(files)}')
    files.sort(key=lambda x: os.path.getmtime(x))
    file = files[-1]
    print(f'selected {file}')
    df = pd.read_csv(file)
    
    # 데이터를 구글 스프레드시트에 씁니다.
    gc = authorize()
    worksheet = get_sheet(gc, 
        spreadsheet_url="https://docs.google.com/spreadsheets/d/1_5cFQJFzAS8WkUBM1JrFFmm9gvH-Cz9RcxBUvGxdZ7Y/edit?usp=sharing",
        spreadsheet_name='donttouchme')
    overwrite_entire_dataframe(worksheet, df)

    chrome_close_safely()


if __name__=='__main__':
    run()