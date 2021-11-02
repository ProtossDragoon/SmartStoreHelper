#-*- coding: utf-8 -*-

"""
이 파일은 주로 metadata 를 읽어들이고 반드시 해야 하는 일들을 하는 역할을 수행합니다.
다음과 같은 기능을 포함하고 있습니다.
"""

# 내장 라이브러리
import os
import pprint
import json
import time

# 서드파티
from selenium import webdriver


def assert_json(
    json_path:str='./storehelper/metadata/template.json',
    print_meta:bool=False,
)->dict:
    """json 파일에 적힌 경로들이 유효한지 파악합니다.

    Args:
        json_path (str, optional): json 파일의 경로입니다. 
            Defaults to './storehelper/metadata/template.json'.

    Returns:
        dict: 딕셔너리로 파싱된 json 파일입니다.
    """
    with open(json_path) as f:
        dic = json.load(f)
    if print_meta:
        pprint.pprint(dic)
    assert os.path.exists(dic['CREDENTIAL_FILE_PATH_PATH']), f"\
        {dic['CREDENTIAL_FILE_PATH_PATH']} 는 존재하지 않는 파일입니다."
    assert os.path.exists(dic['CHROME_DRIVER_PATH']), f"\
        {dic['CHROME_DRIVER_PATH']} 는 존재하지 않는 파일입니다."
    assert os.path.exists(dic['DOWNLOADING_FILE_DIR']), f"\
        {dic['DOWNLOADING_FILE_DIR']} 는 존재하지 않는 파일입니다."
    
    for _, v in dic['NAVER_ADS_CREDENTIAL'].items(): 
        assert os.path.exists(v['ACCESS_LICENSE_TXT_PATH']), f"\
            {v['ACCESS_LICENSE_TXT_PATH']} 는 존재하지 않는 파일입니다."
        assert os.path.exists(v['SECRET_KEY_TXT_PATH']), f"\
            {v['SECRET_KEY_TXT_PATH']} 는 존재하지 않는 파일입니다."
    return dic


def get_json_meatadata(
    json_path:str='./storehelper/metadata/template.json'
)->dict:
    """json metadata 에 대한 getter 입니다. 의미를 살리기 위함입니다.

    Args:
        json_path (str, optional): [description]. Defaults to './storehelper/metadata/template.json'.

    Returns:
        dict: [description]
    """
    return assert_json(json_path=json_path)


def get_chrome_driver(
    json_path:str='./storehelper/metadata/template.json',
    chrome_options=None,
):
    #FIXME 이거 이렇게 쓰면 진짜 나중에 단단히 꼬임.
    #crawlutil 의 common, 클래스로 상태 관리할 것.

    dic = get_json_meatadata(json_path)
    download_dir = os.path.abspath(dic['DOWNLOADING_FILE_DIR'])
    chrome_driver_path = dic['CHROME_DRIVER_PATH']
    prefs = {'download.default_directory':download_dir}
    
    if chrome_options is None:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(
        chrome_driver_path,
        chrome_options=chrome_options,
    )
    time.sleep(2)
    return driver, download_dir, chrome_options, chrome_driver_path


if __name__ == '__main__':
    assert_json()