#-*- coding: utf-8 -*-

# 내장 라이브러리
import os
import pprint
import time
import shutil
import pathlib
import glob
import json

# 서드파티
import pandas as pd
from selenium.common.exceptions import TimeoutException, ElementNotVisibleException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 우리 프로젝트
from storehelper.sheetutil.common import authorize, get_sheet
from storehelper.sheetutil.writer import overwrite_entire_dataframe
from storehelper.crawlutil.common import chrome_driver, chrome_close_safely, wait_for_downloads_v2, scroll_page_down
from storehelper.crawlutil.common import get_chrome_default_download_dir, set_with_join_chrome_default_download_dir

set_with_join_chrome_default_download_dir(pathlib.Path(__file__).stem)
chrome_download_dir = get_chrome_default_download_dir()


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


def item_exists(ns_meta):
    """페이지에 아이템이 몇 개 존재하는지 여부를 리턴하는 헬퍼 함수입니다.

    Args:
        ns_meta (dict): meta['naver_shopping'] 일 가능성이 높습니다.

    Returns:
        int: (현재까지 보이는) 상품의 개수
        web elements: 찾아낸 아이템들
    
    Exceptinos:
        ElementNotVisibleException: selenium 예외로, url 로 검사한 결과
            검색 페이지로 넘어가지 못한 것 같을 때 레이즈합니다.
    """
    time.sleep(1)
    if chrome_driver.current_url.find('search') == -1:
        m = f'아직 검색 페이지에 도착하지 못했습니다. 현재 url : {chrome_driver.current_url}'
        raise ElementNotVisibleException(m)

    items = chrome_driver.find_elements(By.XPATH,
        value=ns_meta['item_container']['xpath']
        )
    if len(items):
        found_items_cnt = len(items)
        return found_items_cnt, items
    else:
        e = chrome_driver.find_elements(By.XPATH,
            value=ns_meta['no_result']['xpath']
            )
        if e:
            print('해당 키워드의 상품이 존재하지 않습니다.')
            return 0, e
        else:
            if chrome_driver.current_url.find('search') == -1:
                print('알 수 없는 오류입니다.')
                return 0, None
            else:
                print('성인 키워드입니다.')
                return 0, None


def run():
    ns_meta = read_json()['naver_shopping']
    gs_meta = read_json()['google_spreadsheet']
    
    chrome_driver.get(ns_meta['url'])
    worksheet = get_sheet(authorize(),
        spreadsheet_url=gs_meta['url'],
        spreadsheet_name=gs_meta['name'])

    r_index_start = gs_meta['keyword']['start_col'] + str(gs_meta['keyword']['start_row'])
    r_index_end   = gs_meta['keyword']['end_col'] + str(gs_meta['keyword']['end_row'])
    reading_cells = worksheet.range(f'{r_index_start}:{r_index_end}')
    print(f'range : {r_index_start}:{r_index_end}')

    w_index_start = gs_meta['target']['start_col'] + str(gs_meta['target']['start_row'])
    w_index_end   = gs_meta['target']['end_col'] + str(gs_meta['target']['end_row'])
    writing_cells = worksheet.range(f'{w_index_start}:{w_index_end}')

    # 모든 셀에 대해서 확인합니다.
    for i, (r_cell, w_cell) in enumerate(zip(reading_cells, writing_cells)):
        keyword = r_cell.value
        if not len(keyword):
            print(f'키워드 {repr(keyword)} 가 비어 있습니다. 탐색을 중단합니다.')
            # 키워드가 비어 있으면 탐색을 중단합니다.
            break
        chrome_driver.get(ns_meta['url'])
        print(f'키워드 {repr(keyword)} 에 대해서 검사를 시작합니다.')
        chrome_driver.find_element(By.XPATH,
            value=ns_meta['search_box']['xpath']
        ).clear() # 기본값 정리
        chrome_driver.find_element(By.XPATH,
            value=ns_meta['search_box']['xpath']
        ).send_keys(keyword) # 입력

        while True:
            # 네이버 쇼핑 메인은 약간의 시간차 공격을 합니다.
            # 이 시간동안 대기합니다.
            try:
                WebDriverWait(chrome_driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, ns_meta['search_button']['xpath'])
                    )).click()
            except TimeoutException as e:
                print(f'5초간 응답이 없습니다. 다시 시도합니다.')
            
            try:
                ret, _ = item_exists(ns_meta) 
                if ret or (not ret):
                    # 아이템이 있든 말든, 넘어갔으므로 loop 을 나갑니다.
                    break
            except ElementNotVisibleException as e:
                continue

        found_items_cnt = 0
        trial_cnt = 0
        retry_max_cnt = 5
        while found_items_cnt < 10: # 10 개 미만의 상품이 발견될 경우
            # 네이버는 스크롤을 내리면 아이템들이 동적으로 로드됩니다.
            scroll_page_down(delay=0.5)

            # 1페이지에 등록되어 있는 아이템들의 카테고리를 확인합니다.
            found_items_cnt, items = item_exists(ns_meta)
            if retry_max_cnt:
                trial_cnt += 1
                print(f'Loading store, trial {trial_cnt}/{retry_max_cnt}')
                print('실제로 해당 키워드에 등록된 아이템이 너무 적어서 지연이 발생할수도 있고,'
                    '쇼핑검색 로딩이 느린 것일수도 있습니다. MACOS 의 경우,'
                    '크롬을 최소화시켜두었을 때 이 현상이 발생할 수 있습니다.')
                if trial_cnt == retry_max_cnt:
                    break
        
        if items is None:
            print(f'{repr(keyword)} 는 조회할 수 없는 키워드이므로 패스합니다.')
            continue

        res = []
        for n, item in enumerate(items, start=1):
            print(f'n: {n}/{len(items)}')
            categories = item.find_elements(By.TAG_NAME,
                value=ns_meta["item_category_container"]["tag_name"]
            )
            for idx, category in enumerate(categories):
                if idx == 0:
                    s = f'{category.text}'
                else:
                    s += f'_{category.text}'
            print(f'{s}')
            res.append(s)

        # 유니크 값을 검사하고 스프레드시트에 작성할 텍스트를 생성합니다.
        ret = ''
        for idx, unique_category in enumerate(pd.Series(res).unique()):
            if idx == 0:
                ret = f'{unique_category}'
            else:
                ret += f'\n{unique_category}'
        
        if ret:
            print(f'키워드 {repr(keyword)} 에 해당하는 카테고리 셀'
                f'(기존 스프레드 시트 값:{repr(w_cell.value)}) 에'
                f'값 {repr(ret)} 을 덮어쓸 예정입니다.')
            w_cell.value = ret
            ret = ''

    # API 콜을 최소화하기 위해 모든 작업을 마친 뒤 업데이트합니다.
    # 중간에 업데이트할 수 있도록 만들어주는 것도 좋은 방법이리라 생각합니다.
    worksheet.update_cells(writing_cells)
    chrome_close_safely()


if __name__ == "__main__":
    run()