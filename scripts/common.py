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


def get_latest_file(chrome_download_dir:str, parse_fn=None):
    """크롬 다운로드 경로로부터 최신 파일을 가져옵니다.
    Args:
        chrome_download_dir (str): 크롬의 다운로드 경로
        parse_fn (fn): 가끔 보면 진짜 얄궂은 애들이 있습니다.
            생각 없이 만든건지 csv 는 세미콜론 구분이라는 것을 알면서 
            가령 "1200" 을 "1,200" 으로 표기하여 저장하는 등 이상한 행동을... 하
            그래서 어쩔 수 없이 만들었습니다.
            파일을 선택한 뒤 해당 parser 을 통해 처리합니다.
            parse_fn 은 파일 한 줄을 하나의 원소로 담은 리스트를 입력받아 리스트를 리턴합니다.
    Returns:
        p: 파일 경로
    """
    query = os.path.join(chrome_download_dir,'*.csv') # 출력파일 이름으로 설정해주고 싶지만 한글 안먹음
    files = glob.glob(query)
    print(f'searching files...\n\t{repr(files)}')
    files.sort(key=lambda x: os.path.getmtime(x))
    p = files[-1]
    print(f'selected {p}')
    
    with open(p, mode='r') as f:
        lines = f.readlines()
    with open(p, mode='w') as f:
        f.writelines(parse_fn(lines))
    return p


def get_latest_file_as_df(chrome_download_dir:str, parse_fn=None):
    """크롬 다운로드 경로로부터 최신 파일을 가져옵니다.
    Args:
        chrome_download_dir (str): 크롬의 다운로드 경로

    Returns:
        dataframe: 데이터프레임 객체 csv
    """
    p = get_latest_file(chrome_download_dir, parse_fn=parse_fn)
    df = pd.read_csv(p)
    return df