# 내장
import pathlib
import os
import json
import glob

# 서드파티
import pandas as pd

def read_json(filename):
    """파일 이름과 동일한 파일명의 json 파일을 읽어들입니다.
    """
    path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), 
        f"{filename}.json")
    print(path)
    with open(path, 'r') as f:
        di = json.load(f)
    return di


def get_latest_file(chrome_download_dir:str):
    """크롬 다운로드 경로로부터 최신 파일을 가져옵니다.
    Args:
        chrome_download_dir (str): 크롬의 다운로드 경로

    Returns:
        p: 파일 경로
    """
    query = os.path.join(chrome_download_dir,'*.csv') # 출력파일 이름으로 설정해주고 싶지만 한글 안먹음
    files = glob.glob(query)
    print(f'searching files...\n\t{repr(files)}')
    files.sort(key=lambda x: os.path.getmtime(x))
    p = files[-1]
    print(f'selected {p}')

    return p


def get_latest_file_as_df(chrome_download_dir:str):
    """크롬 다운로드 경로로부터 최신 파일을 가져옵니다.
    Args:
        chrome_download_dir (str): 크롬의 다운로드 경로

    Returns:
        dataframe: 데이터프레임 객체 csv
    """
    p = get_latest_file(chrome_download_dir)
    df = pd.read_csv(p)
    return df