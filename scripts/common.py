import pathlib
import os
import json

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